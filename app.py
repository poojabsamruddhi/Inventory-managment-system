from datetime import datetime
from decimal import Decimal
import hashlib
import os
import re

for env_key in ['AWS_SESSION_TOKEN', 'AWS_SECURITY_TOKEN']:
    if env_key in os.environ:
        del os.environ[env_key]

import pandas as pd
import streamlit as st

import config
from db import DynamoDBManager

st.set_page_config(
    page_title='Online Inventory Management System',
    page_icon='📦',
    layout='wide',
)

css_styles = (
    "<style>"
    ".stApp, [data-testid='stAppViewContainer'] { background: radial-gradient(circle at top left, #0f2027, #203a43, #2c5364); background-attachment: fixed; }"
    "[data-testid='stHeader'] { background: rgba(15, 32, 39, 0.85); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255, 255, 255, 0.1); }"
    "h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 700 !important; letter-spacing: -0.02em; }"
    "p, li, label, span { color: #cbd5e1 !important; }"
    ".enterprise-hero { background: linear-gradient(135deg, rgba(30, 58, 138, 0.85) 0%, rgba(37, 99, 235, 0.8) 100%); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.18); border-radius: 24px; padding: 2.2rem 2.8rem; margin-bottom: 1.5rem; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3); display: flex; justify-content: space-between; align-items: center; }"
    ".hero-title { color: white !important; font-size: 2.2rem !important; font-weight: 700 !important; margin: 0 !important; }"
    ".hero-subtitle { color: #93c5fd !important; font-size: 1.05rem !important; margin-top: 0.4rem !important; margin-bottom: 0 !important; }"
    ".shop-id-badge { background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.25); color: white; padding: 0.5rem 1rem; border-radius: 30px; font-weight: 600; font-size: 0.95rem; letter-spacing: 0.02em; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); }"
    "[data-testid='metric-container'] { background: rgba(255, 255, 255, 0.07); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 16px; padding: 1.2rem 1.4rem; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15); }"
    "[data-testid='stMetricValue'] { color: #60a5fa !important; font-weight: 800 !important; font-size: 1.8rem !important; }"
    "[data-testid='stMetricLabel'] { color: #93c5fd !important; }"
    ".stButton > button, .stFormSubmitButton > button { border-radius: 12px; font-weight: 650; border: 1px solid rgba(255, 255, 255, 0.2); background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: #ffffff; min-height: 2.8rem; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); transition: all 0.3s ease; }"
    ".stButton > button:hover, .stFormSubmitButton > button:hover { border-color: rgba(255, 255, 255, 0.4); background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: #ffffff; box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5); }"
    "[data-testid='stSidebar'] { background: rgba(15, 32, 39, 0.95); border-right: 1px solid rgba(255, 255, 255, 0.1); }"
    "div[data-baseweb='input'] > div, div[data-baseweb='select'] > div, input, textarea, select { background-color: #ffffff !important; background: #ffffff !important; color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; border-color: rgba(255, 255, 255, 0.3) !important; border-radius: 10px !important; }"
    "div[data-baseweb='select'] span { color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; }"
    ".total-calc-box { background: rgba(37, 99, 235, 0.25); border: 1px solid rgba(96, 165, 250, 0.5); border-radius: 10px; padding: 0.55rem 1rem; color: #ffffff; font-weight: 700; font-size: 1.1rem; text-align: center; margin-top: 1.7rem; }"
    "</style>"
)
st.markdown(css_styles, unsafe_allow_html=True)


@st.cache_resource
def get_db():
    return DynamoDBManager()


db = get_db()


def load_inventory(shop_id: str):
    try:
        all_items = db.get_all_items()
        return [item for item in all_items if item.get('ShopID') == shop_id]
    except Exception as e:
        st.error(f'Failed to load inventory: {str(e)}')
        return []


def format_currency(value):
    try:
        return f'₹{float(value):,.2f}'
    except:
        return '₹0.00'


def generate_product_id(name: str) -> str:
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name).strip().upper()
    slug = re.sub(r'\s+', '_', clean_name)
    return f'PROD-{slug}' if slug else 'PROD-UNKNOWN'


def format_display_id(raw_id: str) -> str:
    return raw_id.split('__', 1)[-1] if '__' in str(raw_id) else str(raw_id)


if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'shop_id' not in st.session_state:
    st.session_state.shop_id = ''
if 'shop_name' not in st.session_state:
    st.session_state.shop_name = ''
if 'shop_phone' not in st.session_state:
    st.session_state.shop_phone = ''
if 'shop_category' not in st.session_state:
    st.session_state.shop_category = 'Grocery & Supermarket'

if not st.session_state.logged_in:
    login_banner = (
        "<div style='background: linear-gradient(135deg, rgba(30, 58, 138, 0.85) 0%, rgba(37, 99, 235, 0.8) 100%); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.18); border-radius: 24px; padding: 2.2rem 2.8rem; text-align: center; max-width: 580px; margin: 3rem auto 1.5rem auto; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);'>"
        "<div style='font-size: 2.5rem; margin-bottom: 0.5rem;'>📦</div>"
        "<h1 style='font-size: 2.2rem; margin: 0; color: white !important;'>Online Inventory Management</h1>"
        "<p style='font-size: 1.1rem; margin-top: 0.5rem; color: #93c5fd !important;'>Authenticate your shop node to access secure database storage</p>"
        "</div>"
    )
    st.markdown(login_banner, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        with st.form('enterprise_login_form'):
            input_shop_name = st.text_input('Shop Name', placeholder='e.g., Samruddhi stores')
            input_phone = st.text_input('Manager Contact Number', placeholder='e.g., +91 9876543210')
            input_category = st.selectbox(
                'Business Category',
                [
                    'Grocery & Supermarket',
                    'Clothing & Apparel',
                    'Electronics & Gadgets',
                    'Pharmacy & Medical',
                    'Stationery & Books',
                    'Hardware & General',
                    'Other',
                ],
            )

            submitted = st.form_submit_button('🔒 Initialize Secure Session', width='stretch')

            if submitted:
                if input_shop_name.strip() and input_phone.strip():
                    st.session_state.shop_name = input_shop_name.strip()
                    st.session_state.shop_phone = input_phone.strip()
                    st.session_state.shop_category = input_category

                    raw_id_string = f"{input_shop_name.strip().upper()}-{input_phone.strip()}"
                    stable_hash = int(hashlib.md5(raw_id_string.encode('utf-8')).hexdigest(), 16)
                    st.session_state.shop_id = f"SHOP-{stable_hash % 90000 + 10000}"

                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error('⚠️ Shop Name and Contact Number are required parameters.')

else:
    with st.sidebar:
        st.markdown(f'### 🏪 {st.session_state.shop_name}')
        st.markdown(f'🆔 **Shop ID:** `{st.session_state.shop_id}`')
        st.markdown(f'📞 **Support:** {st.session_state.shop_phone}')
        st.markdown(f'📂 **Sector:** {st.session_state.shop_category}')
        st.divider()

        if st.button('🚪 Terminate Session', width='stretch'):
            st.session_state.logged_in = False
            st.rerun()

        st.markdown(
            f'<p style="font-size: 0.75rem; text-align: center; margin-top: 3rem; color: #93c5fd;">Table: <b>{config.DYNAMODB_TABLE_NAME}</b><br>Status: <span style="color: #4ade80; font-weight: bold;">🟢 Connected</span></p>',
            unsafe_allow_html=True,
        )

    hero_html = (
        f"<div class='enterprise-hero'>"
        f"<div><h2 class='hero-title'>Welcome, {st.session_state.shop_name}</h2>"
        f"<p class='hero-subtitle'>Real-time overview of your inventory</p></div>"
        f"<div><div class='shop-id-badge'>🆔 {st.session_state.shop_id}</div></div>"
        f"</div>"
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    data = load_inventory(st.session_state.shop_id)
    df = pd.DataFrame(data) if data else pd.DataFrame()

    total_products = len(df) if not df.empty else 0
    total_stock_units = int(df['quantity'].sum()) if not df.empty and 'quantity' in df.columns else 0
    low_stock_count = len(df[df['quantity'] < config.DEFAULT_LOW_STOCK_THRESHOLD]) if not df.empty and 'quantity' in df.columns else 0
    total_valuation = (pd.to_numeric(df['unit_price'], errors='coerce') * pd.to_numeric(df['quantity'], errors='coerce')).sum() if not df.empty and 'unit_price' in df.columns and 'quantity' in df.columns else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric('📦 Active Items', total_products)
    m2.metric('⚠️ Low Stock Alerts', low_stock_count)
    m3.metric('📊 Aggregate Units', f'{total_stock_units:,}')
    m4.metric('💰 Total Asset Valuation', format_currency(total_valuation))

    st.divider()

    if not df.empty and 'quantity' in df.columns:
        low_items_list = df[df['quantity'] < config.DEFAULT_LOW_STOCK_THRESHOLD]['item_name'].tolist()
        if low_items_list:
            st.warning(
                f'🚨 **Critical Stock Warning**: Items falling below safety threshold ({config.DEFAULT_LOW_STOCK_THRESHOLD} units): {", ".join(low_items_list)}'
            )

    tab_view, tab_add, tab_manage = st.tabs(
        ['📋 Inventory Registry', '➕ Register New Item', '⚙️ Item Management']
    )

    with tab_view:
        st.markdown('### 🔍 Query & Analytics Grid')
        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            search_query = st.text_input('Filter by Product Name, Item ID, or Vendor', '').lower()
        with col_s2:
            stock_filter = st.selectbox(
                'Inventory Status Filter',
                [
                    'All Operating Stock',
                    'Optimal Stock Level',
                    f'Critical Stock (<{config.DEFAULT_LOW_STOCK_THRESHOLD})',
                ],
            )

        if not df.empty:
            filtered_df = df.copy()
            filtered_df['display_id'] = filtered_df.get('item_id', pd.Series(dtype='str')).apply(format_display_id)
            filtered_df['quantity'] = pd.to_numeric(filtered_df['quantity'], errors='coerce').fillna(0)
            filtered_df['unit_price'] = pd.to_numeric(filtered_df['unit_price'], errors='coerce').fillna(0.0)

            if search_query:
                filtered_df = filtered_df[
                    filtered_df.get('item_name', pd.Series(dtype='str')).str.lower().str.contains(search_query, na=False)
                    | filtered_df['display_id'].str.lower().str.contains(search_query, na=False)
                    | filtered_df.get('supplier', pd.Series(dtype='str')).str.lower().str.contains(search_query, na=False)
                ]

            if stock_filter.startswith('Critical Stock'):
                filtered_df = filtered_df[filtered_df['quantity'] < config.DEFAULT_LOW_STOCK_THRESHOLD]
            elif stock_filter == 'Optimal Stock Level':
                filtered_df = filtered_df[filtered_df['quantity'] >= config.DEFAULT_LOW_STOCK_THRESHOLD]

            display_df = pd.DataFrame()
            display_df['Item ID'] = filtered_df['display_id']
            display_df['Product Name'] = filtered_df.get('item_name', '')
            display_df['Category Classification'] = filtered_df.get('category', '')
            display_df['Available Stock'] = filtered_df.apply(
                lambda row: f"{int(row['quantity'])} {row.get('unit', 'Units')}", axis=1
            )
            display_df['Unit Price (1 Qty)'] = filtered_df['unit_price'].apply(format_currency)
            display_df['Total Amount'] = (filtered_df['quantity'] * filtered_df['unit_price']).apply(format_currency)
            display_df['Inventory Health'] = filtered_df['quantity'].apply(
                lambda x: '⚠️ Critical' if x < config.DEFAULT_LOW_STOCK_THRESHOLD else '🟢 Optimal'
            )
            display_df['Vendor / Supplier'] = filtered_df.get('supplier', 'N/A')
            display_df['Last Audit Timestamp'] = filtered_df.get('last_updated', datetime.now().strftime('%Y-%m-%d %H:%M'))

            st.dataframe(display_df, width='stretch', hide_index=True)

            csv_bytes = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label='📥 Export Audit Report (CSV)',
                data=csv_bytes,
                file_name=f"{st.session_state.shop_name.replace(' ', '_')}_audit_report.csv",
                mime='text/csv',
            )
        else:
            st.info('📭 Registry is currently unpopulated. Use the **Register New Item** tab to initialize records.')

    with tab_add:
        st.markdown('### ➕ Inventory Ingestion Pipeline')
        st.info('ℹ️ Enter Total Quantity, select measurement unit, and enter price for 1 quantity — the Total Amount calculates automatically.')

        with st.container(border=True):
            prod_name = st.text_input('Product Name', placeholder='e.g., Sugar', key='add_prod_name')

            c_cat, c_sup = st.columns(2)
            with c_cat:
                category = st.selectbox(
                    'Sector Classification',
                    [
                        'Grains & Staples',
                        'Beverages',
                        'Dairy & Bakery',
                        'Snacks & Sweets',
                        'Household Essentials',
                        'Personal Care',
                        'Pharmacy & Medical',
                        'Electronics',
                        'Apparel',
                        'Industrial / General',
                    ],
                    key='add_category',
                )
            with c_sup:
                supplier = st.text_input('Vendor / Supplier Source', placeholder='e.g., global traders', key='add_supplier')

            c_qt, c_unit, c_pr, c_tot = st.columns([1, 1, 1, 1.2])
            with c_qt:
                quantity = st.number_input('Total Quantity', min_value=0, step=1, value=0, key='add_qty')
            with c_unit:
                unit_type = st.selectbox(
                    'Unit',
                    ['Units', 'Kg', 'Grams', 'Liters', 'ML', 'Packets', 'Boxes', 'Pieces'],
                    key='add_unit_type',
                )
            with c_pr:
                price = st.number_input('Price per Unit (₹)', min_value=0.0, step=1.0, format='%.2f', value=0.0, key='add_price')
            with c_tot:
                calculated_total = float(quantity) * float(price)
                st.markdown(
                    f'<div class="total-calc-box">Total: ₹{calculated_total:,.2f}</div>',
                    unsafe_allow_html=True,
                )

            if st.button('⚡ Commit Record to Database', width='stretch'):
                if prod_name.strip():
                    try:
                        clean_prod_id = generate_product_id(prod_name)
                        db_item_id = f"{st.session_state.shop_id}__{clean_prod_id}"
                        
                        existing_item = db.get_item(db_item_id) if hasattr(db, 'get_item') else None
                        
                        final_qty = int(quantity)
                        if existing_item and 'quantity' in existing_item:
                            final_qty += int(existing_item['quantity'])

                        item_payload = {
                            'item_id': db_item_id,
                            'ShopID': st.session_state.shop_id,
                            'shop_name': st.session_state.shop_name,
                            'item_name': prod_name.strip(),
                            'category': category,
                            'unit': unit_type,
                            'unit_price': float(price),
                            'quantity': final_qty,
                            'supplier': supplier or 'Direct Vendor',
                            'discount_percentage': 0.0,
                            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        db.add_item(item_payload)
                        st.success(
                            f'✅ Successfully registered **{prod_name}** ({quantity} {unit_type} added, total now {final_qty} {unit_type} @ ₹{price:,.2f}/unit = **₹{float(final_qty) * float(price):,.2f}**)'
                        )
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f'Ingestion Error: {str(e)}')
                else:
                    st.error('⚠️ Product Name is mandatory.')

    with tab_manage:
        st.markdown('### ⚙️ Item Lifecycle & Audit Management')
        if not df.empty:
            id_map = {
                f"{format_display_id(row['item_id'])} ({row.get('item_name', '')})": row['item_id']
                for _, row in df.iterrows()
            }
            display_labels = list(id_map.keys())

            col_upd, col_del = st.columns(2)

            with col_upd:
                st.markdown('#### ✏️ Modify Stock & Pricing')
                with st.container(border=True):
                    up_label = st.selectbox('Select Target Item ID', display_labels)
                    up_id = id_map[up_label]
                    new_qty = st.number_input('Revised Stock Quantity', min_value=0, step=1, key='upd_qty')
                    new_price = st.number_input('Revised Amount for 1 Unit (₹)', min_value=0.0, format='%.2f', key='upd_price')
                    revised_total = float(new_qty) * float(new_price)
                    st.info(f'💰 **Revised Total Valuation:** ₹{revised_total:,.2f}')

                    if st.button('Update Database Record', width='stretch'):
                        try:
                            db.update_item(
                                up_id,
                                {
                                    'quantity': int(new_qty),
                                    'unit_price': float(new_price),
                                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                },
                            )
                            st.success(f'Successfully updated Item `{format_display_id(up_id)}`')
                            st.rerun()
                        except Exception as e:
                            st.error(f'Update Error: {str(e)}')

            with col_del:
                st.markdown('#### 🗑️ Purge Item Record')
                with st.form('enterprise_delete_form'):
                    del_label = st.selectbox('Select Item to Purge', display_labels)
                    del_id = id_map[del_label]
                    confirm_del = st.checkbox('Authorize permanent deletion from database')

                    if st.form_submit_button('Execute Purge Protocol', width='stretch'):
                        if confirm_del:
                            db.delete_item(del_id)
                            st.success(f'Successfully purged Item `{format_display_id(del_id)}`')
                            st.rerun()
                        else:
                            st.warning('Authorization checkbox required to execute purge.')
        else:
            st.info('📭 No active records available for item management.')