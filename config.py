"""
Configuration module for Cloud Inventory Management System.
Handles environment variables, AWS credential discovery, and application defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Find and load .env file from the project root if present
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=False)

# AWS Settings
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

# DynamoDB Settings
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "InventoryItems")
DYNAMODB_ENDPOINT_URL = os.getenv("DYNAMODB_ENDPOINT_URL")  # e.g., http://localhost:8000 for local testing

# Application Defaults
DEFAULT_LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "5"))


def get_config_summary() -> dict:
    """
    Returns safe configuration metadata for UI diagnostic display,
    masking sensitive secret keys.
    """
    masked_key = (
        f"{AWS_ACCESS_KEY_ID[:4]}...{AWS_ACCESS_KEY_ID[-4:]}"
        if AWS_ACCESS_KEY_ID and len(AWS_ACCESS_KEY_ID) > 8
        else ("Configured" if AWS_ACCESS_KEY_ID else "Not Set in .env (Using AWS Default Chain / IAM)")
    )

    return {
        "region": AWS_REGION,
        "table_name": DYNAMODB_TABLE_NAME,
        "endpoint_url": DYNAMODB_ENDPOINT_URL or "AWS Cloud (Default Public Endpoint)",
        "access_key_preview": masked_key,
        "is_local_endpoint": bool(DYNAMODB_ENDPOINT_URL),
        "low_stock_threshold": DEFAULT_LOW_STOCK_THRESHOLD,
    }
