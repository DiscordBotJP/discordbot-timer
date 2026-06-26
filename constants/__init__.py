from dotenv import load_dotenv
from os import getenv

load_dotenv()

TOKEN = getenv('DISCORD_BOT_TOKEN')
OPS_LOG_HUB_URL = getenv('OPS_LOG_HUB_URL')
OPS_LOG_HUB_KEY = getenv('OPS_LOG_HUB_KEY')
OPS_LOG_PROJECT = getenv('OPS_LOG_PROJECT', 'discordbot-timer')
OPS_LOG_ENVIRONMENT = getenv('OPS_LOG_ENVIRONMENT', 'development')
DASHBOARD_CONFIG_URL = getenv(
    'DASHBOARD_CONFIG_URL',
    'https://dashboard.discordbot.jp/api/bot-runtime/settings',
)
DASHBOARD_CONFIG_SECRET = getenv('DASHBOARD_BOT_CONFIG_SECRET') or getenv(
    'DASHBOARD_INGEST_SECRET',
)
