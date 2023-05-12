# Pterodactyl Automated Backups ![image](https://github.com/Fz77z/pterodactyl-automated-backups/assets/90436534/7b33995b-2241-4725-aa39-b057f13cd3ab)


## Overview

Pterodactyl Automatic Backups is a Python script that automates the process of creating backups for all servers connected to your panel. It utilizes the Pterodactyl API to initiate backups for multiple servers consecutively. In case of backup failures, it provides a retry mechanism and sends email alerts to notify the administrator.

## Features

- **Automated backups:** Supports automatic backups for Pterodactyl servers.
- **Reliable:** Handles backup failures and retries the process for failed servers.
- **User-friendly:** Easy to set up and use, minimal technical expertise required.
- **email-support:** Sends email alerts to notify the administrator about backup failures.
- **logging:** Logs backup events and errors to a file for easy troubleshooting.
- **any type:** Supports both s3 and filesystem backups.


## Prerequisites

Before using this script, ensure that the following dependencies are installed:

1. Python 3.x
2. requests module
3. dotenv module
4. logging module


## Installation

To install Automated Backups, follow these steps:

1. Clone the repository: `git clone <repo_url>`
2. Navigate to the project directory: `cd automated-backups`
3. Setup your Python environment and install dependencies (Assuming Python and pip are installed)
4. rename the example env file: `mv .env.example .env`
5. Generate a client API key on your pterodactyl panel: `Account Settings > API Credentials > Create`
6. Replace the .env placeholder values with your own configuration.
7. Test the script using following command: `python backup.py`

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



