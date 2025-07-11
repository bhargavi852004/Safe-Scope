# config.py
from dotenv import load_dotenv
import os

class Config:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()  # Ensure the .env file is loaded

        # Environment variables from .env file
        self.SECRET_KEY = os.getenv("SECRET_KEY")
        self.DEBUG = os.getenv("DEBUG") == "True"  # Convert to boolean
        self.ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",")
        self.MONGO_URI = os.getenv("MONGO_URI")

        # Email configuration
        self.EMAIL_HOST = os.getenv("EMAIL_HOST")
        self.EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
        self.EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
        self.EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
        self.EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS") == "True"

        # Together.ai API Key
        self.TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

    def __repr__(self):
        return f"Config(SECRET_KEY: {self.SECRET_KEY}, DEBUG: {self.DEBUG})"
