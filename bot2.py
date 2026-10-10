import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'super_secret_key_ecommerce'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            image TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Новый'
        )
    ''')
    product_count = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    if product_count == 0:
        conn.execute(
            'INSERT INTO products (title, price, description, image) VALUES (?, ?, ?, ?)',
            ('Смартфон Changan Pro', 15000, 'Мощный смартфон с отличной камерой и ярким экраном.', 'https://via.placeholder.com/300')
        )
        conn.execute(
            'INSERT INTO products (title, price, description, image) VALUES (?, ?, ?, ?)',
            ('Беспроводные наушники', 2500, 'Чистый звук и долгая работа без подзарядки.', 'https://via.placeholder.com/300')
        )
        conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = {}
    cart = session['cart']
    
    str_id = str(product_id)
    if str_id in cart:
        cart[str_id] += 1
    else:
        cart[str_id] = 1
        
    session.modified = True
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    if 'cart' not in session or not session['cart']:
        return render_template('cart.html', items=[], total=0)
    
    conn = get_db_connection()
    cart_items = []
    total = 0
    
    for product_id, quantity in session['cart'].items():
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if product:
            item_total = product['price'] * quantity
            total += item_total
            cart_items.append({
                'id': product['id'],
                'title': product['title'],
                'price': product['price'],
                'quantity': quantity,
                'item_total': item_total,
                'image': product['image']
            })
    conn.close()
    return render_template('cart.html', items=cart_items, total=total)

@app.route('/checkout', methods=['POST'])
def checkout():
    name = request.form.get('name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    
    if 'cart' not in session or not session['cart']:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    total = 0
    for product_id, quantity in session['cart'].items():
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if product:
            total += product['price'] * quantity
            
    conn.execute(
        'INSERT INTO orders (customer_name, phone, address, total) VALUES (?, ?, ?, ?)',
        (name, phone, address, total)
    )
    conn.commit()
    conn.close()
    session.pop('cart', None)
    
    return render_template('order_success.html', name=name, address=address)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = get_db_connection()
    if request.method == 'POST':
        title = request.form.get('title')
        price = request.form.get('price')
        description = request.form.get('description')
        image = request.form.get('image', 'https://via.placeholder.com/300')
        
        if title and price:
            conn.execute(
                'INSERT INTO products (title, price, description, image) VALUES (?, ?, ?, ?)',
                (title, float(price), description, image)
            )
            conn.commit()
        return redirect(url_for('admin'))
        
    products = conn.execute('SELECT * FROM products').fetchall()
    orders = conn.execute('SELECT * FROM orders').fetchall()
    conn.close()
    return render_template('admin.html', products=products, orders=orders)

if __name__ == '__main__':
    app.run(debug=True)
