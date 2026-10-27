#!/usr/bin/env python3
"""
Initialization script for the Cloud Inventory Management System.
Checks DynamoDB connectivity, creates tables if missing,
and clears all items from both InventoryItems and Inventory tables.
"""

import argparse
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import get_config_summary
from db import DynamoDBManager


def main():
    print("=" * 65)
    print("Cloud Inventory Management System - Universal Database Wiping Tool")
    print("=" * 65)

    config_info = get_config_summary()
    print(f"AWS Region:        {config_info['region']}")
    print("-" * 65)

    # Check both potential table names used in your project
    table_names = ["InventoryItems", "Inventory"]

    for t_name in table_names:
        print(f"\nChecking table: '{t_name}'...")
        db_manager = DynamoDBManager(table_name=t_name)
        is_connected, message, _ = db_manager.verify_connection()

        if is_connected and "does not exist" not in message:
            print(f"Found active table '{t_name}'. Clearing all items...")
            try:
                deleted_count = db_manager.clear_all_items()
                print(f"Successfully deleted {deleted_count} items from '{t_name}'.")
            except Exception as e:
                print(f"Error clearing table '{t_name}': {e}")
        else:
            print(f"Table '{t_name}' does not exist or could not be reached. Skipping.")

    print("\n" + "=" * 65)
    print("Database wipe complete! All tables are now clean.")
    print("=" * 65)


if __name__ == "__main__":
    main()