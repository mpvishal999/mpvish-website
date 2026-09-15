"""Configuration for MPVISH."""
import os
from dotenv import load_dotenv

load_dotenv()

def _bool(val, default=False):
    if val is None:
        return default
    return val.strip().lower() in ('1', 'true', 'yes', 'on')


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

    # Database — BOTH apps use the SAME DATABASE_URL to share data
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///mpvish.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

    SITE_NAME = os.environ.get('SITE_NAME', 'MPVISH')
    SITE_TAGLINE = os.environ.get('SITE_TAGLINE', 'MP Ki Padhai, Ek Jagah')
    SITE_URL = os.environ.get('SITE_URL', 'http://127.0.0.1:5000')

    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads'))
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

    REMEMBER_COOKIE_DURATION = 30 * 24 * 3600

    # SMTP (optional)
    SMTP_HOST = os.environ.get('SMTP_HOST', '')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', '')

    # Ads
    ADSTERRA_CODE = os.environ.get('ADSTERRA_CODE', '')
    ADSENSE_CODE = os.environ.get('ADSENSE_CODE', '')
    ADSENSE_PUBLISHER_ID = os.environ.get('ADSENSE_PUBLISHER_ID', '')

    # SEO / Analytics
    GOOGLE_SEARCH_CONSOLE_CODE = os.environ.get('GOOGLE_SEARCH_CONSOLE_CODE', '')
    GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', '')

    # Payments
    UPI_ID = os.environ.get('UPI_ID', '')
    PAYMENT_INSTRUCTIONS = os.environ.get('PAYMENT_INSTRUCTIONS', '')
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

    # Social
    CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL', '')
    TELEGRAM_URL = os.environ.get('TELEGRAM_URL', '')
    TELEGRAM_CHANNEL_URL = os.environ.get('TELEGRAM_CHANNEL_URL', '')
    YOUTUBE_URL = os.environ.get('YOUTUBE_URL', '')
    INSTAGRAM_URL = os.environ.get('INSTAGRAM_URL', '')
    WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '')

    # Google OAuth (optional)
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

    # Admin bootstrap
    ADMIN_NAME = os.environ.get('ADMIN_NAME', 'Admin')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', '')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')

    STORAGE_BACKEND = 'local'

    @staticmethod
    def init_app(app):
        pass
