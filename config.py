"""Application configuration for POS System."""
import os
import sys
from pathlib import Path

# When built with PyInstaller: use exe directory for writable files (database)
if getattr(sys, 'frozen', False):
    basedir = Path(sys.executable).parent
else:
    basedir = Path(__file__).resolve().parent


def _get_pos_name():
    """Get POS/store name from config file or environment. Run set_pos_name.py to customize."""
    # 1. Check pos_config.json (in app/exe directory)
    config_path = basedir / 'pos_config.json'
    if config_path.exists():
        try:
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('POS_NAME', data.get('pos_name', data.get('store_name', 'POS System'))).strip()
        except (json.JSONDecodeError, KeyError, OSError):
            pass
    # 2. Environment variable
    return (os.environ.get('POS_NAME') or os.environ.get('STORE_NAME') or 'POS System').strip()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'pos-system-secret-key-change-in-production'
    
    # Customizable POS/Store name - set via pos_config.json or POS_NAME env var
    POS_NAME = _get_pos_name()
    
    # SQLite by default; override with DATABASE_URL for PostgreSQL/MySQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{basedir / "database.db"}'
    
    # PostgreSQL compatibility: SQLite doesn't support certain features
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
    
    # Session
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Low stock threshold
    LOW_STOCK_THRESHOLD = 10
    
    # Backup
    BACKUP_DIR = basedir / 'backups'


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
