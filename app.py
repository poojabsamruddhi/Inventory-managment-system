from datetime import datetime
from decimal import Decimal
import os
import re

# --- STRIP STALE WINDOWS TOKENS ---
for env_key in ['AWS_SESSION_TOKEN', 'AWS_SECURITY_TOKEN']:
  if env_key in os.environ:
    del os.environ[env_key]

import pandas as pd
import streamlit as st

import config
from db import DynamoDBManager

# Page Configuration
st.set_page_config(
    page_title='Online Inventory Management System',
    page_icon='📦',
    layout='wide',
)

# --- ULTRA-MODERN GLASSMORPHISM & DEEP BLUE GRADIENT UI THEME ---
st.markdown(
    """
    <style>
    .stApp, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top left, #0f2027, #203a43, #2c5364);
        background-attachment: fixed;
    }

    [data-testid="stHeader"] {
        background: rgba(15, 32, 39, 0.85);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    p, li, label, span {
        color: #cbd5e1 !important;
    }

    .enterprise-hero {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.85) 0%, rgba(37, 99, 235, 0.8) 100%);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 24px;
        padding: 2.2rem 2.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .hero-title {
        color: white !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
    }

    .hero-subtitle {
        color: #93c5fd !important;
        font-size: 1.05rem !important;
        margin-top: 0.4rem !important;
        margin-bottom: 0 !important;
    }

    .shop-id-badge {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.25);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 30px;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 0.02em;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    [data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.07);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
    }

    [data-testid="stMetricValue"] {
        color: #60a5fa !important;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }

    [data-testid="stMetricLabel"] {
        color: #93c5fd !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        border-radius: 12px;
        font-weight: 650;
        border: 1px solid rgba(255, 255, 255, 0.2);
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: #ffffff;
        min-height: 2.8rem;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        transition: all 0.3s ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        border-color: rgba(255, 255, 255, 0.4);
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: #ffffff;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
    }

    [data-testid="stSidebar"] {
        background: rgba(15, 32, 39, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div,
    input, textarea, select {
        background-color: #ffffff !important;
        background: #ffffff !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="select"] span {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- INITIALIZE DATABASE MANAGER ---
@st.cache_resource
def get_db():
  return DynamoDBManager()


db = get_db()


# --- HELPER FUNCTIONS ---
@st.cache_data(ttl=300)
def load_inventory():
  try:
    return db.get_all_items()
  except Exception as e:
    st.error(f'Failed to load inventory: {str(e)}')
    return []


def format_currency(value):
  return f'₹{value:,.2f}'


def generate_product_id(name: str) -> str:
  clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name).strip().upper()
  slug = re.sub(r'\s+', '_', clean_name)
  return f'PROD-{slug}' if slug else 'PROD-UNKNOWN'


# --- COLLEGE DEMO DATA SET ---
DEMO_PRODUCTS = [
    {
        'item_id': 'PROD-BASMATI_RICE_5KG',
        'item_name': 'Basmati Rice 5kg',
        'category': 'Grains & Staples',
        'unit_price': 450.0,
        'quantity': 45,
        'supplier': 'India Gate Foods',
        'discount_percentage': 0.0,
    },
    {
        'item_id': 'PROD-SUNFLOWER_OIL_1L',
        'item_name': 'Sunflower Oil 1L',
        'category': 'Grains & Staples',
        'unit_price': 140.0,
        'quantity': 3,
        'supplier': 'Fortune Agro',
        'discount_percentage': 0.0,
    },
    {
        'item_id': 'PROD-TATA_SALT_1KG',
        'item_name': 'Tata Salt 1kg',
        'category': 'Grains & Staples',
        'unit_price': 28.0,
        'quantity': 60,
        'supplier': 'Tata Consumer',
        'discount_percentage': 0.0,
    },
    {
        'item_id': 'PROD-COLGATE_MAX_FRESH',
        'item_name': 'Colgate Max Fresh 150g',
        'category': 'Personal Care',
        'unit_price': 95.0,
        'quantity': 2,
        'supplier': 'Colgate-Palmolive',
        'discount_percentage': 0.0,
    },
    {
        'item_id': 'PROD-AMUL_BUTTER_500G',
        'item_name': 'Amul Butter 500g',
        'category': 'Dairy & Bakery',
        'unit_price': 275.0,
        'quantity': 18,
        'supplier': 'GCMMF Dairy',
        'discount_percentage': 0.0,
    },
    {
        'item_id': 'PROD-NESCAFE_CLASSIC',
        'item_name': 'Nescafe Classic Coffee 100g',
        'category': 'Beverages',
        'unit_price': 320.0,
        'quantity': 25,
        'supplier': 'Nestle India',
        'discount_percentage': 0.0,
    },
]


# --- SESSION STATE INITIALIZATION ---
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

# ==========================================
# STEP 1: SHOPKEEPER LOGIN PORTAL
# ==========================================
if not st.session_state.logged_in:
  st.markdown(
      """
        <div style="background: linear-gradient(135deg, rgba(30, 58, 138, 0.85) 0%, rgba(37, 99, 235, 0.8) 100%); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.18); border-radius: 24px; padding: 2.2rem 2.8rem; text-align: center; max-width: 580px; margin: 5rem auto 0 auto; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📦</div>
            <h1 style='font-size: 2.2rem; margin: 0; color: white !important;'>Online Inventory Management</h1>
            <p style='font-size: 1.1rem; margin-top: 0.5rem; color: #93c5fd !important;'>
                College Project Demonstration Portal
            </p>
        </div>
        """,
      unsafe_allow_html=True,
  )

  c1, c2, c3 = st.columns([1, 1.4, 1])
  with c2:
    with st.form('enterprise_login_form'):
      input_shop_name = st.text_input(
          'Shop Name', value='Samruddhi Stores'
      )
      input_phone = st.text_input(
          'Manager Contact Number', value='9876543210'
      )
      input_category = st.selectbox(
          'Business Category', [
              'Grocery & Supermarket',
              'Clothing & Apparel',
              'Electronics & Gadgets',
              'Pharmacy & Medical',
              'Stationery & Books',
              'Hardware & General',
              'Other',
          ]
      )

      submitted = st.form_submit_button('🔒 Initialize Secure Session', width='stretch')

      if submitted:
        if input_shop_name.strip() and input_phone.strip():
          st.session_state.shop_name = input_shop_name.strip()
          st.session_state.shop_phone = input_phone.strip()
          st.session_state.shop_category = input_category

          raw_id_string = f"{input_shop_name.strip().upper()}-{input_phone.strip()}"
          st.session_state.shop_id = f"SHOP-{abs(hash(raw_id_string)) % 90000 + 10000}"

          st.session_state.logged_in = True
          st.rerun()
        else:
          st.error('⚠️ Shop Name and Contact Number are required parameters.')

# ==========================================
# STEP 2: OPERATIONS DASHBOARD
# ==========================================
else:
  # Sidebar Profile
  with st.sidebar:
    st.markdown(f'### 🏪 {st.session_state.shop_name}')
    st.markdown(f'🆔 **Shop ID:** `{st.session_state.shop_id}`')
    st.markdown(f'📞 **Support:** {st.session_state.shop_phone}')
    st.markdown(f'📂 **Sector:** {st.session_state.shop_category}')
    st.divider()

    if st.button('✨ Load College Demo Data', width='stretch'):
      try:
        count = db.seed_sample_data(DEMO_PRODUCTS)
        st.success(f'Successfully loaded {count} demo products!')
        st.cache_data.clear()
        st.rerun()
      except Exception as e:
        st.error(f'Seeding error: {e}')

    if st.button('🚪 Terminate Session', width='stretch'):
      st.session_state.logged_in = False
      st.rerun()

    st.markdown(
        f'<p style="font-size: 0.75rem; text-align: center; margin-top: 3rem;'
        f' color: #93c5fd;">Table: <b>{config.DYNAMODB_TABLE_NAME}</b><br>Status:'
        ' <span style="color: #4ade80; font-weight: bold;">🟢 Connected</span></p>',
        unsafe_allow_html=True,
    )

  # Executive Header Banner
  st.markdown(
      f"""
        <div class="enterprise-hero">
            <div>
                <h2 class="hero-title">Welcome, {st.session_state.shop_name}</h2>
                <p class="hero-subtitle">Real-time overview of your inventory</p>
            </div>
            <div>
                <div class="shop-id-badge">🆔 {st.session_state.shop_id}</div>
            </div>
        </div>
        """,
      unsafe_allow_html=True,
  )

  data = load_inventory()
  df = pd.DataFrame(data) if data else pd.DataFrame()

  if df.empty:
    st.info('📭 Your inventory is currently empty. Click the button below to instantly populate sample products for your college presentation!')
    if st.button('🚀 Load Demo Products for Presentation', width='stretch'):
      try:
        db.seed_sample_data(DEMO_PRODUCTS)
        st.success('Demo items loaded successfully!')
        st.cache_data.clear()
        st.rerun()
      except Exception as e:
        st.error(f'Error loading demo data: {e}')

  total_products = len(df) if not df.empty else 0
  total_stock_units = (
      int(df['quantity'].sum())
      if not df.empty and 'quantity' in df.columns
      else 0
  )
  low_stock_count = (
      len(df[df['quantity'] < config.DEFAULT_LOW_STOCK_THRESHOLD])
      if not df.empty and 'quantity' in df.columns
      else 0
  )
  total_valuation = (
      (df['unit_price'] * df['quantity']).sum()
      if not df.empty and 'unit_price' in df.columns and 'quantity' in df.columns
      else 0
  )

  # Telemetry Cards
  m1, m2, m3, m4 = st.columns(4)
  m1.metric('📦 Active Items', total_products)
  m2.metric('⚠️ Low Stock Alerts', low_stock_count)
  m3.metric('📊 Aggregate Units', f'{total_stock_units:,}')
  m4.metric('💰 Total Asset Valuation', format_currency(total_valuation))

  st.divider()

  if not df.empty and 'quantity' in df.columns:
    low_items_list = df[df['quantity'] < config.DEFAULT_LOW_STOCK_THRESHOLD][
        'item_name'
    ].tolist()
    if low_items_list:
      st.warning(
          f'🚨 **Critical Stock Warning**: Items falling below safety threshold'
          f' ({config.DEFAULT_LOW_STOCK_THRESHOLD} units):'
          f' {", ".join(low_items_list)}'
      )

  # Navigation Tabs
  tab_view, tab_add, tab_manage = st.tabs(
      ['📋 Inventory Registry', '➕ Register New Item', '⚙️ Item Management']
  )

  # --- TAB 1: INVENTORY REGISTRY ---
  with tab_view:
    st.markdown('### 🔍 Query & Analytics Grid')
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
      search_query = st.text_input(
          'Filter by Product Name, Item ID, or Vendor', ''
      ).lower()
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
      if search_query:
        name_mask = filtered_df.get('item_name', pd.Series(dtype='str')).astype(str).str.lower().str.contains(search_query, na=False)
        id_mask = filtered_df.get('item_id', pd.Series(dtype='str')).astype(str).str.lower().str.contains(search_query, na=False)
        supp_mask = filtered_df.get('supplier', pd.Series(dtype='str')).astype(str).str.lower().str.contains(search_query, na=False)
        filtered_df = filtered_df[name_mask | id_mask | supp_mask]

      if stock_filter.startswith('Critical Stock'):
        filtered_df = filtered_df[
            filtered_df['quantity'] < config.DEFAULT_LOW_STOCK_THRESHOLD
        ]
      elif stock_filter == 'Optimal Stock Level':
        filtered_df = filtered_df[
            filtered_df['quantity'] >= config.DEFAULT_LOW_STOCK_THRESHOLD
        ]

      display_df = pd.DataFrame()
      display_df['Item ID'] = filtered_df.get('item_id', '')
      display_df['Product Name'] = filtered_df.get('item_name', '')
      display_df['Category Classification'] = filtered_df.get('category', '')
      display_df['Available Stock'] = filtered_df['quantity'].apply(
          lambda x: f'{x} units'
      )
      display_df['Inventory Health'] = filtered_df['quantity'].apply(
          lambda x: (
              '⚠️ Critical'
              if x < config.DEFAULT_LOW_STOCK_THRESHOLD
              else '🟢 Optimal'
          )
      )
      display_df['Unit Price'] = filtered_df['unit_price'].apply(
          format_currency
      )
      display_df['Vendor / Supplier'] = filtered_df.get('supplier', 'N/A')
      display_df['Last Audit Timestamp'] = filtered_df.get(
          'last_updated', datetime.now().strftime('%Y-%m-%d %H:%M')
      )

      st.dataframe(display_df, width='stretch', hide_index=True)

      csv_bytes = filtered_df.to_csv(index=False).encode('utf-8')
      st.download_button(
          label='📥 Export Audit Report (CSV)',
          data=csv_bytes,
          file_name=f"{st.session_state.shop_name.replace(' ', '_')}_audit_report.csv",
          mime='text/csv',
      )
    else:
      st.info(
          '📭 Registry is currently unpopulated. Use the sidebar or button above'
          ' to load demo records.'
      )

  # --- TAB 2: REGISTER NEW ITEM ---
  with tab_add:
    st.markdown('### ➕ Inventory Ingestion Pipeline')
    st.info(
        'ℹ️ Item IDs are compiled automatically from product names.'
        ' Identical product descriptions aggregate under a unified inventory'
        ' record.'
    )

    with st.form('enterprise_add_form', clear_on_submit=True):
      prod_name = st.text_input(
          'Product Name', placeholder='e.g., Premium Basmati Rice 5kg'
      )

      c_cat, c_sup = st.columns(2)
      with c_cat:
        category = st.selectbox(
            'Sector Classification', [
                'Grains & Staples',
                'Beverages',
                'Dairy & Bakery',
                'Snacks & Sweets',
                'Household Essentials',
                'Personal Care',
                'Electronics',
                'Apparel',
                'Industrial / General',
            ]
        )
      with c_sup:
        supplier = st.text_input(
            'Vendor / Supplier Source', placeholder='e.g., Global Agro Corp'
        )

      c_pr, c_qt = st.columns(2)
      with c_pr:
        price = st.number_input(
            'Unit Valuation / Selling Price (₹)', min_value=0.0, format='%.2f'
        )
      with c_qt:
        quantity = st.number_input(
            'Initial Ingestion Quantity', min_value=0, step=1
        )

      submitted = st.form_submit_button(
          '⚡ Commit Record to Database', width='stretch'
      )

      if submitted:
        if prod_name.strip():
          try:
            generated_product_id = generate_product_id(prod_name)
            item_payload = {
                'item_id': generated_product_id,
                'ShopID': st.session_state.shop_id,
                'item_name': prod_name.strip(),
                'category': category,
                'unit_price': float(price),
                'quantity': int(quantity),
                'supplier': supplier or 'Direct Vendor',
                'discount_percentage': 0.0,
            }
            db.add_item(item_payload)
            st.success(
                f'✅ Successfully registered **{prod_name}** under Item ID:'
                f' `{generated_product_id}`'
            )
            st.balloons()
            st.cache_data.clear()
            st.rerun()
          except Exception as e:
            st.error(f'Ingestion Error: {str(e)}')
        else:
          st.error('⚠️ Product Name is mandatory.')

  # --- TAB 3: ITEM MANAGEMENT ---
  with tab_manage:
    st.markdown('### ⚙️ Item Lifecycle & Audit Management')
    if not df.empty:
      item_ids = df['item_id'].tolist()

      col_upd, col_del = st.columns(2)

      with col_upd:
        st.markdown('#### ✏️ Modify Stock & Pricing')
        with st.form('enterprise_update_form'):
          up_id = st.selectbox('Select Target Item ID', item_ids)
          new_qty = st.number_input(
              'Revised Stock Quantity', min_value=0, step=1
          )
          new_price = st.number_input(
              'Revised Unit Valuation (₹)', min_value=0.0, format='%.2f'
          )

          if st.form_submit_button('Update Database Record', width='stretch'):
            try:
              db.update_item(
                  up_id,
                  {
                      'quantity': int(new_qty),
                      'unit_price': float(new_price),
                  },
              )
              st.success(f'Successfully updated Item `{up_id}`')
              st.cache_data.clear()
              st.rerun()
            except Exception as e:
              st.error(f'Update Error: {str(e)}')

      with col_del:
        st.markdown('#### 🗑️ Purge Item Record')
        with st.form('enterprise_delete_form'):
          del_id = st.selectbox('Select Item to Purge', item_ids)
          confirm_del = st.checkbox(
              'Authorize permanent deletion from database'
          )

          if st.form_submit_button('Execute Purge Protocol', width='stretch'):
            if confirm_del:
              db.delete_item(del_id)
              st.success(f'Successfully purged Item `{del_id}`')
              st.cache_data.clear()
              st.rerun()
            else:
              st.warning('Authorization checkbox required to execute purge.')
    else:
      st.info('📭 No active records available for item management.')