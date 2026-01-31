from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, DecimalField, DateField, PasswordField
from wtforms.validators import DataRequired, NumberRange, Regexp


#register form
class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirmation = PasswordField("Confirmation", validators=[DataRequired()])
    submit = SubmitField("Register")

#login form
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

#change password form
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    confirmation = PasswordField("Confirm New Password", validators=[DataRequired()])
    submit = SubmitField("Change Password")

#expense add/edit form
class ExpenseForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    amount = DecimalField("Amount", places=2, validators=[DataRequired()])
    expense_date = DateField("Date", validators=[DataRequired()])
    submit = SubmitField("Save")

#budget form
class BudgetForm(FlaskForm):
    amount = DecimalField("Amount", places=2, validators=[DataRequired()])
    month = StringField("Month", validators=[DataRequired()])
    submit = SubmitField("Set Budget")

#for delete
class DeleteConfirmationForm(FlaskForm):
    submit = SubmitField("Delete")

#month select form for displaying the expenses of a particular month
class MonthSelectForm(FlaskForm):
    selected_month = StringField("Month", validators=[DataRequired(), Regexp(r"^\d{4}-\d{2}$", message="Invalid month format")])
    submit = SubmitField("Submit")  

#for closing the month by clicking the form button
class CloseMonth(FlaskForm):
    submit = SubmitField("CLOSE MONTH")  