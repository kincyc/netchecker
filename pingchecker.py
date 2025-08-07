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
    ssid = re.sub(r"[^\w\s]", "", ssid)  # Remove punctuation
    ssid = ssid.replace(" ", "_")  # Replace spaces with underscores
    return ssid


# Function to get the current Wi-Fi network name (SSID)
def get_wifi_network_name():
    try:
        # Get the Wi-Fi device (usually 'Wi-Fi' or 'en0' on Macs)
        result = subprocess.check_output(
            ["ipconfig", "getsummary", "en0"],
            text=True,  # Ensures the output is returned as a string
        )
        # Use awk to parse the SSID from the result
        ssid = subprocess.check_output(
            ["awk", "-F", " SSID : ", "/ SSID : / {print $2}"], input=result, text=True
        ).strip()
        return ssid if ssid else "Not_Connected_or_Unknown"
    except subprocess.CalledProcessError:
        return "Error_Retrieving_SSID"


# Function to initialize the log file
def init_log_file(ssid):
    file_name = f"{ssid}-ping.log"
    header = "Network\tDate\t    Time\tDelta\t\tPing Result"
    if not os.path.exists(file_name):
        with open(file_name, "w") as file:
            file.write(f"{header}\n")
    print(header)
    return file_name


# Function to set up logging
def setup_logging(ssid, silent_mode=False):
    file_name = init_log_file(ssid)
    log_format = "%(message)s"  # Log format without timestamps
    logging.basicConfig(
        level=logging.INFO if not silent_mode else logging.WARNING,
        format=log_format,
        handlers=[
            logging.FileHandler(file_name, mode="a"),  # Append to the log file
            logging.StreamHandler(),  # Optionally print to console
        ],
    )


# Function to get the boot mode (Safe Mode or Normal)
def get_boot_mode():
    try:
        result = subprocess.check_output(
            ["system_profiler", "SPSoftwareDataType"], text=True
        )
        # Extract the "Boot Mode" from the result
        match = re.search(r"Boot Mode: (\w+)", result)
        if match:
            return match.group(1)  # Return the boot mode (Safe or Normal)
        else:
            return "Unknown"
    except subprocess.CalledProcessError:
        return "Error_Retrieving_Boot_Mode"


def ping_address(address, threshold, interval, last_ping_time):
    try:
        # Ping the given address with a single request (-c 1 for one ping)
        result = subprocess.run(
            ["ping", "-c", "1", "-t", "1", address],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        output = result.stdout
        error = result.stderr

        # Get the current timestamp and network name (SSID)
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d  %H:%M:%S")
        ssid = sanitize_ssid(get_wifi_network_name())

        # Check for error in the ping response
        if error:
            message = f"{ssid}\t{timestamp}\tPing to {address} failed: {error.strip()}"
            logging.error(message)
        else:
            # Extract relevant ping info using regex
            match = re.search(
                r"(\d+) bytes from [^\s]+: icmp_seq=(\d+) ttl=(\d+) time=([\d.]+) ms",
                output,
            )
            if match:
                ttl = match.group(3)
                time_ms = float(match.group(4))

                # Prepare the restart message with ttl
                if last_ping_time is None:
                    message = (
                        f"{ssid}\t{timestamp}\tRESTART\t\tttl={ttl}\ttime={time_ms} ms"
                    )
                    logging.info(message)
                else:
                    # Prepare the ping message for subsequent pings
                    time_delta = (now - last_ping_time).total_seconds()
                    time_delta_str = f"{time_delta:.2f} sec"
                    message = f"{ssid}\t{timestamp}\t{time_delta_str}\tttl={ttl}\ttime={time_ms} ms"

                    # Check if the ping time exceeds the threshold
                    if time_ms > threshold or time_delta > (2 * interval):
                        logging.info(colored(message, "red"))
                    else:
                        logging.info(message)
            else:
                logging.error(f"{timestamp}\t{ssid}\tPing failed or no match found.")

        return now  # Update the last ping time
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return last_ping_time


# Main function
if __name__ == "__main__":
    # Set up argparse to handle command-line input
    parser = argparse.ArgumentParser(
        description="Ping a given address and display results with a timestamp and network information."
    )
    parser.add_argument(
        "--address", "-a", type=str, help="The address to ping (e.g., 8.8.8.8)"
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=1,
        help="Interval between pings in seconds",
    )
    parser.add_argument(
        "--threshold", "-t", type=float, default=100.0, help="Threshold in milliseconds"
    )
    parser.add_argument(
        "--silent",
        "-s",
        action="store_true",
        help="Run in silent mode (log to file only)",
    )

    # Get the boot mode (Safe or Normal)
    boot_mode = get_boot_mode()
    print(f"\nBoot Mode: {boot_mode.upper()}\n")

    # Parse the arguments
    args = parser.parse_args()

    # Get the sanitized SSID for logging
    ssid = sanitize_ssid(get_wifi_network_name())

    # Set up logging
    setup_logging(ssid, args.silent)

    # Initialize the last ping time
    last_ping_time = None

    # Continuously ping the provided address
    while True:
        last_ping_time = ping_address(
            args.address, args.threshold, args.interval, last_ping_time
        )
        time.sleep(args.interval)
