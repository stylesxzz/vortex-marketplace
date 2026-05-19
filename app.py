from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import sqlite3
import hashlib
import requests
import os
from database import get_connection, init_db
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Inicializar banco de dados
init_db()

# Credenciais do Admin Exclusivo
ADMIN_USERNAME = "stylesxz"
ADMIN_WALLET = "bc1qahd3xa7uzl5u86k80twckyvn5j8gyye62atvvr"

def obfuscate_username(username):
    if len(username) <= 3:
        return username[0] + "*" * (len(username) - 1)
    return username[:3] + "*" * (len(username) - 3)

def get_admin_password_hash():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'admin_pwd_hash'")
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def set_admin_password(password):
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('admin_pwd_hash', ?)", (pwd_hash,))
    conn.commit()
    conn.close()

def get_admin_wallet():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'admin_wallet'")
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else "WALLET_NOT_CONFIGURED"

def set_admin_wallet(new_wallet):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = 'admin_wallet'", (new_wallet,))
    conn.commit()
    conn.close()

def verify_blockchain_tx(txid, target_wallet, expected_amount):
    try:
        response = requests.get(f"https://blockchain.info/rawtx/{txid}", timeout=5)
        if response.status_code != 200:
            return False
        
        data = response.json()
        expected_sats = int(expected_amount * 100000000)
        
        for out in data.get('out', []):
            if out.get('addr') == target_wallet:
                if abs(out.get('value', 0) - expected_sats) < 1000:
                    return True
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and 'user_id' not in request.args:
            return redirect(url_for('welcome'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def welcome():
    if 'user_id' in session:
        return redirect(url_for('main_menu'))
    
    # Verificar se é a primeira execução
    if not get_admin_password_hash():
        return redirect(url_for('setup_admin'))
    
    return render_template('welcome.html')

@app.route('/setup-admin', methods=['GET', 'POST'])
def setup_admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password:
            set_admin_password(password)
            return redirect(url_for('welcome'))
    return render_template('setup_admin.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar se o usuario esta banido
    cursor.execute("SELECT id FROM banned_users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return render_template('welcome.html', error="This account has been banned")
    
    cursor.execute("SELECT id, username, wallet_address, likes, is_verified FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user[0]
        session['username'] = user[1]
        session['wallet'] = user[2]
        session['is_verified'] = user[4]
        return redirect(url_for('main_menu'))
    else:
        return render_template('welcome.html', error="User not found")

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    wallet = request.form.get('wallet')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar se o usuario ou carteira estao banidos
    cursor.execute("SELECT id FROM banned_users WHERE username = ? OR wallet_address = ?", (username, wallet))
    if cursor.fetchone():
        conn.close()
        return render_template('welcome.html', error="This username or wallet is banned")
    
    try:
        cursor.execute("INSERT INTO users (username, wallet_address) VALUES (?, ?)", (username, wallet))
        conn.commit()
        user_id = cursor.lastrowid
        session['user_id'] = user_id
        session['username'] = username
        session['wallet'] = wallet
        session['is_verified'] = 0
        conn.close()
        return redirect(url_for('main_menu'))
    except sqlite3.IntegrityError:
        conn.close()
        return render_template('welcome.html', error="Username already exists")

@app.route('/guest')
def guest_mode():
    session['user_id'] = None
    session['username'] = 'GUEST'
    return redirect(url_for('main_menu'))

@app.route('/menu')
def main_menu():
    is_guest = session.get('username') == 'GUEST'
    user_info = {
        'username': obfuscate_username(session.get('username', 'GUEST')) if not is_guest else 'GUEST',
        'is_guest': is_guest
    }
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products WHERE is_sold = 0")
    product_count = cursor.fetchone()[0]
    conn.close()
    
    return render_template('menu.html', user=user_info, product_count=product_count)

@app.route('/market')
def market():
    search_query = request.args.get('search', '')
    
    conn = get_connection()
    cursor = conn.cursor()
    if search_query:
        cursor.execute("""
            SELECT p.id, p.name, p.price_btc, u.username, u.likes, u.is_verified 
            FROM products p JOIN users u ON p.seller_id = u.id 
            WHERE p.is_sold = 0 AND (p.name LIKE ? OR p.description LIKE ?)
        """, (f'%{search_query}%', f'%{search_query}%'))
    else:
        cursor.execute("""
            SELECT p.id, p.name, p.price_btc, u.username, u.likes, u.is_verified 
            FROM products p JOIN users u ON p.seller_id = u.id 
            WHERE p.is_sold = 0
        """)
    products = cursor.fetchall()
    conn.close()
    
    products_list = []
    for p in products:
        products_list.append({
            'id': p[0],
            'name': p[1],
            'price': f"{p[2]:.8f}",
            'seller': obfuscate_username(p[3]),
            'seller_id': p[3],
            'likes': p[4],
            'verified': p[5]
        })
    
    return render_template('market.html', products=products_list, search=search_query)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.name, p.description, p.price_btc, p.product_type, p.digital_content, u.id, u.username, u.wallet_address, u.likes, u.is_verified
        FROM products p JOIN users u ON p.seller_id = u.id
        WHERE p.id = ? AND p.is_sold = 0
    """, (product_id,))
    product = cursor.fetchone()
    conn.close()
    
    if not product:
        return redirect(url_for('market'))
    
    is_guest = session.get('username') == 'GUEST'
    product_info = {
        'id': product[0],
        'name': product[1],
        'description': product[2],
        'price': f"{product[3]:.8f}",
        'type': product[4],
        'content': product[5],
        'seller_id': product[6],
        'seller': obfuscate_username(product[7]),
        'seller_wallet': product[8],
        'likes': product[9],
        'verified': product[10],
        'is_guest': is_guest
    }
    
    return render_template('product.html', product=product_info, admin_wallet=get_admin_wallet())

@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell_product():
    if session.get('username') == 'GUEST':
        return redirect(url_for('welcome'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        product_type = request.form.get('type')
        content = request.form.get('content')
        txid = request.form.get('txid')
        
        admin_wallet = get_admin_wallet()
        fee = price * 0.03
        
        if not verify_blockchain_tx(txid, admin_wallet, fee):
            return render_template('sell.html', error="Transaction verification failed", admin_wallet=admin_wallet)
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (name, description, price_btc, seller_id, product_type, digital_content)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, description, price, session['user_id'], product_type, content))
        conn.commit()
        conn.close()
        
        return redirect(url_for('inventory'))
    
    return render_template('sell.html', admin_wallet=get_admin_wallet())

@app.route('/buy/<int:product_id>', methods=['POST'])
@login_required
def buy_product(product_id):
    if session.get('username') == 'GUEST':
        return redirect(url_for('welcome'))
    
    email = request.form.get('email')
    address = request.form.get('address')
    txid = request.form.get('txid')
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.name, p.price_btc, p.seller_id, p.product_type, p.digital_content, u.wallet_address
        FROM products p JOIN users u ON p.seller_id = u.id
        WHERE p.id = ?
    """, (product_id,))
    product = cursor.fetchone()
    
    if not product:
        conn.close()
        return redirect(url_for('market'))
    
    seller_wallet = product[6]
    price = product[2]
    
    if not verify_blockchain_tx(txid, seller_wallet, price):
        conn.close()
        return render_template('product.html', error="Transaction verification failed")
    
    cursor.execute("""
        INSERT INTO transactions (buyer_id, seller_id, product_id, amount_btc, fee_btc, buyer_email, shipping_address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session['user_id'], product[3], product_id, price, 0, email, address))
    
    cursor.execute("UPDATE products SET is_sold = 1 WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('cart'))

@app.route('/cart')
@login_required
def cart():
    if session.get('username') == 'GUEST':
        return redirect(url_for('welcome'))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.name, t.amount_btc, t.timestamp, p.digital_content
        FROM transactions t JOIN products p ON t.product_id = p.id
        WHERE t.buyer_id = ?
    ''', (session['user_id'],))
    transactions = cursor.fetchall()
    conn.close()
    
    items = []
    for t in transactions:
        items.append({
            'name': t[0],
            'amount': f"{t[1]:.8f}",
            'date': t[2],
            'content': t[3]
        })
    
    return render_template('cart.html', items=items)

@app.route('/inventory')
@login_required
def inventory():
    if session.get('username') == 'GUEST':
        return redirect(url_for('welcome'))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price_btc, is_sold FROM products WHERE seller_id = ?", (session['user_id'],))
    items = cursor.fetchall()
    conn.close()
    
    inventory_items = []
    for i in items:
        inventory_items.append({
            'id': i[0],
            'name': i[1],
            'price': f"{i[2]:.8f}",
            'sold': i[3]
        })
    
    return render_template('inventory.html', items=inventory_items)

@app.route('/profile')
@login_required
def profile():
    if session.get('username') == 'GUEST':
        return redirect(url_for('welcome'))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, wallet_address, likes, is_verified FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    user_info = {
        'username': user[1],
        'wallet': user[2],
        'likes': user[3],
        'verified': user[4]
    }
    
    return render_template('profile.html', user=user_info)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    if session.get('username') == 'GUEST':
        return redirect(url_for('welcome'))
    
    new_username = request.form.get('username')
    new_wallet = request.form.get('wallet')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE users SET username = ?, wallet_address = ? WHERE id = ?", 
                      (new_username, new_wallet, session['user_id']))
        conn.commit()
        session['username'] = new_username
        session['wallet'] = new_wallet
        conn.close()
        return redirect(url_for('profile'))
    except sqlite3.IntegrityError:
        conn.close()
        return render_template('profile.html', error="Username already exists")

@app.route('/chat')
@login_required
def chat():
    if session.get('username') == 'GUEST':
        return redirect(url_for('welcome'))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username, c.message, c.timestamp
        FROM chat_messages c JOIN users u ON c.user_id = u.id
        ORDER BY c.timestamp DESC LIMIT 50
    """)
    messages = cursor.fetchall()
    conn.close()
    
    messages_list = []
    for m in messages:
        messages_list.append({
            'username': obfuscate_username(m[0]),
            'message': m[1],
            'timestamp': m[2]
        })
    
    messages_list.reverse()
    return render_template('chat.html', messages=messages_list)

@app.route('/chat/send', methods=['POST'])
@login_required
def send_chat_message():
    if session.get('username') == 'GUEST':
        return jsonify({'error': 'Must be logged in'}), 403
    
    message = request.form.get('message', '').strip()
    if not message or len(message) > 500:
        return redirect(url_for('chat'))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_messages (user_id, message) VALUES (?, ?)", 
                  (session['user_id'], message))
    conn.commit()
    conn.close()
    
    return redirect(url_for('chat'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    # Verificar se o usuario logado eh o admin exclusivo
    if session.get('username') != ADMIN_USERNAME or session.get('wallet') != ADMIN_WALLET:
        return render_template('admin_login.html', error="Access denied")
    
    if request.method == 'POST':
        password = request.form.get('password')
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if pwd_hash != get_admin_password_hash():
            return render_template('admin_login.html', error="Incorrect password")
        
        session['admin'] = True
        return redirect(url_for('admin_settings'))
    
    return render_template('admin_login.html')

@app.route('/admin-settings')
def admin_settings():
    if session.get('username') != ADMIN_USERNAME or session.get('wallet') != ADMIN_WALLET:
        return redirect(url_for('admin_panel'))
    
    if not session.get('admin'):
        return redirect(url_for('admin_panel'))
    
    current_wallet = get_admin_wallet()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, wallet_address, likes, is_verified FROM users")
    users = cursor.fetchall()
    conn.close()
    
    users_list = []
    for u in users:
        users_list.append({
            'id': u[0],
            'username': u[1],
            'wallet': u[2],
            'likes': u[3],
            'verified': u[4]
        })
    
    return render_template('admin_settings.html', wallet=current_wallet, users=users_list)

@app.route('/api/update-wallet', methods=['POST'])
def update_wallet():
    if session.get('username') != ADMIN_USERNAME or session.get('wallet') != ADMIN_WALLET:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    new_wallet = request.form.get('wallet')
    set_admin_wallet(new_wallet)
    return redirect(url_for('admin_settings'))

@app.route('/api/verify-user/<int:user_id>', methods=['POST'])
def verify_user(user_id):
    if session.get('username') != ADMIN_USERNAME or session.get('wallet') != ADMIN_WALLET:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_verified = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_settings'))

@app.route('/api/ban-user/<int:user_id>', methods=['POST'])
def ban_user(user_id):
    if session.get('username') != ADMIN_USERNAME or session.get('wallet') != ADMIN_WALLET:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Obter informacoes do usuario
    cursor.execute("SELECT username, wallet_address FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user:
        # Adicionar a tabela de banidos
        cursor.execute("INSERT INTO banned_users (username, wallet_address, banned_by) VALUES (?, ?, ?)", 
                      (user[0], user[1], ADMIN_USERNAME))
        # Marcar como banido
        cursor.execute("UPDATE users SET is_banned = 1 WHERE id = ?", (user_id,))
        conn.commit()
    
    conn.close()
    return redirect(url_for('admin_settings'))

@app.route('/like-seller/<int:seller_id>', methods=['POST'])
@login_required
def like_seller(seller_id):
    if session.get('username') == 'GUEST':
        return jsonify({'error': 'Must be logged in'}), 403
    
    if session['user_id'] == seller_id:
        return jsonify({'error': 'You cannot like yourself'}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO user_likes (voter_id, target_id) VALUES (?, ?)", (session['user_id'], seller_id))
        cursor.execute("UPDATE users SET likes = likes + 1 WHERE id = ?", (seller_id,))
        conn.commit()
        conn.close()
        return redirect(request.referrer or url_for('market'))
    except sqlite3.IntegrityError:
        conn.close()
        return redirect(request.referrer or url_for('market'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
