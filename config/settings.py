import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))

# Claude API
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# PayPal
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")

# Business Settings
LEADS_UPDATE_INTERVAL = int(os.getenv("LEADS_UPDATE_INTERVAL", "3600"))
MAX_CONCURRENT_AGENTS = int(os.getenv("MAX_CONCURRENT_AGENTS", "5"))
PRICE_PER_MONTH = 50000  # UZS (примерно $5)
COMMISSION_PERCENT = 0.20  # 20% от генерированных продаж

# Email
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Business Information
BUSINESS_NAME = "AI Sales Bot Tashkent"
BUSINESS_DESCRIPTION = "Автоматизируйте генерацию лидов с помощью AI"
