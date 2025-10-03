from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"  

# --- Hardcoded users ---
USERS = {
    "kotia": "054761",   
    "kisia": "172001"
}

# --- DB Helper ---
def get_db():
    conn = sqlite3.connect("finance.db")
    conn.row_factory = sqlite3.Row
    return conn

# --- Init DB ---
def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        amount REAL,
        type TEXT,
        category TEXT,
        date TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in USERS and USERS[username] == password:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return "Invalid login"
    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    conn = get_db()
    c = conn.cursor()

    # Add transaction
    if request.method == "POST":
        amount = float(request.form["amount"])
        type_ = request.form["type"]
        category = request.form["category"]
        c.execute("INSERT INTO transactions (user, amount, type, category, date) VALUES (?,?,?,?,?)",
                  (user, amount, type_, category, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()

    # Personal transactions
    c.execute("SELECT * FROM transactions WHERE user=?", (user,))
    transactions = c.fetchall()

    # Personal balance
    income = sum(t["amount"] for t in transactions if t["type"] == "income")
    expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
    balance = income - expenses

    # Combined balance
    c.execute("SELECT * FROM transactions")
    all_tx = c.fetchall()
    total_income = sum(t["amount"] for t in all_tx if t["type"] == "income")
    total_expenses = sum(t["amount"] for t in all_tx if t["type"] == "expense")
    total_balance = total_income - total_expenses

    return render_template(
        "dashboard.html",
        user=user,
        transactions=[dict(t) for t in transactions],  # convert Row -> dict for JSON
        balance=balance,
        total_balance=total_balance,
        total_income=total_income,
        total_expenses=total_expenses
    )

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

