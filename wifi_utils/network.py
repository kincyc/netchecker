# wifi_utils/network.py

import subprocess
import os
import json
import re


def get_wifi_network_name():
    try:
        result = subprocess.check_output(
            [
                os.path.expanduser(
                    "~/Applications/wifi-unredactor.app/Contents/MacOS/wifi-unredactor"
                )
            ],
            text=True,
        )
        data = json.loads(result)
        ssid = data.get("ssid")
        return ssid if ssid else "UNKNOWN"
    except subprocess.CalledProcessError as e:
        print(f"wifi-unredactor error: {e}")
        return "SSID ERROR"
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON from wifi-unredactor: {e}")
        return "JSON ERROR"
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "ERROR"


def sanitize_ssid(ssid):
    if not ssid:
        return "Unknown_Network"
    ssid = re.sub(r"[^\w\s]", "", ssid)
    ssid = ssid.replace(" ", "_")
    return ssid
