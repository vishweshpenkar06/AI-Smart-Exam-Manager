"""
AI Exam Manager — Configuration Classes
Environment-specific configuration for development, production, and testing.
"""
import os
from datetime import timedelta


class Config:
    """Base configuration — shared by all environments"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    TESTING = False

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,   # Verify connections before using
        'pool_recycle': 3600,    # Recycle connections every hour
    }

    # Session security
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # File uploads
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB limit

    # Rate limiting storage (in-memory by default)
    RATELIMIT_STORAGE_URI = 'memory://'

    # WTF CSRF
    WTF_CSRF_ENABLED = False


class DevelopmentConfig(Config):
    """Development — debug on, SQLite, relaxed security"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///exam_manager.db'
    )
    # Allow HTTP cookies in development
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production — debug off, strict security, PostgreSQL"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://exam_user:exam_pass@localhost:5432/exam_manager'
    )
    SESSION_COOKIE_SECURE = True

    # Stricter SQL alchemy pool for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 10,
        'max_overflow': 20,
    }


class TestingConfig(Config):
    """Testing — in-memory DB, CSRF off"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Registry — used by app.py to select config
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
