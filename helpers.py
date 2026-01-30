from flask import json, redirect, render_template, session
from functools import wraps
from datetime import datetime
    
def login_required(f):
    """
    Decorator to require login before accessing a route.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def usd(amount):
    if amount is None:
        amount = 0.0  # default to 0 if no expenses
    return f"${amount:,.2f}"


#check if budget exsists to add expense
def budget_exists(user_id, month, db):
    row = db.execute("SELECT * FROM budgets WHERE user_id = ? AND month = ?", (user_id, month)).fetchone()
    db.commit()
    return row is not None

#check month it it is closed for adding or editing expenses
def is_month_closed(user_id, month, db):
    row = db.execute(
        "SELECT locked FROM budgets WHERE user_id = ? AND month = ?", 
        (user_id, month)
    ).fetchone()
    return bool(row and row["locked"])
