import os
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# 1. Setup & Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///orders.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')

# This is your staff password
STAFF_API_KEY = os.environ.get('STAFF_KEY', 'admin_secret_123')

db = SQLAlchemy(app)

# 2. The Menu Data
MENU = [
    {"id": "1", "name": "Veg Grilled Sandwich", "price": 40, "image": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=500"},
    {"id": "2", "name": "Spicy Chicken Burger", "price": 80, "image": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500"},
    {"id": "3", "name": "Fresh Orange Juice", "price": 30, "image": "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?w=500"},
    {"id": "4", "name": "Masala Pasta", "price": 90, "image": "https://images.unsplash.com/photo-1551183053-bf91b1dca103?w=500"}
]

# 3. Database Model
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

# 4. Student Routes
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

# 5. Staff Dashboard Route
@app.route('/staff')
def staff_dashboard():
    key = request.args.get('key')
    if key != STAFF_API_KEY:
        return "Unauthorized: Please provide the correct ?key= in the URL", 401
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('staff_dashboard.html', orders=orders)

# 6. Run Block (Must be at the very bottom)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
