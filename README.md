FrogBot
=======

> Discord bot meant for smaller D&D servers and for my personal use. 

FrogBot is written in [discord.py](https://github.com/Rapptz/discord.py) and uses MongoDB for its database

Requirements
------------
* Python 3.x.x
* Pip
* MongoDB Server


Setup
-----
1. Clone the github repository 
    1. `git clone https://github.com/1drturtle/FrogBot.git`
2. Create a virtual environment and activate it
    1. `virtualenv venv`
    2. `source venv/scripts/activate` on linux, `"venv/scripts/activate.bat"` on Windows
3. Populate environment variables. I'm not going to describe how to do this, but here are the environment variables you need:
    1. `DISCORD_MONGO_URL` - URL to Mongo DB with auth
    2. `DISCORD_BOT_TOKEN` - Token of the bot.
    3. `DISCORD_BOT_PREFIX` - Sets the prefix of the bot for commands
    4. `MONGO_DB` - Sets which database to use on the Mongo Server.
    5. `SENTRY_URL` (Optional) - URL For Sentry Error Reporting
    6. `API_URL` (Optional) - URL for API (Used for online checks.)
    7. `API_KEY` (Optional) - Key for above API
4. Install Dependencies
    1. `pip install -r requirements.txt`
5. Run Bot (Make sure your environment variables are set)
    1. `py dbot.py`
    
Contributing
------------
If you spot a bug, please open an issue!
If you would like to contribute to the project, open a PR!