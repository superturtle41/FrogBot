import os

PREFIX = os.environ.get('DISCORD_BOT_PREFIX', ';')
DEV_ID = 175386962364989440
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
MONGO_URL = os.environ.get('DISCORD_MONGO_URL')
MONGO_DB = os.environ.get('MONGO_DB', 'frogbotdb')
DEFAULT_STATUS = os.environ.get('DISCORD_STATUS', f'API')
MY_SERVER = os.environ.get('MY_SERVER')
