import os


class Config:
    # Security key for sessions - keep this secret
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'pulseiq-super-secret-key-2025'

    # SQLite database - stored locally in instance/pulseiq.db
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL') or 'sqlite:///pulseiq.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Apify token - you will add yours here later
    APIFY_TOKEN = os.environ.get('APIFY_TOKEN', '')

    # Max posts to collect per case
    MAX_POSTS_PER_CASE = 100

    # Run in debug mode (shows errors clearly)
    DEBUG = True
