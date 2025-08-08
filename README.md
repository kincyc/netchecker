this uses the Ookla speedtest-cli library and runs a download, upload and latency test on a user-defined frequency.

this script can output to screen (--silent false)

it will create log files for each SSID that is connects to.

For example, if your computer is connected to the TEST1 Wifi network, it will create a TEST1.log file.

If for some reason, you switch networks, e.g. NEWNETWORK, it will create a new logfile called NEWNETWORK.log and write to that.

It will handle a network change during operation.
if there are error states, those will be logged as well, in the ISP column
the log files are space delimited so they "work" with MacOS console
you can adjust the frequency, the script will default to every 5 minutes

_Column meanings_

- Date date of test from Ookla server OR localtime if there is an error
- Time time of ""
- Network name of SSID
- Delay delta in second between current test and previous. if restarting or changing networks, will be 0
- D/L download speed as reported by Ookla
- U/L upload speed as reported by Ookla
- Ping latency as reported by Ookla
- ISP name of ISP as reported by Ookla
- Test Server name/location of Ookla test server

# IMPORTANT

because of security settings in MacOS with regards to location services, you'll need to install the following:

git https://github.com/noperator/wifi-unredactor.git
git --help
git clone https://github.com/noperator/wifi-unredactor.git
cd wifi-unredactor
ls -lsa
more README.md
./build-and-install.sh
~/Applications/wifi-unredactor.app/Contents/MacOS/wifi-unredactor
