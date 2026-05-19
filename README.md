# VORTEX MARKETPLACE v15 - WEB EDITION

**Secure • Anonymous • Decentralized Bitcoin Marketplace**

```
             ,  ,
             \ \
             ) \ \    _p_
             )^ )\ /  p\
              \  \ \/  /  |
               \  \  \  /   /
                \  \  \/   /
                 \  \    /
                  \  \  /
                   \  \/
                    \ /
                     V
```

## 🚀 Features

- **100% Anonymous**: Access via Tor Hidden Services (.onion)
- **Web-Based Interface**: Modern hacker aesthetic with green neon theme
- **Bitcoin Payments**: TXID verification for all transactions
- **User Roles**: Admin, Seller, Buyer, and Guest modes
- **Product Types**: Support for Digital (auto-delivery) and Physical goods
- **Reputation System**: User likes and verified seller badges
- **Admin Panel**: Secure password-protected marketplace management
- **3% Listing Fee**: Automatic fee collection from sellers
- **Privacy First**: Username obfuscation to prevent account hijacking

## 📋 Requirements

- **Python 3.7+**
- **Tor** (for Hidden Service)
- **Flask** (installed automatically)
- **Linux/Termux** environment

## 🔧 Installation

### 1. Download and Extract

```bash
# Download the Vortex v15 Web package
unzip vortex_v15_web.zip
cd vortex_v15_web
```

### 2. Install Dependencies

```bash
# Python dependencies (Flask, Requests)
pip3 install flask requests

# Tor (if not already installed)
sudo apt install tor  # Debian/Ubuntu
# or
pkg install tor       # Termux
```

### 3. Quick Start

```bash
# Make the launcher executable
chmod +x start_vortex.sh

# Run the marketplace
./start_vortex.sh
```

The script will:
1. ✅ Check all dependencies
2. ✅ Configure Tor Hidden Service
3. ✅ Generate your `.onion` address
4. ✅ Initialize the database
5. ✅ Start the Flask web server
6. ✅ Display your access URL

## 🌐 Accessing the Marketplace

### Via Tor Browser (Recommended)

1. **Download Tor Browser** from [torproject.org](https://www.torproject.org/download/)
2. **Open Tor Browser**
3. **Navigate to** the `.onion` address displayed in the terminal
4. **Create an account** or login

### Local Testing (Development)

```
http://127.0.0.1:5000
```

## 👤 User Roles

### Guest Mode
- Browse products
- View seller information
- **Cannot**: Buy, sell, or like

### Buyer
- Browse and purchase products
- Like sellers
- View purchase history
- **Cannot**: List products without selling

### Seller
- Create product listings (3% fee required)
- Manage inventory
- Receive Bitcoin payments
- Build reputation through likes

### Admin
- Manage marketplace settings
- Update admin wallet address
- Verify trusted sellers
- Change admin password
- **Protected**: Password-required access

## 💰 Payment System

### Listing a Product

1. Click **"Create Listing"**
2. Enter product details
3. Set price in BTC
4. Send **3% listing fee** to admin wallet
5. Paste transaction TXID to verify
6. Product goes live!

### Buying a Product

1. Browse the **Market**
2. Click on a product
3. Send payment to seller's wallet
4. Paste transaction TXID
5. For digital products: Instant access
6. For physical products: Provide shipping address

## 🔐 Security Features

### Admin Password Protection

On first run, you'll set an admin password. This password:
- Is hashed with SHA-256
- Protects the admin panel
- Can be changed anytime
- Is stored securely in the database

### Tor Hidden Service

- Your marketplace runs as a `.onion` service
- All traffic is encrypted through Tor
- No IP address exposure
- Accessible only through Tor Browser

### Username Obfuscation

- Usernames are partially hidden (e.g., `Vor***`)
- Prevents account hijacking
- Maintains seller reputation

## 📁 Project Structure

```
vortex_v15_web/
├── app.py                 # Flask application logic
├── database.py            # SQLite database management
├── start_vortex.sh        # Tor + Flask launcher
├── README.md              # This file
├── templates/             # HTML templates
│   ├── base.html
│   ├── welcome.html
│   ├── menu.html
│   ├── market.html
│   ├── product.html
│   ├── sell.html
│   ├── cart.html
│   ├── inventory.html
│   ├── admin_login.html
│   ├── admin_settings.html
│   └── setup_admin.html
├── static/
│   └── css/
│       └── style.css      # Hacker theme styling
└── marketplace.db         # SQLite database (created on first run)
```

## 🎨 Customization

### Change Admin Wallet

1. Login to **Admin Panel**
2. Enter your admin password
3. Update the wallet address
4. Save changes

### Verify Sellers

1. Go to **Admin Settings**
2. Find the seller you want to verify
3. Click **"VERIFY"**
4. They'll get a **[✓ VERIFIED]** badge

### Change Admin Password

1. Access **Admin Settings**
2. Look for password change option
3. Set a new strong password

## 🛠️ Troubleshooting

### Tor not starting?

```bash
# Check if Tor is already running
ps aux | grep tor

# Kill any existing Tor processes
pkill -f tor

# Try starting again
./start_vortex.sh
```

### Port already in use?

Edit `app.py` and change:
```python
app.run(host='127.0.0.1', port=5001)  # Change 5000 to another port
```

### Database errors?

```bash
# Remove the old database
rm marketplace.db

# Run the script again (it will recreate it)
./start_vortex.sh
```

### Flask not starting?

```bash
# Install dependencies manually
pip3 install flask requests

# Run Flask directly for debugging
python3 app.py
```

## 📝 First-Time Setup Checklist

- [ ] Install Python 3 and Tor
- [ ] Extract the Vortex package
- [ ] Run `./start_vortex.sh`
- [ ] Set your admin password
- [ ] Note your `.onion` address
- [ ] Open Tor Browser
- [ ] Navigate to your `.onion` address
- [ ] Create your seller account
- [ ] Set your admin wallet address
- [ ] Create your first product listing

## 🔒 Important Security Notes

1. **Backup your database**: `marketplace.db` contains all user and transaction data
2. **Encrypt sensitive files**: Use GPG to encrypt your database before uploading
3. **Strong passwords**: Use complex admin passwords (mix of letters, numbers, symbols)
4. **Keep Tor updated**: Regularly update Tor for security patches
5. **Monitor logs**: Check for suspicious activity in transaction history

## 📞 Support & Troubleshooting

For issues or questions:

1. Check the **Troubleshooting** section above
2. Review Flask error messages in the terminal
3. Ensure Tor is running: `ps aux | grep tor`
4. Verify Python version: `python3 --version`
5. Test local access first: `http://127.0.0.1:5000`

## 📜 License

This software is provided as-is for educational and legitimate purposes only.

## ⚡ Version History

- **v15 Web** - Web interface with Tor Hidden Service
- **v14 Pro** - Terminal-based CLI version
- **v13** - Initial Bitcoin integration
- **v12** - User reputation system
- **v11** - Admin panel security

---

**VORTEX MARKETPLACE v15 - Secure • Anonymous • Decentralized**

```
⚡ Secure Gateway ⚡
100% Anonymous
Bitcoin Powered
```
