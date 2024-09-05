#!/opt/homebrew/bin/python3

import speedtest
import time
import os
import subprocess
import argparse
import logging
import re
from datetime import datetime, timedelta

# Global variable to store the time of the last test and last SSID
last_test_time = None
last_ssid = None


def init_log_file(ssid):
	file_name = f"{ssid}.log"
	if not os.path.exists(file_name):
		with open(file_name, 'w') as file:
			header = "Date        Time      Network            Delay     D/L     U/L    Ping  ISP               Test Server\n"
			file.write(header)
	return file_name

def setup_logging(silent_mode, ssid):
	file_name = init_log_file(ssid)	 # Ensure the log file exists and has a header
	# removing the logging timestamp
	# log_format = "%(asctime)-20s %(message)s"
	log_format = "%(message)s"
	logging.basicConfig(level=logging.INFO if not silent_mode else logging.WARNING,
						format=log_format,
						handlers=[
							logging.FileHandler(file_name, mode='a'),  # Append mode
							logging.StreamHandler()
						])

def sanitize_ssid(ssid):
	ssid = re.sub(r'[^\w\s]', '', ssid)	 # Remove punctuation
	ssid = ssid.replace(' ', '_')		# Replace spaces with underscores
	return ssid

def get_wifi_network_name():
	try:
		# Get the Wi-Fi device (usually 'Wi-Fi' or 'en0' on Macs)
		result = subprocess.check_output(["networksetup", "-getairportnetwork", "en0"]).decode('utf-8')
		# Parse the result for the SSID
		if "You are not associated with an AirPort network" in result:
			return "Not_Connected_or_Unknown"
		else:
			return result.split(": ")[1].strip()
	except subprocess.CalledProcessError:
		return "Error_Retrieving_SSID"

def calculate_delay(current_time):
	global last_test_time
	if last_test_time is None:
		delay = 0
	else:
		delay = (current_time - last_test_time).total_seconds() / 60  # Delay in minutes
	last_test_time = current_time
	return delay

def update_delay():
	global last_test_time
	now = datetime.now()
	delay = calculate_delay(now)
	return [now, delay]

def test_speed(ssid):
	now, delay = update_delay()
	try:
		st = speedtest.Speedtest()
		st.download()
		st.upload()
		st.get_servers([])
		st.get_best_server()
		results_dict = st.results.dict()

		# we used to get the time from the speedtest object but then we had to switch to system time
		# if speedtest was down. This is no longer necessary.
		# utc_timestamp = datetime.strptime(results_dict["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ")
		# local_timestamp = utc_timestamp - timedelta(hours=8)
		# delay = calculate_delay(local_timestamp)
		return {
			"date": now.strftime("%Y-%m-%d"),
			"time": now.strftime("%H:%M:%S"),
			"network": ssid[:16].ljust(16),
			"delay": delay,
			"download_speed": results_dict["download"] / 1024 / 1024,
			"upload_speed": results_dict["upload"] / 1024 / 1024,
			"ping": results_dict["ping"],
			"isp": results_dict["client"]["isp"][:16].ljust(16),
			"server": results_dict["server"]["name"]
		}
	except Exception as e:

		# Directly incorporate the error message into the ISP column
		error_message = "Error: " + str(e).split(":")[-1]  # Simplify the error message if needed
		return {
			"date": now.strftime("%Y-%m-%d"),
			"time": now.strftime("%H:%M:%S"),
			"network": ssid[:16].ljust(16),
			"delay": delay,
			"download_speed": 0,
			"upload_speed": 0,
			"ping": 0,
			"isp": error_message[:16].ljust(16),  # Ensure the error fits into the ISP column
			"server": ""
		}

def format_results(results):
	formatted_result = f"{results['date']:10}  {results['time']:8}  {results['network']}  " \
					   f"{results['delay']:6.2f}  {results['download_speed']:6.2f}  " \
					   f"{results['upload_speed']:6.2f}  {results['ping']:6.2f}  " \
					   f"{results['isp']}  {results['server']}"
	return formatted_result

def start_message(now, ssid):
	# this message is printed at script start to indicate a restart of the monitor
	formatted_result = f"{now.strftime('%Y-%m-%d')}  {now.strftime('%H:%M:%S')}  {ssid}          RESTART"
	return formatted_result

def main(interval_minutes, silent_mode):
	ssid = get_wifi_network_name()
	ssid = sanitize_ssid(ssid)
	setup_logging(silent_mode, ssid)
	logging.info(start_message(datetime.now(), ssid))
	while True:
		results = test_speed(ssid)
		formatted_results = format_results(results)
		logging.info(formatted_results)
		time.sleep(interval_minutes * 60)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Run speed tests at regular intervals.")
	parser.add_argument("--interval", "-i", type=int, default=5, help="Interval in minutes between each test (default is 5 minutes).")
	parser.add_argument("--silent", "-s", action="store_true", help="Run in silent mode without printing results to the screen.")
	args = parser.parse_args()
	print(f"Interval: {args.interval}\tSilent Mode: {args.silent}")
	main(args.interval, args.silent)
