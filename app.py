from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from bson import ObjectId
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = 'agaaya182822yhhanaiAGUB9'

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['LMS']
collection = db['users']
books_collection = db['books']
users_collection = db['users']


# Home route
@app.route('/')
def home():
    return render_template('home.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        query = {"username": email, "password": password}
        user = collection.find_one(query)

        if user:
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['role'] = user['role']

            # Redirect based on role
            if user['role'] == 'admin':
                return redirect(url_for('admin_page'))
            else:
                return redirect(url_for('user_page'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate inputs
        if not username or not password or not confirm_password:
            flash('All fields are required', 'danger')
            return redirect(url_for('signup'))
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('signup'))

        # Check for duplicates
        if collection.find_one({"username": username}):
            flash('Username already exists. Please choose another.', 'danger')
            return redirect(url_for('signup'))

        # Insert new user into the database
        new_user = {
            "username": username,
            "password": password,
            "role": "user"  # Default role for new users
        }
        collection.insert_one(new_user)
        flash('Signup successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

# User page route
@app.route('/user_page')
def user_page():
    if 'role' in session and session['role'] == 'user':
        return render_template('user.html', username=session['username'])
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('home'))

# # Admin page route
# @app.route('/admin_page')
# def admin_page():
#     if 'role' in session and session['role'] == 'admin':
#         return render_template('admin.html', username=session['username'])
#     else:
#         flash('Access Denied', 'danger')
#         return redirect(url_for('home'))

# Admin page route to display all books
 

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))
 

# Admin page route to display all books
@app.route('/admin_page')
def admin_page():
    if 'role' in session and session['role'] == 'admin':
        books = list(books_collection.find())  # Fetch all books
        return render_template('admin.html', books=books)
    else:
        flash('Access Denied', 'danger')
        return redirect(url_for('home'))
 


# Route to display user's dashboard and borrowed books
@app.route('/user_dashboard')
def user_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('login'))

    # Find the user from the database
    user = users_collection.find_one({"_id": ObjectId(user_id)})

    if user:
        # Fetch borrowed books for the user
        borrowed_books = books_collection.find({"borrowedBy": ObjectId(user_id)})
        return render_template('user_dashboard.html', borrowed_books=borrowed_books)

    flash("User not found.", "danger")
    return redirect(url_for('login'))


 
@app.route('/view_book/<book_id>')
def view_book(book_id):
    book = books_collection.find_one({"_id": ObjectId(book_id)})
    if book:
        price_history = book.get('priceHistory', [])
        quantity_history = book.get('quantityHistory', [])
        
        # Create a graph for price history
        fig1, ax1 = plt.subplots()
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Price', color='tab:blue')
        ax1.plot(price_history, color='tab:blue', label='Price')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        fig1.tight_layout()

        # Convert price history plot to PNG image and encode as base64
        img_price = io.BytesIO()
        plt.savefig(img_price, format='png')
        img_price.seek(0)
        img_base64_price = base64.b64encode(img_price.getvalue()).decode('utf-8')
        plt.close(fig1)

        # Create a graph for quantity history
        fig2, ax2 = plt.subplots()
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Quantity', color='tab:green')
        ax2.plot(quantity_history, color='tab:green', label='Quantity')
        ax2.tick_params(axis='y', labelcolor='tab:green')
        fig2.tight_layout()

        # Convert quantity history plot to PNG image and encode as base64
        img_quantity = io.BytesIO()
        plt.savefig(img_quantity, format='png')
        img_quantity.seek(0)
        img_base64_quantity = base64.b64encode(img_quantity.getvalue()).decode('utf-8')
        plt.close(fig2)

        return render_template('view_book.html', book=book, img_base64_price=img_base64_price, img_base64_quantity=img_base64_quantity)
    else:
        flash('Book not found', 'danger')
        return redirect(url_for('admin_page'))
# Route to delete a book
@app.route('/delete_book/<book_id>', methods=['POST'])
def delete_book(book_id):
    books_collection.delete_one({"_id": ObjectId(book_id)})
    flash('Book deleted successfully', 'success')
    return redirect(url_for('admin_page'))


# Route to edit book details
@app.route('/edit_book/<book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = books_collection.find_one({"_id": ObjectId(book_id)})
    if not book:
        flash('Book not found', 'danger')
        return redirect(url_for('admin_page'))

    if request.method == 'POST':
        name = request.form['name']
        isbn = request.form['isbn']
        category = request.form['category']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])

        # Update the book in the database
        books_collection.update_one(
            {"_id": ObjectId(book_id)},
            {"$set": {
                "name": name,
                "isbn": isbn,
                "category": category,
                "price": price,
                "quantity": quantity
            }}
        )
        flash('Book updated successfully', 'success')
        return redirect(url_for('admin_page'))

    return render_template('edit_book.html', book=book)


# Route to add a new book
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        name = request.form['name']
        isbn = request.form['isbn']
        category = request.form['category']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        
        # Insert the new book into the database
        new_book = {
            "name": name,
            "isbn": isbn,
            "category": category,
            "price": price,
            "quantity": quantity,
            "borrowedBy": [],
            "priceHistory": [],
            "quantityHistory": []
        }
        books_collection.insert_one(new_book)
        flash('Book added successfully', 'success')
        return redirect(url_for('admin_page'))

    return render_template('add_book.html')

# Display all books for users
@app.route('/user_books')
def user_books():
    # Retrieve all books from the database
    books = books_collection.find()

    return render_template('user_books.html', books=books)

# Route to display user's borrowed books
 

# Borrow a book
@app.route('/borrow_book/<book_id>', methods=['POST'])
def borrow_book(book_id):
    user_id = session['user_id']  # Get the user ID from session
    
    # Find the book by its ID
    book = books_collection.find_one({"_id": ObjectId(book_id)})
    
    if book and book['quantity'] > 0:
        # Decrease the quantity of the book
        new_quantity = book['quantity'] - 1
        
        # Update the book in the database
        books_collection.update_one({"_id": ObjectId(book_id)}, {"$set": {"quantity": new_quantity}})
        
        # Add this book to the user's borrowed books list
        users_collection.update_one(
            {"_id": ObjectId(user_id)}, 
            {"$push": {"borrowedBooks": {"bookId": book['_id'], "name": book['name']}}}
        )
        
        flash(f"You have successfully borrowed {book['name']}.", "success")
    else:
        flash("Sorry, this book is out of stock.", "danger")
    
    return redirect(url_for('user_books'))

# Display borrowed books for the user
@app.route('/my_borrowed_books')
def my_borrowed_books():
    user_id = session['user_id']
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    borrowed_books = user.get('borrowedBooks', [])
    
    return render_template('my_borrowed_books.html', borrowed_books=borrowed_books)

# Return a borrowed book
@app.route('/return_book/<book_id>', methods=['POST'])
def return_book(book_id):
    user_id = session['user_id']  # Get the user ID from session

    # Find the book in the borrowed books list
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    borrowed_books = user.get('borrowedBooks', [])
    
    book_to_return = None
    for book in borrowed_books:
        if str(book['bookId']) == book_id:
            book_to_return = book
            break

    if book_to_return:
        # Remove the book from the user's borrowed books list
        users_collection.update_one(
            {"_id": ObjectId(user_id)}, 
            {"$pull": {"borrowedBooks": {"bookId": ObjectId(book_id)}}}
        )

        # Increase the book's quantity in the inventory
        book = books_collection.find_one({"_id": ObjectId(book_id)})
        new_quantity = book['quantity'] + 1
        books_collection.update_one({"_id": ObjectId(book_id)}, {"$set": {"quantity": new_quantity}})
        
        flash(f"You have successfully returned {book['name']}.", "success")
    else:
        flash("You haven't borrowed this book.", "danger")

    return redirect(url_for('my_borrowed_books'))



if __name__ == '__main__':
    app.run(debug=True)
