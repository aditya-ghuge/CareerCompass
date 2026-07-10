"""
CareerCompass AI - Configuration Module
Centralizes all application configuration.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    # ---------------------------------------------------------
    # Flask
    # ---------------------------------------------------------
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", os.urandom(32).hex())
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    TESTING = False

    # ---------------------------------------------------------
    # IBM watsonx.ai
    # ---------------------------------------------------------
    WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "").strip(" \"'")
    WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "").strip(" \"'")
    WATSONX_URL = os.getenv(
        "WATSONX_URL",
        "https://au-syd.ml.cloud.ibm.com"
    ).strip(" \"'")

    # ---------------------------------------------------------
    # Model
    # ---------------------------------------------------------
    GRANITE_MODEL_ID = os.getenv(
        "GRANITE_MODEL_ID",
        "meta-llama/llama-3-3-70b-instruct"
    ).strip(" \"'")

    # ---------------------------------------------------------
    # Generation Parameters
    # ---------------------------------------------------------
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))

    # Better for structured JSON generation
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))

    # Deterministic output
    TOP_P = float(os.getenv("TOP_P", "1.0"))

    TOP_K = int(os.getenv("TOP_K", "50"))

    REPETITION_PENALTY = float(
        os.getenv("REPETITION_PENALTY", "1.05")
    )

    # ---------------------------------------------------------
    # Application
    # ---------------------------------------------------------
    APP_PORT = int(os.getenv("APP_PORT", "5000"))

    @classmethod
    def validate(cls):
        """
        Validate required IBM credentials.
        Returns list of missing variables.
        """

        missing = []

        if not cls.WATSONX_API_KEY:
            missing.append("WATSONX_API_KEY")

        if not cls.WATSONX_PROJECT_ID:
            missing.append("WATSONX_PROJECT_ID")

        return missing


class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = "development"


class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = "production"


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


ActiveConfig = config_map.get(
    os.getenv("FLASK_ENV", "default"),
    DevelopmentConfig,
)