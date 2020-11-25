import os

PREFIX = os.environ.get('DISCORD_BOT_PREFIX', ';')
DEV_ID = 175386962364989440
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
MONGO_URL = os.environ.get('DISCORD_MONGO_URL')
MONGO_DB = os.environ.get('MONGO_DB', 'frogbotdb')
DEFAULT_STATUS = os.environ.get('DISCORD_STATUS', f'with the API')

# API
API_URL = os.getenv('BOT_API_URL', None)
API_KEY = os.getenv('BOT_API_KEY', None)
DBL_API_KEY = os.getenv('BOT_DBL_API_KEY', None)
DAGPI_API_KEY = os.getenv('BOT_DAGPI_API_KEY', None)

# Version
VERSION = os.environ.get('VERSION', 'testing')

# Error Reporting
SENTRY_URL = os.getenv('SENTRY_URL', None)
ENVIRONMENT = os.getenv('ENV', 'development')
