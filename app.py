import os, random, string
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- 1. CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///orders.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'canteen-secret-key'
STAFF_API_KEY = os.environ.get('STAFF_KEY', 'canteen123')
db = SQLAlchemy(app)
IST = timezone(timedelta(hours=5, minutes=30))

# --- 2. MENU DATA (Compressed for readability) ---
MENU = [
    {"id": "1", "name": "Veg Noodles", "price": 50, "image": "https://images.unsplash.com/photo-1585032226651-759b368d7246?w=500"},
    {"id": "2", "name": "Veg Fried Rice", "price": 50, "image": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=500"},
    {"id": "3", "name": "White Sauce Pasta", "price": 60, "image": "https://images.unsplash.com/photo-1645112481338-3564e161043e?w=500"},
    {"id": "4", "name": "Red Sauce Pasta", "price": 60, "image": "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=500"},
    {"id": "5", "name": "Veg Mac & Cheese", "price": 70, "image": "https://images.unsplash.com/photo-1543339308-43e59d6b73a6?w=500"},
    {"id": "6", "name": "Veg Sandwich", "price": 30, "image": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=500"},
    {"id": "7", "name": "Grilled Veg Sandwich", "price": 40, "image": "https://images.unsplash.com/photo-1528736235302-52922df5c122?w=500"},
    {"id": "8", "name": "Veg Burger", "price": 50, "image": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=500"},
    {"id": "9", "name": "Cheese Burger", "price": 60, "image": "https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=500"},
    {"id": "10", "name": "Garlic Bread", "price": 30, "image": "https://images.unsplash.com/photo-1619535814932-7989fa2c9daf?w=500"},
    {"id": "11", "name": "French Fries", "price": 40, "image": "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=500"},
    {"id": "12", "name": "Peri Fries", "price": 50, "image": "https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=500"},
    {"id": "13", "name": "Cheese Fries", "price": 60, "image": "https://images.unsplash.com/photo-1585109649139-366815a0d713?w=500"},
    {"id": "14", "name": "Cold Coffee", "price": 50, "image": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=500"},
    {"id": "15", "name": "Lemonade", "price": 20, "image": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500"},
    {"id": "16", "name": "Iced Tea", "price": 30, "image": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=500"}
]

# --- 3. DATABASE TABLE CREATION ---
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_ref = db.Column(db.String(10), unique=True)
    collection_pin = db.Column(db.String(4))
    student_name = db.Column(db.String(100))
    roll_number = db.Column(db.String(20))
    student_class = db.Column(db.String(50))
    items = db.Column(db.String(500))
    total_price = db.Column(db.Integer)
    payment_method = db.Column(db.String(20), default="Cash")
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# --- 4. FUNCTIONS & ROUTES ---
def is_ordering_open():
    return True # Change to False during viva if you want to demonstrate the time lock!
    # Viva logic: 
    # now_ist = datetime.now(IST)
    # if now_ist.hour < 7 or (now_ist.hour == 7 and now_ist.minute < 45): return True
    # return False

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not is_ordering_open():
            return "Ordering is closed. Cutoff is 7:45 AM.", 403
            
        # 1. Get basic details
        name = request.form.get('student_name')
        roll_no = request.form.get('roll_number')
        cls_sec = request.form.get('class_section')
        selected_ids = request.form.getlist('items')
        
        # 2. Calculate Bill using a standard loop (Easy to explain in Viva)
        total = 0
        order_list = []
        
        for item_id in selected_ids:
            qty = int(request.form.get(f'qty_{item_id}', 1))
            for item in MENU: 
                if item['id'] == item_id:
                    total = total + (item['price'] * qty)
                    order_list.append(f"{qty}x {item['name']}")
                    break # Stop searching once item is found
        
        # 3. Generate Random Strings
        ref = "#" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        pin = str(random.randint(1000, 9999))
        
        # 4. Save to Database
        new_order = Order(
            order_ref=ref, collection_pin=pin, student_name=name, roll_number=roll_no, 
            student_class=cls_sec, items=", ".join(order_list), total_price=total
        )
        db.session.add(new_order)
        db.session.commit()
        
        return redirect(url_for('success', order_ref=ref))
        
    return render_template('index.html', menu=MENU, is_open=is_ordering_open())

@app.route('/success/<order_ref>')
def success(order_ref):
    order = Order.query.filter_by(order_ref=order_ref).first_or_404()
    return render_template('success.html', order=order)

@app.route('/staff')
def staff_dashboard():
    if request.args.get('key') != STAFF_API_KEY:
        return "Unauthorized", 401
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    total_orders = len(orders)
    
    # Simple loop to count pending orders
    pending = 0
    for o in orders:
        if o.is_completed == False:
            pending += 1
            
    return render_template('staff_dashboard.html', orders=orders, total=total_orders, pending=pending)

@app.route('/complete/<int:order_id>', methods=['POST'])
def complete_order(order_id):
    if request.args.get('key') != STAFF_API_KEY:
        return "Unauthorized", 401
        
    order = Order.query.get_or_404(order_id)
    order.is_completed = True
    db.session.commit()
    
    return redirect(url_for('staff_dashboard', key=request.args.get('key')))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
