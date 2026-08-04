import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]

WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST", "")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "change-me")

PORT = int(os.environ.get("PORT", 8080))

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./local.db")

JAMENDO_CLIENT_ID = os.environ.get("JAMENDO_CLIENT_ID", "")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")
