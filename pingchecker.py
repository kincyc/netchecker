import subprocess
import re
from datetime import datetime
import argparse
import time
import logging
import os
from termcolor import colored  # For colored output

# Function to sanitize the SSID name
def sanitize_ssid(ssid):
    ssid = re.sub(r'[^\w\s]', '', ssid)  # Remove punctuation
    ssid = ssid.replace(' ', '_')        # Replace spaces with underscores
    return ssid

# Function to get the current Wi-Fi network name (SSID)
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

# Function to initialize the log file
def init_log_file(ssid):
    file_name = f"{ssid}-ping.log"
    if not os.path.exists(file_name):
        with open(file_name, 'w') as file:
            header = "Date        Time      Network            Ping Result\n"
            file.write(header)
    return file_name

# Function to set up logging
def setup_logging(ssid, silent_mode=False):
    file_name = init_log_file(ssid)
    log_format = "%(message)s"  # Log format without timestamps (timestamps are included in the message)
    logging.basicConfig(level=logging.INFO if not silent_mode else logging.WARNING,
                        format=log_format,
                        handlers=[
                            logging.FileHandler(file_name, mode='a'),  # Append to the log file
                            logging.StreamHandler()                    # Optionally print to console
                        ])

# Function to log a start or restart message
def start_message(now, ssid):
    # This message is printed/logged at the script start to indicate a restart of the monitor
    formatted_result = f"{now.strftime('%Y-%m-%d')}  {now.strftime('%H:%M:%S')}  {ssid}          RESTART"
    return formatted_result

# Function to ping a given address and log the result
def ping_address(address, threshold):
    try:
        # Ping the given address with a single request (-c 1 for one ping)
        result = subprocess.run(['ping', '-c', '1', address], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout
        error = result.stderr

        # Get the current timestamp and network name (SSID)
        timestamp = datetime.now().strftime('%Y-%m-%d  %H:%M:%S')
        ssid = sanitize_ssid(get_wifi_network_name())

        # Check for error in the ping response
        if error:
            # If there is an error (e.g., no route to host), log the error message with timestamp
            message = f"{timestamp}\t{ssid}\tPing to {address} failed: {error.strip()}"
            logging.error(message)
        else:
            # Extract relevant ping info using regex for a successful ping
            match = re.search(r'(\d+) bytes from [^\s]+: icmp_seq=(\d+) ttl=(\d+) time=([\d.]+) ms', output)
            if match:
                bytes_received = match.group(1)
                icmp_seq = match.group(2)
                ttl = match.group(3)
                time_ms = float(match.group(4))  # Convert time to float for comparison

                # Prepare the ping message
                message = f"{timestamp}\t{ssid}\t{bytes_received} bytes from {address}\ticmp_seq={icmp_seq}\tttl={ttl}\ttime={time_ms} ms"

                # Check if the ping time exceeds the threshold
                if time_ms > threshold:
                    # Log in red if the time exceeds the threshold (in console)
                    logging.info(colored(message, 'red'))
                else:
                    # Log normally if the time is within the threshold
                    logging.info(message)
            else:
                logging.error(f"{timestamp}\t{ssid}\tPing to {address} failed or no match found in output.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

# Main function to parse command-line arguments and call the ping function
if __name__ == "__main__":
    # Set up argparse to handle command-line input
    parser = argparse.ArgumentParser(description="Ping a given address and display results with a timestamp and network information.")
    parser.add_argument('--address', "-a", type=str, help="The address to ping (e.g., 8.8.8.8)")
    parser.add_argument('--interval', "-i", type=int, default=1, help="Interval between pings in seconds (default is 1 second)")
    parser.add_argument('--threshold', '-t', type=float, default=100.0, help="Time threshold in milliseconds to trigger red warning (default is 100 ms)")
    parser.add_argument('--silent', '-s', action='store_true', help="Run in silent mode (log to file only, no console output)")

    # Parse the arguments
    args = parser.parse_args()

    # Get the sanitized SSID for logging
    ssid = sanitize_ssid(get_wifi_network_name())

    # Set up logging
    setup_logging(ssid, args.silent)

    # Log the start message
    logging.info(start_message(datetime.now(), ssid))

    # Continuously ping the provided address with the specified interval and threshold
    while True:
        ping_address(args.address, args.threshold)
        time.sleep(args.interval)  # Use the interval provided by the user (default 1 second)