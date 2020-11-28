FrogBot
=======

> Discord bot meant for smaller D&D servers and for my personal use. 

FrogBot is written in [discord.py](https://github.com/Rapptz/discord.py) and uses MongoDB for its database

Requirements
------------
* Python 3.8.x
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
    * Required - 
      1. `DISCORD_MONGO_URL` - URL to Mongo DB with auth
      2. `DISCORD_BOT_TOKEN` - Token of the bot from discord developer page.
      4. `MONGO_DB` - Sets which database to use on the Mongo Server.
    * Optional -
      1. `SENTRY_URL` - URL For Sentry Error Reporting
      2. `API_URL` - URL for API (Used for online uptime reporting.)
      3. `API_KEY` - Key for above API
      4. `DBL_API_KEY` - API key for discord bot list
      5. `DAGPI_API_KEY` - API key used for Dagpi.xyz API
      6. `DEV_ID` - Your discord ID, used in bot owner checks. (default my id)
      7. `DISCORD_STATUS` - What status to use by default. (default `'with the api'`)
      8. `MONGO_DB` - Which database to use on the mongo server (default `frogbotdb`)
      9. `VERSION` - Current Bot Version (unused currently)
      10. `ENVIRONMENT` - Bot Environment (`development` or `production`)
      11. `DISCORD_BOT_PREFIX` - Sets the prefix of the bot for commands (default `;`)
4. Install Dependencies
    1. `pip install -r requirements.txt`
5. Run Bot (Make sure your environment variables are set)
    1. `py dbot.py`
    
Contributing
------------
If you spot a bug, please open an issue!
If you would like to contribute to the project, open a PR!