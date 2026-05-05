import os
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# ==========================================
# 1. CONFIGURATION
# ==========================================
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///orders.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'canteen-secret-key')

# Your confirmed staff key
STAFF_API_KEY = os.environ.get('STAFF_KEY', 'canteen123')

db = SQLAlchemy(app)

# ==========================================
# 2. UPDATED MENU DATA
# ==========================================
MENU = [
    # --- Main Items ---
    {"id": "1", "name": "Veg Noodles", "price": 50, "image": "https://images.unsplash.com/photo-1585032226651-759b368d7246?w=500"},
    {"id": "2", "name": "Veg Fried Rice", "price": 50, "image": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=500"},
    {"id": "3", "name": "White Sauce Pasta", "price": 60, "image": "https://images.unsplash.com/photo-1645112481338-3564e161043e?w=500"},
    {"id": "4", "name": "Red Sauce Pasta", "price": 60, "image": "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=500"}, # Fixed Image
    {"id": "5", "name": "Veg Mac & Cheese", "price": 70, "image": "https://images.unsplash.com/photo-1543339308-43e59d6b73a6?w=500"},
    
    # --- Quick Bites ---
    {"id": "6", "name": "Veg Sandwich", "price": 30, "image": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=500"},
    {"id": "7", "name": "Grilled Veg Sandwich", "price": 40, "image": "https://images.unsplash.com/photo-1528736235302-52922df5c122?w=500"},
    {"id": "8", "name": "Veg Burger", "price": 50, "image": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=500"},
    {"id": "9", "name": "Cheese Burger (Veg)", "price": 60, "image": "https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=500"},
    {"id": "10", "name": "Garlic Bread", "price": 30, "image": "https://images.unsplash.com/photo-1619535814932-7989fa2c9daf?w=500"}, # Fixed Image
    
    # --- Sides ---
    {"id": "11", "name": "French Fries (Small)", "price": 40, "image": "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=500"},
    {"id": "12", "name": "Peri Peri Fries", "price": 50, "image": "https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=500"},
    {"id": "13", "name": "Cheese Fries", "price": 60, "image": "https://images.unsplash.com/photo-1585109649139-366815a0d713?w=500"},
    
    # --- Drinks ---
    {"id": "14", "name": "Cold Coffee", "price": 50, "image": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=500"},
    {"id": "15", "name": "Lemonade", "price": 20, "image": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500"},
    {"id": "16", "name": "Iced Tea", "price": 30, "image": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=500"}
]

# ==========================================
# 3. DATABASE MODEL
# ==========================================
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_ref = db.Column(db.String(10), unique=True)
    student_name = db.Column(db.String(100))
    student_class = db.Column(db.String(20))
    items = db.Column(db.String(500))
    total_price = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# ==========================================
# 4. ROUTES
# ==========================================

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('student_name')
        cls = request.form.get('class_section')
        selected_ids = request.form.getlist('items')
        
        chosen = [i for i in MENU if i['id'] in selected_ids]
        total = sum(i['price'] for i in chosen)
        item_names = ", ".join([i['name'] for i in chosen])
        
        ref = f"#{''.join(random.choices(string.ascii_uppercase + string.digits, k=5))}"
        
        new_order = Order(order_ref=ref, student_name=name, student_class=cls, items=item_names, total_price=total)
        db.session.add(new_order)
        db.session.commit()
        
        return redirect(url_for('success', order_ref=ref))
    return render_template('index.html', menu=MENU)

@app.route('/success/<order_ref>')
def success(order_ref):
    order = Order.query.filter_by(order_ref=order_ref).first_or_404()
    return render_template('success.html', order=order)

@app.route('/staff')
def staff_dashboard():
    key = request.args.get('key')
    if key != STAFF_API_KEY:
        return f"Unauthorized: Incorrect Key.", 401
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('staff_dashboard.html', orders=orders)

# ==========================================
# 5. RUN
# ==========================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
