"""
Streamlit Frontend for Cloud Inventory Management System.
Connected to AWS DynamoDB via db.py layer.
"""

from datetime import datetime
import pandas as pd
import streamlit as st

import config
from db import DynamoDBManager

# Page Configuration
st.set_page_config(
    page_title="Cloud Inventory Management System",
    page_icon="📦",
    layout="wide",
)

# Initialize Database Manager
@st.cache_resource
def get_db_manager():
    return DynamoDBManager()

db = get_db_manager()

def main():
    st.title("📦 Cloud Inventory Management System")
    st.markdown("Manage your inventory securely with AWS DynamoDB and Streamlit.")

    # Sidebar Navigation
    st.sidebar.header("Navigation")
    choice = st.sidebar.radio("Go to", ["View Inventory", "Add New Item", "Manage Stock", "Low Stock Alerts"])

    try:
        if choice == "View Inventory":
            st.subheader("📋 Current Inventory Items")
            items = db.get_all_items()
            
            if not items:
                st.info("No items found in the inventory. Use 'Add New Item' to get started.")
            else:
                df = pd.DataFrame(items)
                st.dataframe(df, use_container_width=True)
                
                # Metrics overview
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Unique Items", len(items))
                with col2:
                    total_qty = sum(int(item.get("quantity", 0)) for item in items)
                    st.metric("Total Stock Quantity", total_qty)
                with col3:
                    total_val = sum(float(item.get("price", 0)) * int(item.get("quantity", 0)) for item in items)
                    st.metric("Total Inventory Value", f"${total_val:,.2f}")

        elif choice == "Add New Item":
            st.subheader("➕ Add New Inventory Item")
            with st.form("add_item_form"):
                item_name = st.text_input("Item Name")
                category = st.text_input("Category")
                quantity = st.number_input("Quantity", min_value=0, step=1)
                price = st.number_input("Price ($)", min_value=0.0, format="%.2f")
                supplier = st.text_input("Supplier")
                discount_percentage = st.number_input("Discount Percentage (%)", min_value=0.0, max_value=100.0, step=0.1)
                
                submitted = st.form_submit_button("Add Item")
                if submitted:
                    if not item_name:
                        st.error("Item Name is required.")
                    else:
                        item_data = {
                            "item_name": item_name,
                            "category": category,
                            "quantity": int(quantity),
                            "price": float(price),
                            "supplier": supplier,
                            "discount_percentage": float(discount_percentage)
                        }
                        db.add_item(item_data)
                        st.success(f"Successfully added '{item_name}' to inventory!")

        elif choice == "Manage Stock":
            st.subheader("⚙️ Update or Delete Items")
            items = db.get_all_items()
            if not items:
                st.info("No items available to manage.")
            else:
                item_options = {f"{item['item_name']} (ID: {item['item_id']})": item['item_id'] for item in items}
                selected_label = st.selectbox("Select Item", list(item_options.keys()))
                selected_id = item_options[selected_label]
                
                item_details = db.get_item(selected_id)
                if item_details:
                    st.write(f"**Current Quantity:** {item_details.get('quantity', 0)}")
                    st.write(f"**Current Price:** ${item_details.get('price', 0):,.2f}")
                    
                    action = st.radio("Action", ["Adjust Stock Quantity", "Edit Item Details", "Delete Item"])
                    
                    if action == "Adjust Stock Quantity":
                        delta = st.number_input("Stock Adjustment (+ to add, - to reduce)", value=0, step=1)
                        if st.button("Apply Adjustment"):
                            try:
                                db.adjust_stock(selected_id, int(delta))
                                st.success("Stock updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
                                
                    elif action == "Edit Item Details":
                        with st.form("edit_form"):
                            new_price = st.number_input("New Price ($)", value=float(item_details.get('price', 0.0)), format="%.2f")
                            new_qty = st.number_input("New Quantity", value=int(item_details.get('quantity', 0)), step=1)
                            updated = st.form_submit_button("Save Changes")
                            if updated:
                                db.update_item(selected_id, {"price": float(new_price), "quantity": int(new_qty)})
                                st.success("Item updated successfully!")
                                st.rerun()
                                
                    elif action == "Delete Item":
                        if st.button("Confirm Delete", type="primary"):
                            db.delete_item(selected_id)
                            st.success("Item deleted successfully!")
                            st.rerun()

        elif choice == "Low Stock Alerts":
            st.subheader("⚠️ Low Stock Items")
            items = db.get_all_items()
            threshold = getattr(config, 'LOW_STOCK_THRESHOLD', 5)
            low_stock_items = [item for item in items if int(item.get("quantity", 0)) <= threshold]
            
            if not low_stock_items:
                st.success(f"All items are above the low stock threshold ({threshold} units).")
            else:
                st.warning(f"Found {len(low_stock_items)} item(s) at or below the threshold of {threshold} units.")
                df_low = pd.DataFrame(low_stock_items)
                st.dataframe(df_low, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred while communicating with DynamoDB: {e}")

if __name__ == "__main__":
    main()