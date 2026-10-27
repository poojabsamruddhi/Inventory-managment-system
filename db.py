"""
DynamoDB Database Access Layer.
Manages Boto3 connection, schema initialization, Decimal conversions,
and CRUD operations with comprehensive error handling and batch management.
"""

from datetime import datetime, timezone
from decimal import Decimal
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
import uuid

import boto3
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
    PartialCredentialsError,
)

import config

# Force-clear any stale or empty session tokens from environment variables
for token_key in ["AWS_SESSION_TOKEN", "AWS_SECURITY_TOKEN"]:
    if token_key in os.environ:
        del os.environ[token_key]

logger = logging.getLogger("inventory_db")
logging.basicConfig(level=logging.INFO)


def _to_decimal(val: Any) -> Any:
    """Helper to convert float and numeric types to Decimal for DynamoDB."""
    if isinstance(val, float):
        return Decimal(str(round(val, 2)))
    if isinstance(val, int):
        return Decimal(val)
    if isinstance(val, dict):
        return {k: _to_decimal(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_to_decimal(v) for v in val]
    return val


def _from_decimal(val: Any) -> Any:
    """Helper to convert DynamoDB Decimals to Python int/float for UI & Pandas."""
    if isinstance(val, Decimal):
        if val % 1 == 0:
            return int(val)
        return float(val)
    if isinstance(val, dict):
        return {k: _from_decimal(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_from_decimal(v) for v in val]
    return val


class DynamoDBManager:
    """Encapsulates all DynamoDB operations for the Inventory System."""

    def __init__(
        self,
        table_name: str = config.DYNAMODB_TABLE_NAME,
        region_name: str = config.AWS_REGION,
        endpoint_url: Optional[str] = config.DYNAMODB_ENDPOINT_URL,
    ):
        self.table_name = table_name
        self.region_name = region_name
        self.endpoint_url = endpoint_url
        self._session: Optional[boto3.Session] = None
        self._dynamodb_resource = None
        self._dynamodb_client = None

    def _get_session(self) -> boto3.Session:
        if self._session is None:
            # Securely load credentials from config / environment variables
            self._session = boto3.Session(
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                aws_session_token=None,  # Strictly None to prevent UnrecognizedClientException
                region_name=self.region_name,
            )
        return self._session

    @property
    def client(self):
        """Returns low-level DynamoDB client with custom endpoint if specified."""
        if self._dynamodb_client is None:
            session = self._get_session()
            kwargs: Dict[str, Any] = {"region_name": self.region_name}
            if self.endpoint_url:
                kwargs["endpoint_url"] = self.endpoint_url
            self._dynamodb_client = session.client("dynamodb", **kwargs)
        return self._dynamodb_client

    @property
    def resource(self):
        """Returns high-level DynamoDB resource with custom endpoint if specified."""
        if self._dynamodb_resource is None:
            session = self._get_session()
            kwargs: Dict[str, Any] = {"region_name": self.region_name}
            if self.endpoint_url:
                kwargs["endpoint_url"] = self.endpoint_url
            self._dynamodb_resource = session.resource("dynamodb", **kwargs)
        return self._dynamodb_resource

    @property
    def table(self):
        """Returns the DynamoDB Table resource."""
        return self.resource.Table(self.table_name)

    def verify_connection(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Tests AWS connectivity and checks whether the DynamoDB table exists."""
        try:
            response = self.client.list_tables(Limit=20)
            existing_tables = response.get("TableNames", [])

            if self.table_name in existing_tables:
                desc = self.client.describe_table(TableName=self.table_name)
                table_info = desc.get("Table", {})
                return (
                    True,
                    f"Successfully connected! Table '{self.table_name}' is ACTIVE.",
                    {
                        "table_status": table_info.get("TableStatus", "UNKNOWN"),
                        "item_count": table_info.get("ItemCount", 0),
                        "table_arn": table_info.get("TableArn", "N/A"),
                        "billing_mode": table_info.get("BillingModeSummary", {}).get(
                            "BillingMode", "PAY_PER_REQUEST"
                        ),
                    },
                )
            return (
                True,
                f"Connected to AWS, but table '{self.table_name}' does not exist yet.",
                {"table_status": "NOT_FOUND", "existing_tables": existing_tables},
            )

        except NoCredentialsError:
            return (
                False,
                "AWS credentials not found. Please configure credentials in .env or run aws configure.",
                {},
            )
        except PartialCredentialsError:
            return (
                False,
                "Incomplete AWS credentials found. Check both Access Key and Secret Key.",
                {},
            )
        except EndpointConnectionError as e:
            return (
                False,
                f"Failed to connect to DynamoDB endpoint ({self.endpoint_url or self.region_name}): {e}",
                {},
            )
        except ClientError as e:
            error = e.response.get("Error", {})
            return (
                False,
                f"AWS ClientError [{error.get('Code', 'Unknown')}]: {error.get('Message', str(e))}",
                {},
            )
        except Exception as e:
            return False, f"Unexpected error connecting to DynamoDB: {e}", {}

    def create_table_if_not_exists(self) -> Tuple[bool, str]:
        """Creates the InventoryItems table if it doesn't exist."""
        try:
            existing_tables = self.client.list_tables().get("TableNames", [])
            if self.table_name in existing_tables:
                return True, f"Table '{self.table_name}' already exists."

            logger.info("Creating DynamoDB table: %s...", self.table_name)
            self.client.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {"AttributeName": "item_id", "KeyType": "HASH"}
                ],
                AttributeDefinitions=[
                    {"AttributeName": "item_id", "AttributeType": "S"}
                ],
                BillingMode="PAY_PER_REQUEST",
            )

            self.client.get_waiter("table_exists").wait(
                TableName=self.table_name,
                WaiterConfig={"Delay": 2, "MaxAttempts": 30},
            )
            return True, f"Table '{self.table_name}' successfully created and active."

        except ClientError as e:
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            logger.error("Failed to create table: %s", error_msg)
            return False, f"Failed to create table: {error_msg}"
        except Exception as e:
            logger.error("Unexpected error creating table: %s", e)
            return False, f"Unexpected error creating table: {e}"

    def get_all_items(self) -> List[Dict[str, Any]]:
        """Fetches all inventory items and handles pagination."""
        items: List[Dict[str, Any]] = []
        try:
            response = self.table.scan()
            items.extend(response.get("Items", []))

            while "LastEvaluatedKey" in response:
                response = self.table.scan(
                    ExclusiveStartKey=response["LastEvaluatedKey"]
                )
                items.extend(response.get("Items", []))

            deserialized = [_from_decimal(item) for item in items]
            return sorted(
                deserialized,
                key=lambda x: str(x.get("item_name", "")).lower(),
            )
        except Exception as e:
            logger.error("Error fetching inventory items: %s", e)
            raise

    def get_items_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Returns all items belonging to a specific category."""
        all_items = self.get_all_items()
        if not category or category.lower() in (
            "all", "all categories", "all catalogs"
        ):
            return all_items
        return [
            item for item in all_items
            if str(item.get("category", "")).strip().lower()
            == category.strip().lower()
        ]

    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single item by item_id."""
        try:
            response = self.table.get_item(Key={"item_id": item_id})
            item = response.get("Item")
            return _from_decimal(item) if item else None
        except ClientError as e:
            logger.error("Error fetching item %s: %s", item_id, e)
            raise

    def add_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inserts a new inventory item into DynamoDB."""
        new_item = dict(item_data)
        if not new_item.get("item_id"):
            new_item["item_id"] = str(uuid.uuid4())

        try:
            new_item["discount_percentage"] = float(
                new_item.get("discount_percentage", 0.0)
            )
        except (ValueError, TypeError):
            new_item["discount_percentage"] = 0.0

        new_item["last_updated"] = datetime.now(timezone.utc).isoformat()
        dynamo_item = _to_decimal(new_item)

        try:
            self.table.put_item(Item=dynamo_item)
            return _from_decimal(dynamo_item)
        except ClientError as e:
            logger.error("Error adding item: %s", e)
            raise

    def update_item(self, item_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Updates an existing item and refreshes its timestamp."""
        try:
            current = self.get_item(item_id)
            if not current:
                raise ValueError(f"Item with ID '{item_id}' not found.")

            updated_item = {**current, **updates}
            updated_item["item_id"] = item_id

            if "discount_percentage" in updated_item:
                try:
                    updated_item["discount_percentage"] = float(
                        updated_item["discount_percentage"]
                    )
                except (ValueError, TypeError):
                    updated_item["discount_percentage"] = 0.0

            updated_item["last_updated"] = datetime.now(timezone.utc).isoformat()
            dynamo_item = _to_decimal(updated_item)
            self.table.put_item(Item=dynamo_item)
            return _from_decimal(dynamo_item)
        except ClientError as e:
            logger.error("Error updating item %s: %s", item_id, e)
            raise

    def adjust_stock(self, item_id: str, delta: int) -> Dict[str, Any]:
        """Adjusts stock without allowing the quantity to fall below zero."""
        current = self.get_item(item_id)
        if not current:
            raise ValueError(f"Item with ID '{item_id}' not found.")

        current_qty = int(current.get("quantity", 0))
        new_qty = current_qty + delta
        if new_qty < 0:
            raise ValueError(
                f"Cannot reduce stock by {-delta}. Current stock is only {current_qty}."
            )

        return self.update_item(item_id, {"quantity": new_qty})

    def delete_item(self, item_id: str) -> bool:
        """Deletes one item by its item_id."""
        try:
            self.table.delete_item(Key={"item_id": item_id})
            return True
        except ClientError as e:
            logger.error("Error deleting item %s: %s", item_id, e)
            raise

    def clear_all_items(self) -> int:
        """Deletes all inventory items using batch_writer."""
        all_items = self.get_all_items()
        deleted_count = 0
        if not all_items:
            return 0

        try:
            with self.table.batch_writer() as batch:
                for item in all_items:
                    item_id = item.get("item_id")
                    if item_id:
                        batch.delete_item(Key={"item_id": item_id})
                        deleted_count += 1
            logger.info("Cleared %s items from %s", deleted_count, self.table_name)
            return deleted_count
        except ClientError as e:
            logger.error("Error clearing table %s: %s", self.table_name, e)
            raise

    def seed_sample_data(self, sample_items: List[Dict[str, Any]]) -> int:
        """Inserts sample inventory items in a batch."""
        inserted_count = 0
        with self.table.batch_writer() as batch:
            for item in sample_items:
                item_copy = dict(item)
                if not item_copy.get("item_id"):
                    item_copy["item_id"] = str(uuid.uuid4())
                if not item_copy.get("last_updated"):
                    item_copy["last_updated"] = datetime.now(timezone.utc).isoformat()
                if "discount_percentage" not in item_copy:
                    item_copy["discount_percentage"] = 0.0
                batch.put_item(Item=_to_decimal(item_copy))
                inserted_count += 1
        return inserted_count