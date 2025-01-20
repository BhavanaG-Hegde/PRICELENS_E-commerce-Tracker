from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from top_deals_scraper import top_deals 
from scrape_amazon import scrape_amazon
from scrape_amazon_update import scrape_amazon_update # Import the scraper function
import sqlite3
import asyncio
import time
import datetime
from urllib.parse import unquote
from flask import jsonify, request
import logging
from flask import jsonify, session

app = Flask(__name__)
app.secret_key = 'web_scraper'
database="web_scraper.db"

def setup_database():
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products2(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            name TEXT,
            price TEXT,
            link TEXT,
            image_url TEXT,
            bestseller_tag TEXT
        )
    """)

    #Table to store tracked products
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tracked_products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        name TEXT,
        price TEXT,
        link TEXT ,
        image_url TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_email) REFERENCES users(email),
        UNIQUE(user_email,link)
    )
""")
    
    #table for price history
    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    product_link TEXT NOT NULL ,
    price DECIMAL(10, 2) NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_email, product_link) REFERENCES tracked_products(user_email,link) ON DELETE CASCADE
    )""" )
    conn.commit()
    return conn

def store_data(conn, query, products):
    """Store product data into the database."""
    if not products:
        print("No products to store.")
        return

    cursor = conn.cursor()
    for product in products:
        cursor.execute("""
            INSERT INTO products2 (query, name, price, link, image_url, bestseller_tag) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (query, product["name"], product["price"], product["link"], product["image_url"], product["bestseller_tag"]))
    conn.commit()
    print(f"Stored {len(products)} products into the database.")

# Database connection function
def get_db_connection():
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

# Create users table if it doesn't exist
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()

# Home page
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')  # Render the main HTML page

# # Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the email and password match any user in the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT name, email FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = user[0]  # Store the username in session
            session['email'] = user[1]    # Store the email in session
            flash('Login successful!', 'success')
            time.sleep(1)
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')


# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the email already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Email already exists! Please use a different email.', 'error')
            conn.close()
            return redirect(url_for('login'))

        # Insert the new user into the database
        try:
            cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', 
                           (name, email, password))
            conn.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        except sqlite3.Error as e:
            flash(f'An error occurred: {e}', 'error')
            return redirect(url_for('login'))
        finally:
            conn.close()

    return render_template('login.html')

@app.route('/templates/home')
def home():
    if 'username' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('index'))
    return render_template('home.html', username=session['username'])

@app.route('/logout')
def logout():
    # Clear session data
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))  # Redirect to login page or home

# API Route for Top Deals
@app.route('/api/top-deals')
def api_top_deals():
    # Call the scraper function
    conn=setup_database()
    print("connection successful")
    products = top_deals(max_products=15)
    print("storing")
    store_data(conn, query="best deals of the day", products=products)
    return jsonify(products)
conn.close()

@app.route('/api/scraped-products', methods=['GET'])
async def get_scraped_products():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    try:
        products = await scrape_amazon(query)
       # print('Scraped products:', products)   # Scrape up to 10 products
        return jsonify(products)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to add products to tracked list
@app.route('/api/add-to-track', methods=['POST'])
def add_to_track():
    if 'email' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    user_email = session['email']
    data = request.json

    if not all(key in data for key in ['name', 'price', 'link', 'image_url']):
        return jsonify({'error': 'Invalid product data'}), 400

    try:
        user_email = session['email']
        try:
            price = float(data['price'].replace(',', ''))
        except ValueError:
            return jsonify({'error': 'Invalid price format'}), 400
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert product into tracked_products
        cursor.execute("""
            INSERT INTO tracked_products (user_email, name, price, link, image_url)
            VALUES (?, ?, ?, ?, ?)
        """, (user_email, data['name'], data['price'], data['link'], data['image_url']))
        conn.commit()

        cursor.execute("SELECT id FROM tracked_products WHERE link = ?", (data['link'],))
        product = cursor.fetchone()

        if product:
            # Insert into price_history only if the product exists
            cursor.execute("""
                INSERT INTO price_history (user_email,product_link, price)
                VALUES (?,?,?)
            """, (user_email,data['link'], price))
            conn.commit()

            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Product not found in tracked_products'}), 400

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# Route to view tracked products
@app.route('/tracked-products')
def tracked_products():
    if 'email' not in session:
        flash('Please log in to view your tracked products.', 'warning')
        return redirect(url_for('login'))
    user_email = session['email']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Fetch tracked products for the user using email
        cursor.execute("""
            SELECT name, price, link, image_url, timestamp
            FROM tracked_products
            WHERE user_email = ?
            ORDER BY timestamp DESC
        """, (user_email,))
        tracked_items = cursor.fetchall()
        tracked_items = [dict(row) for row in tracked_items]
        return render_template('tracked_products.html', products=tracked_items)
    finally:
        conn.close()
 
@app.route('/delete_product', methods=['POST'])
def delete_product():
    try:
        # Get the tracked_product_image_url from the POST request JSON body
        user_email=session['email']
        data = request.get_json()
        print("Request data:", data)
        tracked_product_image_url = data.get('tracked_product_image_url')

        if not tracked_product_image_url:
            return jsonify({"error": "Image URL is missing"}), 400
        # Connect to the database and delete the tracked product by image_url
        conn = sqlite3.connect('web_scraper.db')
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("SELECT link FROM tracked_products WHERE image_url = ?", (tracked_product_image_url,))
        product = cursor.fetchone()
        print("Fetched product:", product)

        if not product:
            return jsonify({"error": "Product not found"}), 404
        product_link = product[0]

        # Delete the product from tracked_products (cascading deletes from price_history)
        cursor.execute("DELETE FROM tracked_products WHERE link = ? and user_email=?", (product_link,user_email))
        conn.commit()
        return jsonify({"success": True, "message": "Product deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/price-history/<path:product_link>', methods=['GET'])
def price_history(product_link):
    print(f"Received encoded product_link: {product_link}")  # Debug log for incoming link
   # product_link = unquote(product_link)
    print(f"Decoded product_link: {product_link}")  # Debug log for decoded link
    if 'email' not in session:
        print("User not logged in")  # Debug log for unauthenticated access
        return jsonify({'error': 'User not logged in'}), 401

    user_email = session['email']
    print(f"User email: {user_email}")  # Debug log for session email

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Verify the product belongs to the user
        cursor.execute("""
            SELECT COUNT(*) FROM tracked_products
            WHERE link = ? AND user_email = ?
        """, (product_link, user_email))
        product_count = cursor.fetchone()[0]
        print(f"Product count for user: {product_count}")  # Debug log for product count

        if product_count == 0:
            print("Unauthorized or non-existent product")  # Debug log for unauthorized access
            return jsonify({'error': 'Unauthorized or non-existent product'}), 403
        # Fetch price history
        cursor.execute("""
            SELECT price, date FROM price_history
            WHERE product_link = ? and user_email=?
            ORDER BY date ASC
        """, (product_link,user_email))
        price_history = cursor.fetchall()
        print(f"Price history fetched: {price_history}")  # Debug log for fetched price history

        if not price_history:
            print("No price history found for the product.")  # Debug log for empty history
            return jsonify([])

        result = [{'price': float(price), 'date': date} for price, date in price_history]
        print(f"Formatted result: {result}")  # Debug log for final result
        return jsonify(result)

    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Debug log for exceptions
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/refresh-prices', methods=['POST'])
async def refresh_prices():
    if 'email' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    user_email = session['email']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch all tracked products for the current user
        cursor.execute("""
            SELECT id, link, price FROM tracked_products
            WHERE user_email = ?
        """, (user_email,))
        tracked_products = cursor.fetchall()


        updated_products = []
        for product in tracked_products:
            product_id, product_link, current_price = product
            new_price = await scrape_amazon_update(product_link)
            if not new_price or not new_price.replace(',', '').replace('.', '').isdigit():
                new_price=float(current_price.replace(',', ''))
            else:
                new_price=float(new_price.replace(',', ''))
            if str(new_price) != str(current_price):  # Compare as strings since current_price is TEXT
                # Update `tracked_products` with the new price
                cursor.execute("""
                    UPDATE tracked_products
                    SET price = ?
                    WHERE id = ?
                """, (new_price, product_id))

                # Add the new price to the `price_history` table
            cursor.execute("""
                INSERT INTO price_history (user_email,product_link, price)
                VALUES (?,?, ?)
            """, (user_email,product_link, new_price))

            updated_products.append({'product_link': product_link, 'new_price': new_price})

        conn.commit()
        return jsonify({'message': 'Prices refreshed', 'updated_products': updated_products})

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({'error': str(e)}), 500

    finally:
        conn.close()

if __name__ == "__main__":
   app.run(debug=True)
