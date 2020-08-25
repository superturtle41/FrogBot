import os

prefix = os.getenv('DISCORD_BOT_PREFIX', ';')
environment = os.getenv("ENVIRONMENT", "testing")
if environment == "testing":
    token = os.getenv("DISCORD_BOT_TOKEN_TESTING", "")
    users_file = 'users.json'
elif environment == "py_testing":
    token = os.getenv("DISCORD_BOT_TOKEN_TESTING", "")
    users_file = 'testing_users.json'
elif environment == "production":
    token = os.getenv("DISCORD_BOT_TOKEN", "")
    users_file = 'user.json'
else:
    token = 'ERROR'
testing = environment == "testing"

mongo_host = os.getenv('MONGO_HOST', 'mongodb:27017')
mongo_db = os.getenv('MONGO_DATABASE')
mongo_user = os.getenv('MONGO_USERNAME')
mongo_pass = os.getenv('MONGO_PASSWORD')

version = os.getenv('VERSION', '0.4 Beta')
