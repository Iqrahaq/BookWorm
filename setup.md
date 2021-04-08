## Introduction
Currently you must self-host the bot. No docker image has been created yet, so the setup process is a bit more manual. These instructions might not be 100% perfect for your setup but it should give some rough guidance on getting started.
**Disclaimer** - Follow this guide at your own risk! These instructions are to help with quickstarting, but are not production environment ready.

## Prerequisites
- Something to host on - this could be anything from a VPS to a Raspberry Pi at home.
- Linux OS - This guide has been tested for Ubuntu Server 18.04. Docker/WSL/Windows/XYZ Distro might work fine, but it might not.
- Python 3, Python3 Venv & Pip3 - `sudo apt install python3-pip python3-venv screen`
- A MySQL server with a database & user for BookWorm:
```bash
sudo apt install mysql-server && sudo mysql_secure_installation
sudo mysql -u root
CREATE USER 'bookworm'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON *.* TO 'bookworm'@'localhost';
exit;
mysql -u bookworm -p
CREATE DATABASE bookworm;
exit;
```
- Discord application/bot token & joined to server via OAuth with permissions  - [Discord Dev Portal](https://discord.com/developers/applications)

## Setup
Run through these commands to download and install BookWorm/Dependencies.
```bash
cd ~
mkdir bookworm && cd bookworm
git clone https://github.com/Iqrahaq/BookWorm
python3 -m venv bwenv && source bw/bin/activate
cd BookWorm
pip3 install -r requirements.txt
pip3 install "python-dotenv[cli]"
```
Next, create a file called .env in the code directory with `nano code/.env`, and add the below contents to the file, replacing the values with your info.
```
DISCORD_TOKEN=ABCDEFGHIJKLMNOPQRSTUVWXYZ
HOST=localhost
USER=bookworm
PASSWORD=ThePassYouSetEarlier
DATABASE=bookworm
```
Save with CTRL+X then Y, enter.

## Run the bot
Time to test the setup, and once satisfied we can run it in screen so we can close the SSH session and keep the bot running. Having it run as its own user is advisable in production but this is just a quick guide.

Run `cd code && dotenv run -- python main.py` and if all is good and there are no errors, the application/bot which you joined to your server earlier via OAuth will be showing as online. Give the command **bw!botsetup** and then ensure the role is applied to users so that they can engage with the Book Club commands etc.

If you're satisfied that the bot is working, set up [screen](https://linux.die.net/man/1/screen) so that you can disconnect and keep the bot running. 
