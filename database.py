import sqlite3
import os

def get_connection():
    """Retorna uma conexão com o banco de dados usando caminho relativo."""
    db_path = os.path.join(os.path.dirname(__file__), "marketplace.db")
    return sqlite3.connect(db_path)

def init_db():
    """Cria as tabelas do banco de dados se elas não existirem."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de usuarios (Adicionado likes e is_verified)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        wallet_address TEXT NOT NULL,
        likes INTEGER DEFAULT 0,
        is_verified INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0
    )
    ''')

    # Tabela de produtos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price_btc REAL NOT NULL,
        seller_id INTEGER NOT NULL,
        is_sold BOOLEAN DEFAULT 0,
        product_type TEXT DEFAULT 'fisico',
        image_link TEXT,
        digital_content TEXT,
        fee_payer TEXT DEFAULT 'vendedor',
        FOREIGN KEY (seller_id) REFERENCES users (id)
    )
    ''')

    # Tabela de transacoes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        buyer_id INTEGER NOT NULL,
        seller_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        amount_btc REAL NOT NULL,
        fee_btc REAL NOT NULL,
        buyer_email TEXT,
        shipping_address TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (buyer_id) REFERENCES users (id),
        FOREIGN KEY (seller_id) REFERENCES users (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')

    # Tabela de configuracoes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    
    # Tabela para registrar quem ja deu like em quem (evitar spam)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        voter_id INTEGER,
        target_id INTEGER,
        UNIQUE(voter_id, target_id),
        FOREIGN KEY (voter_id) REFERENCES users (id),
        FOREIGN KEY (target_id) REFERENCES users (id)
    )
    ''')
    
    # Tabela de Chat Global
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Tabela de Usuarios Banidos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS banned_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        wallet_address TEXT,
        banned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        banned_by TEXT DEFAULT 'admin'
    )
    ''')
    
    # Inserir carteira padrao do admin se nao existir
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_wallet', 'SUA_CARTEIRA_AQUI')")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Banco de dados inicializado com sucesso.")
