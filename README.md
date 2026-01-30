#--------------------------My Finance Tracker-------------------------

## Video Demo

## Description

This project is a web-based expense tracker that helps users manage their monthly finances in a simple and structured way. Users can set s monthly budget, record their expenses, and track how much money they have spent and how much remains.
The application is designed to reflect real-life financial behavior. Budgets cannot be set for future months, and once a month is closed, expenses from that month can no longer be edited or added. This encourages users to review and finalize their spending month by month.
This project was created as the final project for CS50X.

## Why This Project Is Important

Many people track expenses informally or forget to review their spending regularly. This application helps users:

- Stay aware of their monthly spending
- Keep past financial records accurate by locking complete months

By enforcing rules such as month locking and budget validation, the application promotes disciplined and realistic expense tracking.

## Objectives

- Allow users to securely manage personal expenses
- Provide a clear monthly view of spending and remaining budget
- Prevent accidental or unrealistic data entry (such as future budgets, expenses)
- Apply authentication, authorization, and server-side validation

## Problem Solved

Without structure, expense tracking becomes unreliable. Users often:

- Forget what monnth an expense belongs to
- Modify past records unintentionally
- Set unrealistic future budgets

This project solves these issues by:

- Organizing expenses by month
- Locking months once finalized
- Restricting future-month actions
- Enforcing all rules on the server side

## Features Explained

### USer Authentication

Users can register, log in and log out securely. Passwords are hashed before being stored in the database.

### Monthly Budget

Each user can sset a budget for a specific month. Budgets cannot be created for future months, ensuring realistic planning.

### Expense Management

Users can add, edit, and delete expenses for an open month. Each expense includes a name, amount, and date.

### Automation Calculations

The dashboard automatically calculates:

- Total budget
- Total expenses
- Remaining balance

### Month Locking

Users can close a month once they are done reviewing it. After closing:

- Expenses cannot be added or edited
- Data remains read-only for accuracy

### Validation and Security

- Server-side checks prevent invalid actions
- CSRF protection is enabled for all forms
- Unauthorized access is blocked using login requirements

## How To Use The Application

1. Register a new account or log in.
2. Set a budget for the current month.
3. Add expenses as you spend money.
4. Review totals on the dashboard.
5. Close the month once finished.
6. Move on to the next month.

## How To Run

1. Install dependencies: pip install -r requirements.txt
2. Run the application: flask run or python app.py
3. Open the provided local URL in a web browser.

## Technologies Used

- Python
- Flask
- SQLite
- Flask-WTF
- Flask-Session
- HTML, CSS, Jinja Templates
