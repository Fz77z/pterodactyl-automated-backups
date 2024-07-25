![image](https://github.com/Fz77z/pterodactyl-automated-backups/assets/90436534/24af539c-eee8-49de-a598-3d3ea1f1f11f)

# Pterodactyl Automated Backups 


## Overview

Pterodactyl Automated Backups is a Python script that automates the process of creating backups for all servers connected to your panel. It utilizes the Pterodactyl API to initiate backups for multiple servers consecutively. In case of backup failures, it provides a retry mechanism and sends email alerts to notify the administrator.

## Features

- **Fully-automated-backups:** Supports automated backups for all servers connected to your pterodactyl panel.
- **Reliable:** Handles backup failures and retries the process for failed servers.
- **User-friendly:** Easy to set up and use, minimal technical expertise required.
- **Email-support:** Sends optional email alerts to notify the administrator about backup failures.
- **Detailed-logging:** Logs backup events and errors to a file for easy troubleshooting.
- **Any-type:** Supports both s3 and filesystem backups.
- **Backup-rotation** Removes older backups when backup limit is reached (filesystem backups only).
- **Post-backup-script** Can run a custom shell script after each successful backup.

## Prerequisites

Before using this script, ensure that the following dependencies are installed:

# Python3
Python 3.x: This script requires Python 3.x. You can check your Python version by running python3 --version in your terminal. If Python 3.x is not installed, you can install it via:

`sudo apt update && sudo apt install python3`


# Installing Modules

If pip is not installed, you can install it via: `sudo apt install python3-pip`

1. `requests`: A Python module used for making HTTP requests.
2. `python-dotenv`: A Python module used for handling .env files.
you can install them using pip via :<br> `pip install requests && pip install python-dotenv`

Note: The `os`, `time`, `json`, `logging`, and `http` modules are part of the Python 3 Standard Library and are included with Python by default.


## Installation

To install Automated Backups, follow these steps:

1. Clone the repository: `git clone <repo_url>`
2. Navigate to the project directory: `cd automated-backups`
3. Setup your Python environment and install dependencies (Assuming Python and pip are installed)
4. rename the example env file: `mv .env.example .env`
5. Generate a client API key on your pterodactyl panel: `Account Settings > API Credentials > Create`
6. Replace the .env placeholder values with your own configuration.
7. Test the script using following command: `python3 backup.py`

`*** Please note: Ensure the account you used to generate the panel api key does not own any of the servers you wish to be backed up. ***`

## Setting Up a Cron Job

To ensure that the script runs automatically at regular intervals, you can set up a cron job. Here's a basic example that would run the backup every day at 4am:

1. Open your crontab file: crontab -e
2. Add the following line: 0 4 * * * /path/to/env/bin/python3 /path/to/your/script/backup.py

## Logging

The script logs backup events and errors to a file named backup.log. You can find this file in the same directory where the script is located. The log format includes the log level and message.

## Disclaimer

This script is provided as-is without any warranty. Use it at your own risk. The author is not responsible for any damages or losses caused by using this script.

## Support

If you encounter any issues or have questions about the application, please visit my [discord](https://discord.gg/ngnKtNdv)



