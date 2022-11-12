# OSU Floodgate (BETA) Discord Bot
This is a modularily written discord bot for student organizations at Oregon State University to verify that all of their members are assosiated with the university. 
Copy config.sample.py to config.py and update the values to be accurate to your respective server. It uses a sqlite3 database to track user status.

It can also restart and upgrade on the fly with just a command. `!upgrade` pulls the latest code from Git and restarts.

This bot was forked from the [Oregon State University Security Club Discord Bot](https://gitlab.com/osusec/discord-bot).

# Requirements
* Python 3
* pip modules
  * discord.py
  * pyutil
  * sqlite (usually preinstalled)

# Install
1. Clone repo
2. `pip install -r requirements.txt`
3. Duplicate `config.sample.py` to `config.py` and fill in the fields
4. `python3 bot.py`

Log is written to `discord.log`, database is at `bot.db`
