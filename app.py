import os
import pysqlite3 as sqlite3
from flask import Flask, flash, json, render_template, request, redirect, session, url_for, g
from datetime import datetime, date
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from forms import BudgetForm, ChangePasswordForm, DeleteConfirmationForm, ExpenseForm, RegisterForm, LoginForm, MonthSelectForm
from flask_wtf.csrf import CSRFError
from flask_wtf import CSRFProtect

from helpers import login_required, usd, budget_exists, is_month_closed

#loading the config file
with open('templates/config.json', 'r') as c:
    params = json.load(c)['params']

app = Flask(__name__)
csrf = CSRFProtect(app)
app.config['WTF_CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = params.get('secret_key') 

#handling CSRFError globally at once for all forms
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash("Form submission failed due to security validation. Please try again.", "danger")
    return redirect(request.referrer or url_for('index'))

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

DATABASE = "expense.db"
#Database functions
def get_db():
    '''Return a DB connection for the current request.'''
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, timeout=10, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

#for pragma
def configure_sqlite():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.close()

configure_sqlite()

@app.teardown_appcontext
def close_db(exception=None):
    '''Close DB at end of request'''
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    '''create DB if missing and apply schema once.'''
    if not os.path.exists(DATABASE):
        db = get_db()
        with open("schema.sql") as f:
            db.executescript(f.read())
        db.commit()
        db.close()

#initialie DB once at startup
init_db()

@app.route('/')
def index():
    return render_template('index.html', params=params)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        confirmation = form.confirmation.data

        if password != confirmation:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register'))
        
        try:
            hashed = generate_password_hash(password)
            db = get_db()
            cur = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, hashed))
            db.commit()
            user_id = cur.lastrowid
            session["user_id"] = user_id
            flash("Registered successfully!", "success")
            return redirect(url_for('dashboard'))
            
        except sqlite3.IntegrityError:
            flash("Username already exists.", "danger")
            return redirect(url_for('register'))
        
    return render_template('register.html', params=params, form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        db = get_db()
        cur = db.execute("SELECT id, hash FROM users WHERE username = ?", (username,))
        user = cur.fetchone()

        if user is None or not check_password_hash(user["hash"], password):
            flash("Invalid username or password", "danger")
            return redirect(url_for('login'))
        
        session["user_id"] = user["id"]
        flash("Logged in successfully!", "success")
        return redirect(url_for('dashboard'))
    
    return render_template('login.html', params=params, form=form)

@app.route('/logout')
def logout():
    #clear session
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('index'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    user_id = session.get('user_id')
    form = ChangePasswordForm()

    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data
        confirmation = form.confirmation.data

        if new_password != confirmation:
            flash("New passwords do not match.", "danger")
            return redirect(url_for('change_password'))
        
        db = get_db()
        user = db.execute("SELECT hash FROM users WHERE id = ?", (user_id,)).fetchone()

        if not check_password_hash(user["hash"], current_password):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for('change_password'))
        
        new_hashed = generate_password_hash(new_password)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", (new_hashed, user_id))
        db.commit()
        flash("Password changed successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('change_password.html', params=params, form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    user_id = session.get('user_id')
    expenses = []
    total_expense = 0
    total_budget = 0
    budget = None
    month_locked = False
    current_month = datetime.today().strftime('%Y-%m')

    form = MonthSelectForm()

    db = get_db()

    # Handle POST: user selects a month
    if form.validate_on_submit():
        selected_month = form.selected_month.data
        if not selected_month:
            flash("Please select a month to view expenses.", "warning")
            return redirect(url_for('dashboard'))
        
        #checking if the selected_month is future to display the expenses
        if selected_month > current_month:
            flash("You cannot select a future month.", "danger")
            return redirect(url_for('dashboard'))

        # Save selected month in session so it persists across page loads
        session['selected_month'] = selected_month

    # For GET request or after redirect, get month from session
    selected_month = session.get('selected_month')

    if selected_month:
        # Check if budget exists for the selected month
        budget = db.execute("SELECT * FROM budgets WHERE user_id = ? AND month = ?", (user_id, selected_month)).fetchone()

        # Only fetch expenses if a budget exists
        if budget:
            expenses = db.execute("SELECT * FROM expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ? ORDER BY date DESC", (user_id, selected_month)).fetchall()
            total_budget = budget["amount"] or 0
            total_expense = db.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ?", (user_id, selected_month)).fetchone()["total"]
            month_locked = is_month_closed(user_id, selected_month, db)
        else:
            flash(f"No budget set for {selected_month}. Please set a budget first.", "warning")

    return render_template('dashboard.html', params=params, budget=budget, expenses=expenses, selected_month=selected_month, current_month=current_month, total_expense=total_expense, total_budget=total_budget, form=form, is_month_closed=month_locked)



@app.route('/set_budget', methods=['GET', 'POST'])
@login_required
def set_budget():
    user_id = session.get('user_id')
    form = BudgetForm()

    current_month = datetime.today().strftime('%Y-%m')

    if form.validate_on_submit():
        month = str(form.month.data)
        amount = float(form.amount.data)

        #checking if the month is future to set budget
        if month > current_month:
            flash("You cannot set a budget for a future month.", "danger")
            return redirect(url_for('dashboard'))
        
        db = get_db()
        user = db.execute("SELECT id FROM budgets WHERE user_id = ? AND month = ?", (user_id, month)).fetchone()
        if user:
            db.execute("UPDATE budgets SET amount = ? WHERE user_id = ? AND month = ?", (amount, user_id, month))
            db.commit()
            flash("Budget updated successfully!", "success")
        else:
            db.execute("INSERT INTO budgets (user_id, month, amount) VALUES (?, ?, ?)", (user_id, month, amount))
            db.commit()
            flash("Budget set successfully!", "success")
        return redirect(url_for('dashboard'))
    return render_template('set_budget.html', params=params, current_month=current_month, form=form)

@app.route('/expense/<int:eid>', methods=['GET', 'POST'])
@login_required
def expense(eid):
    user_id = session.get('user_id')
    form =  ExpenseForm()
    db = get_db()

    if form.validate_on_submit():
        name = form.name.data
        amount = float(form.amount.data)
        expense_date = form.expense_date.data

        month = str(expense_date)[:7]  # 'YYYY-MM'

        
        if not budget_exists(user_id, month, db):
            flash("Please set a budget for the month before adding expense.", "warning")
            return redirect(url_for('set_budget'))
        
        #check if the month is closed for adding or editing expenses
        if is_month_closed(user_id, month, db):
            flash("This month is closed. Expenses cannot be edited or added.", "danger")
            return redirect(url_for('dashboard'))
        
        # add new expenses id eid = 0
        if eid == 0:
            db.execute("INSERT INTO expenses (user_id, name, amount, date) VALUES (?, ?, ?, ?)", (user_id, name, amount, expense_date))
            db.commit()
            flash("Expense added successfully!", "success")
        
        #update/edit the existing expense which has id == eid
        else:
            user = db.execute("SELECT * FROM expenses WHERE user_id = ? AND id = ?", (user_id, eid)).fetchone()
            if user is None:
                flash("Expense not found or unauthorized.", "danger")
                return redirect(url_for('dashboard'))
            db.execute("UPDATE expenses SET name = ?, amount = ?, date = ? WHERE user_id = ? AND id = ?", (name, amount, expense_date, user_id, eid))
            db.commit()
            flash("Expense updated successfully!", "success")
                
        return redirect(url_for('dashboard'))
    
    # GET request — render form
    expense = None
    if eid != 0:
        # Load existing expense to prefill form
        expense = db.execute(
            "SELECT * FROM expenses WHERE user_id = ? AND id = ?",
            (user_id, eid)
        ).fetchone()

        if not expense:
            flash("Expense not found or unauthorized.", "danger")
            return redirect(url_for('dashboard'))
        
        #prefill form with existing data
        if request.method == 'GET':
            form.name.data = expense['name']
            form.amount.data = expense['amount']
            form.expense_date.data = datetime.strptime(expense['date'], '%Y-%m-%d').date()

    return render_template('expense.html', params=params, expense=expense, today=date.today().isoformat(), form=form)

@app.route('/delete_expense/<int:eid>', methods=['GET', 'POST'])
@login_required
def delete_expense(eid):
    user_id = session.get('user_id')
    form = DeleteConfirmationForm()
    db = get_db()

    expense = db.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (eid, user_id)
    ).fetchone()

    if not expense:
        flash("Expense not found or unauthorized.", "danger")
        return redirect(url_for('dashboard'))
    
    if form.validate_on_submit():
        row = db.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (eid, user_id))
        db.commit()
        if row.rowcount != 1:
            flash("Error deleting expense. Please try again.", "danger")
            return redirect(url_for('dashboard'))   
        
        flash("Expense deleted successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('confirm_delete.html', params=params, expense=expense, form=form)

#close or lock the month if user clicks 'Close Month'
@app.route('/close_month/<month>', methods=['POST'])
@login_required
def close_month(month):
    """Lock a budget month so no further expenses can be added or edited."""
    user_id = session.get('user_id')
    db = get_db()

    # Check if budget exists
    budget = db.execute(
        "SELECT * FROM budgets WHERE user_id = ? AND month = ?", 
        (user_id, month)
    ).fetchone()

    if not budget:
        flash(f"No budget set for {month}. Cannot close the month.", "warning")
        return redirect(url_for('dashboard'))

    # Update locked column
    if budget['locked']:
        flash(f"Month {month} is already closed.", "info")
    else:
        db.execute(
            "UPDATE budgets SET locked = 1 WHERE user_id = ? AND month = ?", 
            (user_id, month)
        )
        db.commit()
        flash(f"Month {month} has been closed successfully!", "success")

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run()