import os
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# ==============================
# CONFIGURATION
# ==============================
# Use separate DB for production vs local
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///orders.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-prod')

# Staff Security Key (Set this in Render Environment Variables)
STAFF_API_KEY = os.environ.get('STAFF_KEY', 'admin_secret_123') 

db = SQLAlchemy(app)

# ==============================
# MENU DATA Configuration
# ==============================
MENU = [
    {
        "id": "1",
        "name": "Veg Grilled Sandwich",
        "price": 40,
        "image": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=500&q=80"
    },
    {
        "id": "2",
        "name": "Spicy Chicken Burger",
        "price": 80,
        "image": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=500&q=80"
    },
    {
        "id": "3",
        "name": "Fresh Orange Juice",
        "price": 50,
        "image": "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?auto=format&fit=crop&w=500&q=80"
    },
    {
        "id": "4",
        "name": "Red Sauce Pasta",
        "price": 90,
        "image": "https://images.unsplash.com/photo-1551183053-bf91b1dca103?auto=format&fit=crop&w=500&q=80"
    },
    {
        "id": "5",
        "name": "Chocolate Brownie",
        "price": 60,
        "image": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=500&q=80"
    },
    {
        "id": "6",
        "name": "Veg Momos (8pcs)",
        "price": 70,
        "image": "https://images.unsplash.com/photo-1626074353765-517a681e40be?auto=format&fit=crop&w=500&q=80"
    }
]

# ==============================
# DATABASE MODEL
# ==============================
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_ref = db.Column(db.String(10), unique=True, nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    student_class = db.Column(db.String(20), nullable=False)
    items = db.Column(db.String(500), nullable=False) # Stored as text "Burger, Juice"
    total_price = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "order_ref": self.order_ref,
            "student": self.student_name,
            "class": self.student_class,
            "items": self.items,
            "total": self.total_price,
            "time": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

# Initialize DB
with app.app_context():
    db.create_all()

# ==============================
# ROUTES
# ==============================

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('student_name')
        class_section = request.form.get('class_section')
        selected_item_ids = request.form.getlist('items')
        
        if not name or not class_section or not selected_item_ids:
            return render_template('index.html', menu=MENU, error="Please fill all fields and select items.")

        # Calculate Logic
        selected_items_names = []
        total_price = 0
        
        for item_id in selected_item_ids:
            # Find item in MENU list
            menu_item = next((item for item in MENU if item["id"] == item_id), None)
            if menu_item:
                selected_items_names.append(menu_item["name"])
                total_price += menu_item["price"]

        # Generate Unique Order ID (e.g., #ORD-X9Z)
        order_ref = f"#{''.join(random.choices(string.ascii_uppercase + string.digits, k=5))}"

        # Save to DB
        new_order = Order(
            order_ref=order_ref,
            student_name=name,
            student_class=class_section,
            items=", ".join(selected_items_names),
            total_price=total_price
        )
        db.session.add(new_order)
        db.session.commit()

        return redirect(url_for('success', order_ref=order_ref))

    return render_template('index.html', menu=MENU)

@app.route('/success/<order_ref>')
def success(order_ref):
    order = Order.query.filter_by(order_ref=order_ref).first_or_404()
    return render_template('success.html', order=order)

# ==============================
# STAFF API (SECURE)
# ==============================
@app.route('/api/orders', methods=['GET'])
def get_orders():
    # Security Check
    key = request.args.get('key')
    if not key or key != STAFF_API_KEY:
        return jsonify({"error": "Unauthorized Access", "message": "Invalid or missing Staff Key"}), 401

    # Fetch orders newest first
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify([order.to_dict() for order in orders])

if __name__ == '__main__':
    # Use PORT env variable for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    @app.route('/staff')
def staff_dashboard():
    # This checks for the secret key in the URL
    key = request.args.get('key')
    if key != STAFF_API_KEY:
        return "Unauthorized: Please provide the correct ?key= in the URL", 401
    
    # This grabs all orders from the database, newest first
    orders = Order.query.order_by(Order.created_at.desc()).all()
    
    # This sends orders to the new page we are about to create
    return render_template('staff_dashboard.html', orders=orders)
