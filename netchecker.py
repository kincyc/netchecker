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

def setup_logging(silent_mode):
	logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
	if silent_mode:
		logging.getLogger().setLevel(logging.WARNING)

def sanitize_ssid(ssid):
	ssid = re.sub(r'[^\w\s]', '', ssid)	 # Remove punctuation
	ssid = ssid.replace(' ', '_')		# Replace spaces with underscores
	return ssid

def get_wifi_network_name():
	try:
		result = subprocess.check_output("/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I", shell=True).decode('utf-8')
		for line in result.split('\n'):
			if ' SSID:' in line:
				return line.split(': ')[1]
		return "Not_Connected_or_Unknown"
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

def test_speed(ssid):
	global last_test_time
	try:
		st = speedtest.Speedtest()
		st.download()
		st.upload()
		st.get_servers([])
		st.get_best_server()
		results_dict = st.results.dict()

		utc_timestamp = datetime.strptime(results_dict["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ")
		local_timestamp = utc_timestamp - timedelta(hours=8)
		delay = calculate_delay(local_timestamp)
		date = local_timestamp.strftime("%Y-%m-%d")
		time_str = local_timestamp.strftime("%H:%M:%S")

		return {
			"date": date,
			"time": time_str,
			"network": ssid[:16].ljust(16),
			"delay": "{:6.2f}".format(delay),
			"download_speed": "{:6.2f}".format(results_dict["download"] / 1024 / 1024),
			"upload_speed": "{:6.2f}".format(results_dict["upload"] / 1024 / 1024),
			"ping": "{:6.2f}".format(results_dict["ping"]),
			"isp": results_dict["client"]["isp"][:16].ljust(16),
			"server": results_dict["server"]["name"]
		}
	except Exception as e:
		logging.error(f"Error occurred: {e}")
		now = datetime.now()
		delay = calculate_delay(now)
		error_message = str(e)[:16].ljust(16)  # Truncate and pad the error message
		return {
			"date": now.strftime("%Y-%m-%d"),
			"time": now.strftime("%H:%M:%S"),
			"network": ssid[:16].ljust(16),
			"delay": "{:6.2f}".format(delay),
			"download_speed": "{:6.2f}".format(0),
			"upload_speed": "{:6.2f}".format(0),
			"ping": "{:6.2f}".format(0),
			"isp": error_message,
			"server": ""
		}

def init_log_file(ssid):
	file_name = f"{ssid}.log"
	if not os.path.exists(file_name):
		logging.warning(f"creating : {file_name}")
		with open(file_name, 'w') as file:
			file.write("Date		Time	  Network			delay	D/L		U/L		Ping	ISP				  Test Server\n")			 

	return file_name																						

def get_log_file():
	global last_ssid
	ssid = get_wifi_network_name()
	ssid = sanitize_ssid(ssid)
	if ssid != last_ssid:
		last_ssid = ssid
		return init_log_file(ssid)
	else:
		return f"{ssid}.log"

def write_results_to_file(results):
	file_name = get_log_file()
	with open(file_name, 'a') as file:
		file.write(f"{results['date']}	{results['time']}  {results['network']}	 {results['delay']}	 {results['download_speed']}  {results['upload_speed']}	 {results['ping']}	{results['isp']}  {results['server']}\n")

def main(interval_minutes, silent_mode):
	setup_logging(silent_mode)
	while True:
		ssid = get_wifi_network_name()
		ssid = sanitize_ssid(ssid)
		results = test_speed(ssid)
		logging.info(f"Speed Test Results: {results}")
		write_results_to_file(results)
		time.sleep(interval_minutes * 60)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Run speed tests at regular intervals.")
	parser.add_argument("--interval", "-i", type=int, default=5, help="Interval in minutes between each test (default is 5 minutes).")
	parser.add_argument("--silent", "-s", action="store_true", help="Run in silent mode without printing results to the screen.")
	args = parser.parse_args()

	main(args.interval, args.silent)
