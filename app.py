from datetime import datetime
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import config
from db import DynamoDBManager

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize DB Manager safely
try:
    db = DynamoDBManager()
except Exception as e:
    print(f"Warning: Database initialization error: {e}")
    db = None

DEPARTMENT_LIST = [
    'Groceries & Staples',
    'Dairy & Bakery',
    'Fresh Fruits & Vegetables',
    'Flesh & Meat',
    'Beverages & Snacks',
    'Household Essentials',
    'Personal Care',
    'Electronics & Appliances'
]

def format_date_string(date_str):
    """Safely parse various date formats into DD/MM/YYYY HH:MM:SS"""
    if not date_str:
        return datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%d/%m/%Y %H:%M:%S')
    except Exception:
        try:
            dt = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%d/%m/%Y %H:%M:%S')
        except Exception:
            return date_str

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    shop_name = session.get('shop_name', 'Hypermarket Store')
    user_role = session.get('user_role', 'Store / Mart Admin')
    user_dept = session.get('department', 'All Sections')
    
    if user_role == 'Department Staff':
        selected_dept = user_dept
    else:
        selected_dept = request.args.get('dept', 'All Sections')
    
    all_shop_items = []
    filtered_items = []
    total_valuation = 0.0
    low_stock_count = 0
    
    try:
        if db:
            raw_items = db.get_all_items() or []
            all_shop_items = []
            for item in raw_items:
                if str(item.get('shop_name')).strip().lower() == str(shop_name).strip().lower():
                    item['last_updated'] = format_date_string(item.get('last_updated'))
                    all_shop_items.append(item)
            
            if selected_dept and selected_dept != 'All Sections':
                filtered_items = [item for item in all_shop_items if item.get('department') == selected_dept]
            else:
                filtered_items = all_shop_items
                
            total_valuation = sum(float(i.get('unit_price', 0)) * int(i.get('quantity', 0)) for i in filtered_items)
            low_stock_count = sum(1 for i in filtered_items if int(i.get('quantity', 0)) < getattr(config, 'DEFAULT_LOW_STOCK_THRESHOLD', 5))
    except Exception as e:
        flash(f"Database notice: Could not fetch live items ({str(e)}).", "warning")
        filtered_items = []
        all_shop_items = []

    return render_template(
        'index.html',
        items=filtered_items,
        all_items_raw=all_shop_items,
        shop_name=shop_name,
        user_role=user_role,
        department=user_dept,
        selected_dept=selected_dept,
        departments=DEPARTMENT_LIST,
        total_valuation=total_valuation,
        low_stock_count=low_stock_count
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        shop_name = request.form.get('shop_name', '').strip()
        admin_passcode = request.form.get('admin_passcode', '')

        if not shop_name or not admin_passcode:
            flash("Store Name and Passcode are required.", "warning")
            return render_template('register.html')

        if db:
            # Check if store already exists
            existing_store = db.get_store_account(shop_name)
            if existing_store:
                flash(f"The store '{shop_name}' is already registered. Please log in.", "warning")
                return redirect(url_for('login'))

            # Encrypt the password and save to database
            hashed_pw = generate_password_hash(admin_passcode)
            try:
                db.create_store_account(shop_name, hashed_pw)
                flash("Store registered successfully! You can now log in as Admin.", "success")
                return redirect(url_for('login'))
            except Exception as e:
                flash(f"Database error: {str(e)}", "danger")

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        shop_name = request.form.get('shop_name', '').strip()
        user_role = request.form.get('user_role')
        department = request.form.get('department', 'Groceries & Staples')
        admin_passcode = request.form.get('admin_passcode', '')
        
        if not shop_name:
            flash("Store / Mart Name is required.", "warning")
            return render_template('login.html', departments=DEPARTMENT_LIST)
            
        # Security Check: Verify store-specific admin passcode from Database
        if user_role == 'Store / Mart Admin':
            upper_shop_name = shop_name.upper()
            
            if db:
                store_account = db.get_store_account(upper_shop_name)
                
                if store_account:
                    # Check if the typed password matches the encrypted database password
                    if not check_password_hash(store_account['password_hash'], admin_passcode):
                        flash("Unauthorized: Invalid Admin Security Passcode!", "danger")
                        return render_template('login.html', departments=DEPARTMENT_LIST)
                else:
                    # Fallback for old stores in config.py
                    valid_passcode = getattr(config, 'ADMIN_PASSWORDS', {}).get(upper_shop_name)
                    if not valid_passcode or admin_passcode != valid_passcode:
                        flash("Store not found or Invalid Passcode! Please register your store first.", "danger")
                        return render_template('login.html', departments=DEPARTMENT_LIST)

        session['logged_in'] = True
        session['shop_name'] = shop_name
        session['user_role'] = user_role
        session['department'] = department if user_role == 'Department Staff' else 'All Sections'
        return redirect(url_for('index'))
            
    return render_template('login.html', departments=DEPARTMENT_LIST)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/add', methods=['POST'])
def add_item():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    shop_name = session.get('shop_name')
    user_role = session.get('user_role')
    
    if user_role != 'Department Staff':
        flash("Admin restriction: Item registration is managed by department staff.", "warning")
        return redirect(url_for('index'))
        
    user_dept = session.get('department', 'Groceries & Staples')
    item_name = request.form.get('item_name')
    quantity = int(request.form.get('quantity', 0))
    unit = request.form.get('unit', 'Units')
    unit_price = float(request.form.get('unit_price', 0.0))
    supplier = request.form.get('supplier', 'Direct Vendor')
    
    if item_name and db:
        clean_name_id = item_name.strip().upper().replace(' ', '_')
        item_id = f"{shop_name.upper().replace(' ', '-')}__{user_dept.upper().replace(' ', '_')}__{clean_name_id}"
        
        item_payload = {
            'item_id': item_id,
            'ShopID': shop_name,
            'shop_name': shop_name,
            'department': user_dept,
            'item_name': item_name.strip(),
            'category': 'General',
            'quantity': quantity,
            'unit': unit,
            'unit_price': unit_price,
            'supplier': supplier,
            'last_updated': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        
        try:
            db.add_item(item_payload)
            flash(f"Successfully added {item_name} under {user_dept}!", "success")
        except Exception as e:
            flash(f"Error adding item to database: {str(e)}", "danger")
            
    return redirect(url_for('index'))

@app.route('/delete/<path:item_id>', methods=['POST'])
def delete_item(item_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    user_role = session.get('user_role')
    current_dept = session.get('department') if user_role == 'Department Staff' else request.args.get('dept', 'All Sections')
    
    try:
        if db:
            db.delete_item(item_id)
            flash("Item deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting item: {str(e)}", "danger")
        
    if user_role == 'Department Staff':
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index', dept=current_dept))

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)