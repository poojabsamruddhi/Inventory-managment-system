"""
Curated sample inventory data for testing and demonstration.
Spans primary enterprise categories: Furniture, Groceries, Accessories, Electronics, and Apparel.
Includes stock quantities, unit prices, supplier details, and discount percentages.
"""

from datetime import datetime, timezone
import uuid

SAMPLE_INVENTORY = [
    # --- FURNITURE ---
    {
        "item_id": str(uuid.uuid4()),
        "item_name": "Herman Miller Aeron Ergonomic Chair (Graphite, Size B)",
        "category": "Furniture",
        "quantity": 4,  # Low stock alert
        "unit_price": 1395.00,
        "discount_percentage": 10.0,
        "supplier": "Herman Miller Commercial Group",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },
    {
        "item_id": str(uuid.uuid4()),
        "item_name": "Autonomous SmartDesk Pro (60x30 Solid Bamboo)",
        "category": "Furniture",
        "quantity": 8,
        "unit_price": 649.00,
        "discount_percentage": 15.0,
        "supplier": "Autonomous Workspaces Inc.",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },
    {
        "item_id": str(uuid.uuid4()),
        "item_name": "Steelcase Gesture Executive Task Chair",
        "category": "Furniture",
        "quantity": 2,  # Low stock alert
        "unit_price": 1280.00,
        "discount_percentage": 5.0,
        "supplier": "Steelcase Enterprise Wholesale",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },

    # --- GROCERIES ---
    {
        "item_id": str(uuid.uuid4()),
        "item_name": "Single Origin Organic EVOO Cold-Pressed (1L Glass Bottle)",
        "category": "Groceries",
        "quantity": 45,
        "unit_price": 24.99,
        "discount_percentage": 0.0,
        "supplier": "Mediterranean Harvest Direct",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },
    {
        "item_id": str(uuid.uuid4()),
        "item_name": "Artisan Roasted Whole Bean Espresso Coffee (2.5 lb Bag)",
        "category": "Groceries",
        "quantity": 32,
        "unit_price": 19.50,
        "discount_percentage": 10.0,
        "supplier": "Blue Ridge Roasters",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },
    {
        "item_id": str(uuid.uuid4()),
        "item_name": "Pure New Zealand Raw Manuka Honey (UMF 15+, 500g)",
        "category": "Groceries",
        "quantity": 3,  # Low stock alert
        "unit_price": 68.00,
        "discount_percentage": 12.0,
        "supplier": "Kiwi Apiaries Ltd",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },

    # --- ACCESSORIES ---
    {
        "item_id": str(uuid.uuid4()),
        "item_name": "Bellroy Slim Leather RFID Travel Wallet",
        "category": "Accessories",
        "quantity": 24,
        "unit_price": 89.00,
        "discount_percentage": 10.0,
        "supplier": "Bellroy Australia Dist.",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },
    {
        "item_id": str(uuid.uuid4()),
        "item_name": "Peak Design Everyday Camera Backpack 20L (Charcoal)",
        "category": "Accessories",
        "quantity": 5,
        "unit_price": 279.95,
        "discount_percentage": 15.0,
        "supplier": "Peak Design LLC",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },
    {
        "item_id": str(uuid.uuid4()),
        "item_name": "Ray-Ban Classic Aviator Polarized Sunglasses (Gold/Green)",
        "category": "Accessories",
        "quantity": 0,  # Out of stock!
        "unit_price": 213.00,
        "discount_percentage": 20.0,
        "supplier": "Luxottica Group Wholesale",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },

    # --- ELECTRONICS ---
    {
        "item_id": str(uuid.uuid4()),
        "item_name": "Apple MacBook Pro 14\" M3 Pro (18GB / 512GB Space Black)",
        "category": "Electronics",
        "quantity": 3,  # Low stock alert
        "unit_price": 1999.00,
        "discount_percentage": 5.0,
        "supplier": "Apple Authorized Enterprise",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },
    {
        "item_id": str(uuid.uuid4()),
        "item_name": "Dell UltraSharp 27\" 4K USB-C Hub Monitor (U2723QE)",
        "category": "Electronics",
        "quantity": 7,
        "unit_price": 579.50,
        "discount_percentage": 8.0,
        "supplier": "Dell Global Solutions",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },
    {
        "item_id": str(uuid.uuid4()),
        "item_name": "Sony WH-1000XM5 Wireless Active Noise-Canceling Headphones",
        "category": "Electronics",
        "quantity": 16,
        "unit_price": 348.00,
        "discount_percentage": 15.0,
        "supplier": "Sony Electronics Direct",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },

    # --- APPAREL ---
    {
        "item_id": str(uuid.uuid4()),
        "item_name": "Patagonia Better Sweater 1/4-Zip Fleece Jacket (Navy)",
        "category": "Apparel",
        "quantity": 19,
        "unit_price": 139.00,
        "discount_percentage": 10.0,
        "supplier": "Patagonia Outdoor Provisions",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },
    {
        "item_id": str(uuid.uuid4()),
        "item_name": "Lululemon ABC Classic-Fit Warpstreme Pant (32x32 Obsidian)",
        "category": "Apparel",
        "quantity": 28,
        "unit_price": 128.00,
        "discount_percentage": 0.0,
        "supplier": "Lululemon Athletic Wholesale",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },
    {
        "item_id": str(uuid.uuid4()),
        "item_name": "Allbirds Men's Wool Runners Everyday Sneaker (Natural Grey)",
        "category": "Apparel",
        "quantity": 1,  # Critical low stock!
        "unit_price": 110.00,
        "discount_percentage": 25.0,
        "supplier": "Allbirds Sustainable Footwear",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    },
]
