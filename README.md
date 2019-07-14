# OSU Security Club Discord Bot
This Discord bot verifies email address for your organization in order to federate access to sensitive channels. You can configure multiple valid domains, and what roles require being verified to join. It uses a sqlite3 database to track user status

It can also restart and upgrade on the fly with just a command. `!upgrade` pulls the latest code from Git and restarts.

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
