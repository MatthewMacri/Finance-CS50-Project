import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from datetime import datetime, timezone

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Initialize database
def init_db():
    # Create users table
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            hash TEXT NOT NULL,
            cash REAL NOT NULL DEFAULT 10000.00
        )
    """)

    # Create transactions table
    db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            shares INTEGER NOT NULL,
            price REAL NOT NULL,
            transaction_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Create orders table for history
    db.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER, user_id NUMERIC NOT NULL, symbol TEXT NOT NULL, \
                shares NUMERIC NOT NULL, price NUMERIC NOT NULL, timestamp TEXT, PRIMARY KEY(id), \
                FOREIGN KEY(user_id) REFERENCES users(id))")
    db.execute("CREATE INDEX IF NOT EXISTS orders_by_user_id_index ON orders (user_id)")

# Call the init_db function at the start of your application
init_db()

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    owns = own_shares()
    total = 0
    for symbol, shares in owns.items():
        result = lookup(symbol)
        name, price = result["name"], result["price"]
        stock_value = shares * price
        total += stock_value
        owns[symbol] = (name, shares, usd(price), usd(stock_value))
    cash = db.execute("SELECT cash FROM users WHERE id = ? ", session["user_id"])[0]['cash']
    total += cash
    return render_template("index.html", owns=owns, cash=usd(cash), total=usd(total))

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")

        # Validate symbol
        if not symbol or lookup(symbol) is None:
            return apology("invalid symbol", 400)

        # Validate shares
        if not shares.isdigit() or int(shares) <= 0:
            return apology("invalid shares", 400)

        stock = lookup(symbol)
        cost = stock["price"] * int(shares)
        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]

        if cost > user_cash:
            return apology("can't afford", 400)

        # Update user's cash and record the purchase
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", cost, session["user_id"])
        db.execute("""
            INSERT INTO transactions (user_id, symbol, shares, price, transaction_type)
            VALUES (?, ?, ?, ?, 'buy')
        """, session["user_id"], symbol, shares, stock["price"])

        return redirect("/")
    else:
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    rows = db.execute("SELECT symbol, shares, price, timestamp FROM transactions WHERE user_id = ?", session["user_id"])
    return render_template("history.html", rows=rows)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        symbol = request.form.get("symbol")

        # Validate symbol
        if not symbol:
            return apology("must provide symbol", 400)

        stock = lookup(symbol)

        if stock is None:
            return apology("invalid symbol", 400)

        return render_template("quoted.html", stock=stock)

    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Validate input
        if not request.form.get("username"):
            return apology("must provide username", 400)
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match", 400)

        # Hash password
        hash = generate_password_hash(request.form.get("password"))

        # Insert user into database
        try:
            new_user_id = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                                     request.form.get("username"), hash)
        except:
            return apology("username already taken", 400)

        # Log user in
        session["user_id"] = new_user_id
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    owns = own_shares()
    if request.method == "GET":
        return render_template("sell.html", owns=owns.keys())

    symbol = request.form.get("symbol")
    shares = int(request.form.get("shares"))  # Don't forget: convert str to int

    # Validate symbol
    if symbol not in owns:
        return apology("invalid symbol", 400)

    # Validate shares
    if shares <= 0 or owns[symbol] < shares:
        return apology("invalid shares", 400)

    # Execute sell transaction
    result = lookup(symbol)
    user_id = session["user_id"]
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]['cash']
    price = result["price"]
    remain = cash + price * shares

    db.execute("UPDATE users SET cash = ? WHERE id = ?", remain, user_id)
    db.execute("INSERT INTO transactions (user_id, symbol, shares, price, transaction_type) VALUES (?, ?, ?, ?, 'sell')",
               user_id, symbol, -shares, price)

    return redirect("/")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

def own_shares():
    """Helper function: Which stocks the user owns, and numbers of shares owned. Return: dictionary {symbol: qty}"""
    user_id = session["user_id"]
    owns = {}
    query = db.execute("SELECT symbol, shares FROM transactions WHERE user_id = ?", user_id)
    for q in query:
        symbol, shares = q["symbol"], q["shares"]
        owns[symbol] = owns.setdefault(symbol, 0) + shares
    # filter zero-share stocks
    owns = {k: v for k, v in owns.items() if v != 0}
    return owns

def time_now():
    """HELPER: get current UTC date and time"""
    now_utc = datetime.now(timezone.utc)
    return str(now_utc.date()) + ' @time ' + now_utc.time().strftime("%H:%M:%S")

if __name__ == "__main__":
    app.run()
