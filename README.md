# Autonomous Importing to [Flightlog.org](https://flightlog.org/) from [Volandoo](https://volandoo.com/) Tracker App

## Overview

This Python script automates the process of synchronizing and importing flight logs from **Volandoo.com** to **Flightlog.org**.

### What it does:
- Logs into **Flightlog.org** and retrieves the date of the newest uploaded flight.
- Opens **Volandoo.com** and logs in.
- Collects flights from Volandoo that are newer than the newest Flightlog entry.
- Downloads corresponding `.igc` flight track files from Volandoo.
- Switches back to **Flightlog.org** and uploads the new `.igc` files with appropriate form data.

---

## Requirements

- Python 3.8+
- [Selenium](https://selenium-python.readthedocs.io/)
- Google Chrome browser installed

---

## Installation

1. Clone or download this script.
2. Ensure Google Chrome browser is installed
3. Install required Python packages:

```bash
pip install selenium
```

## How to Run

1. Ensure [Flightlog.org](https://flightlog.org/) is fast and responsive. This website can be very slow, and in that case, the script will fail. Check again later if flightlorg.org feels slow and unresponsive, check back later before running the script.
2. Write your username and password to both [Flightlog.org](https://flightlog.org/) and [Volandoo](https://volandoo.com/) in the file **username_and_password.py** (do not remove the quotation marks).
3. Open a terminal change directory to the directory containing the script.
4. Run the script from the terminal:


- On Linux/macOS:
```bash
python3 flight_importer.py
```

- On Windows:
```bash
python flight_importer.py
```

## Operating System Notes
The script uses `os.path.expanduser("~")` to locate the user home directory, compatible with Linux, macOS, and Windows. The Downloads folder is assumed to be located at `~/Downloads` or equivalent in the user's home directory. This is where the `.igc` files should be located.

## Assumptions & Notes
- The script assumes stable page layouts and element selectors for both websites. If something fails, it might be because the websites' layouts have been changed.
- The browser window size is set to `1500x800` for UI consistency.
- The script includes basic error handling but may need adjustment for site changes or errors.
- Downloads must complete before uploading — the script uses `sleep`s which might need tuning depending on network speed.