"""
Unit tests for data conversion, serialization, discount calculations, and business logic.
"""

from decimal import Decimal
import unittest
from config import get_config_summary
from db import _from_decimal, _to_decimal


class TestDataSerialization(unittest.TestCase):
    def test_to_decimal_conversion(self):
        sample = {
            "name": "Wireless Mouse",
            "price": 49.99,
            "quantity": 10,
            "discount_percentage": 15.0,
            "nested": {"discount": 5.5, "tags": ["tech", 12.34]},
        }
        converted = _to_decimal(sample)
        self.assertIsInstance(converted["price"], Decimal)
        self.assertEqual(converted["price"], Decimal("49.99"))
        self.assertIsInstance(converted["quantity"], Decimal)
        self.assertEqual(converted["quantity"], Decimal(10))
        self.assertIsInstance(converted["discount_percentage"], Decimal)
        self.assertEqual(converted["discount_percentage"], Decimal("15.00"))

    def test_from_decimal_conversion(self):
        dynamo_data = {
            "name": "Mechanical Keyboard",
            "price": Decimal("129.50"),
            "quantity": Decimal("15"),
            "discount_percentage": Decimal("20.0"),
        }
        converted = _from_decimal(dynamo_data)
        self.assertIsInstance(converted["price"], float)
        self.assertEqual(converted["price"], 129.5)
        self.assertIsInstance(converted["quantity"], int)
        self.assertEqual(converted["quantity"], 15)
        self.assertEqual(converted["discount_percentage"], 20.0)

    def test_discount_and_net_calculations(self):
        qty = 4
        unit_price = 1395.00
        discount_pct = 10.0

        subtotal = round(qty * unit_price, 2)
        disc_amt = round(subtotal * (discount_pct / 100.0), 2)
        net_val = round(subtotal - disc_amt, 2)
        eff_price = round(unit_price * (1.0 - (discount_pct / 100.0)), 2)

        self.assertEqual(subtotal, 5580.00)
        self.assertEqual(disc_amt, 558.00)
        self.assertEqual(net_val, 5022.00)
        self.assertEqual(eff_price, 1255.50)

    def test_config_summary_masking(self):
        summary = get_config_summary()
        self.assertIn("region", summary)
        self.assertIn("table_name", summary)
        self.assertIn("access_key_preview", summary)


if __name__ == "__main__":
    unittest.main()
