# ☁️ Cloud Inventory Management System

A production-ready, cloud-native **Inventory & Catalog Management System** built with **Python**, **Streamlit**, and **Amazon DynamoDB** (via **Boto3**).

Completely redesigned with a **Category-First Workflow**, real-time **Discount & Subtotal Valuations**, dynamic **Stock Tracking Badges**, **Timestamped CSV Invoice/Manifest Exports**, and an **Administrative Database Reset** tool.

---

## 🏛️ Architecture Overview

```
                      +---------------------------------------+
                      |          User Browser UI              |
                      |   (Streamlit Interactive Frontend)    |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |         Category Selector             |
                      | (Furniture | Groceries | Electronics) |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |               app.py                  |
                      |  (Catalog Views, Forms, Calculations) |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |               db.py                   |
                      | (Boto3 Layer, Decimal Converter, CRUD)|
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |     AWS DynamoDB ('InventoryItems')   |
                      |  (On-Demand Serverless Auto-scaling)  |
                      +---------------------------------------+
```

---

## 📋 Updated DynamoDB Table Schema (`InventoryItems`)

The database is built on a single-table design with on-demand capacity (`PAY_PER_REQUEST` billing mode):

| Attribute | DynamoDB Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `item_id` | **String (S)** | **Partition Key (PK)** - Unique UUID | `"c7a18b92-98e3-4f91-..."` |
| `item_name` | **String (S)** | Name of the product | `"Herman Miller Aeron Chair"` |
| `category` | **String (S)** | Product category | `"Furniture"`, `"Groceries"`, etc. |
| `quantity` | **Number (N)** | Units currently in stock | `4` |
| `unit_price` | **Number (N)** | Base price per unit in USD | `1395.00` |
| `discount_percentage`| **Number (N)** | Promotional/bulk discount % (0 - 90%) | `10.0` |
| `supplier` | **String (S)** | Vendor or distributor | `"Herman Miller Commercial"` |
| `last_updated` | **String (S)** | ISO 8601 UTC timestamp with date | `"2026-10-26T11:15:06+00:00"` |

---

## 🚀 Redesigned User Flow & Features

### 1. Step 1: Category / Catalog Selection First
- When opening the application, users are greeted by a prominent **Product Category Selector**:
  - 🛋️ **Furniture**
  - 🍎 **Groceries**
  - 👜 **Accessories**
  - 💻 **Electronics**
  - 👕 **Apparel**
  - 🌐 **All Catalogs (Overview)**
- Instantly displays category-scoped KPIs: **Catalog SKUs**, **Available Units**, **Net Valuation ($)**, and **Stock Alerts**.

### 2. Step 2: Filtered Inventory Grid
- Data grid displays **only products belonging to the selected category**.
- Interactive columns:
  - `Product Name`
  - `Stock Qty` (with glowing badges: In Stock, Low Stock, Out of Stock)
  - `Base Price ($)`
  - `Discount (%)`
  - `Disc. Price ($)`
  - `Subtotal ($)`
  - `Net Value ($)`
  - `Supplier`
  - `Last Updated`
- Real-time search query box within the catalog.
- Filter by stock levels (*In Stock Only*, *Low Stock*, *Out of Stock*).

### 3. Real-Time Dynamic Calculations
- Automatically computes:
  - **Gross Subtotal:** $\text{Quantity} \times \text{Unit Price}$
  - **Discount Amount:** $\text{Gross Subtotal} \times \left(\frac{\text{Discount \%}}{100}\right)$
  - **Net Inventory Value:** $\text{Gross Subtotal} - \text{Discount Amount}$
  - **Effective Unit Price:** $\text{Unit Price} \times \left(1 - \frac{\text{Discount \%}}{100}\right)$
- Both the **Add Item Form** and **Edit Item Form** feature an instant **Live Calculation Preview Box**.

### 4. Timestamped CSV Reports & Invoice Billing Summaries
- **Calculated Invoice / Billing Summary**:
  - Itemized table showing line-item quantities, discounts, and net amounts.
  - Generates a **dated, timestamped CSV**: `invoice_Furniture_YYYY-MM-DD_HHMMSS.csv`.
- **Full Inventory Manifest**:
  - Exports complete dataset with UUIDs and audit timestamps: `inventory_manifest_All_Catalogs_YYYY-MM-DD_HHMMSS.csv`.

### 5. Administrative Reset & Batch Management
- **Safe "Clear All Items" Tool**:
  - High-throughput batch deletion (`table.batch_writer()`) to wipe all existing records and start fresh with confirmation safeguards.
- **1-Click 15-Product Demo Seeder**:
  - Seeds 15 realistic enterprise items across all 5 standard categories with varied stock levels and discounts.

---

## 🛠️ Step-by-Step Setup & Execution

### 1. Configure AWS Credentials in `.env`
Ensure your `.env` contains your AWS credentials:
```ini
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
DYNAMODB_TABLE_NAME=InventoryItems
LOW_STOCK_THRESHOLD=5
```

### 2. Initialize / Seed the DynamoDB Table
```bash
# Seed 15 sample products with discounts across 5 categories
python setup_db.py --seed

# Or wipe and re-seed fresh:
python setup_db.py --clear --seed
```

### 3. Launch the Application
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 🧪 Unit Tests
Run the test suite to verify data serialization, Decimal precision, and discount calculations:
```bash
python test_units.py
```
