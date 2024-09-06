import subprocess
import re
from datetime import datetime
import argparse
import time

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

# Function to ping a given address and print the result with timestamp and SSID
def ping_address(address):
    try:
        # Ping the given address with a single request (-c 1 for one ping)
        result = subprocess.run(['ping', '-c', '1', address], stdout=subprocess.PIPE, text=True)
        output = result.stdout

        # Extract relevant ping info using regex
        match = re.search(r'(\d+) bytes from [^\s]+: icmp_seq=(\d+) ttl=(\d+) time=([\d.]+) ms', output)
        if match:
            bytes_received = match.group(1)
            icmp_seq = match.group(2)
            ttl = match.group(3)
            time_ms = match.group(4)

            # Get the current timestamp and network name (SSID)
            timestamp = datetime.now().strftime('%Y-%m-%d  %H:%M:%S')
            ssid = sanitize_ssid(get_wifi_network_name())

            # Print the ping result with the required format
            print(f"{timestamp}\t{ssid}\t{bytes_received} bytes from {address}\ticmp_seq={icmp_seq}\tttl={ttl}\ttime={time_ms} ms")
        else:
            print(f"Ping to {address} failed or no match found in output.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Main function to parse command-line arguments and call the ping function
if __name__ == "__main__":
    # Set up argparse to handle command-line input
    parser = argparse.ArgumentParser(description="Ping a given address and display results with a timestamp and network information.")
    parser.add_argument('--address', "-a", type=str, help="The address to ping (e.g., 8.8.8.8)")
    parser.add_argument('--interval', "-i", type=int, default=1, help="Interval between pings in seconds (default is 1 second)")

    # Parse the arguments
    args = parser.parse_args()

    # Continuously ping the provided address with the specified interval
    while True:
        ping_address(args.address)
        time.sleep(args.interval)  # Use the interval provided by the user (default 1 second)