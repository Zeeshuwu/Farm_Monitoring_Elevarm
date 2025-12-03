# src/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Google Earth Engine
    GEE_PROJECT_ID = os.getenv('GOOGLE_EARTH_ENGINE_PROJECT', 'your-project-id')
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', './data/farm_monitoring.db')
    
    # API Configuration
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 8000))
    
    # Celery Configuration
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Processing Parameters
    MAX_CLOUD_COVER = 30
    DATE_RANGE_START = "2025-02-12"
    DATE_RANGE_END = "2025-06-12"

config = Config()
