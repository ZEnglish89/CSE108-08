from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User
from forms import LoginForm, RegisterForm

app = Flask(__name__)
app.config.from_object(Config)

# Initialize DB
db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # redirect if not logged in

# Required user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --------------------------
# ROUTES
# --------------------------

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:  # plaintext (for now)
            login_user(user)
            flash('Logged in successfully.', 'success')

            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('dashboard_admin'))
            elif user.role == 'instructor':
                return redirect(url_for('dashboard_instructor'))
            elif user.role == 'student':
                return redirect(url_for('dashboard_student'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard/student')
@login_required
def dashboard_student():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    return render_template('dashboard_student.html')

@app.route('/dashboard/instructor')
@login_required
def dashboard_instructor():
    if current_user.role != 'instructor':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    return render_template('dashboard_instructor.html')

@app.route('/dashboard/admin')
@login_required
def dashboard_admin():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    return render_template('dashboard_admin.html')

# --------------------------
# USER MANAGEMENT (CRUD)
# --------------------------

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    form = RegisterForm()
    if form.validate_on_submit():
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            role=form.role.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash(f"User '{new_user.username}' created successfully.", 'success')
        return redirect(url_for('admin_users'))

    users = User.query.all()
    return render_template('user_management.html', users=users, form=form)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if current_user.role != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    user = User.query.get_or_404(user_id)
    form = RegisterForm(obj=user)

    if request.method == 'POST' and form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.password = form.password.data
        user.role = form.role.data
        db.session.commit()
        flash("User updated successfully.", "success")
        return redirect(url_for('admin_users'))

    return render_template('register.html', form=form, edit_mode=True)

@app.route('/admin/users/delete/<int:user_id>')
@login_required
def admin_delete_user(user_id):
    if current_user.role != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "info")
    return redirect(url_for('admin_users'))

# --------------------------
# ADD COURSE (Placeholder)
# --------------------------

@app.route('/add-course')
@login_required
def add_course():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    return render_template('add_course.html')

# --------------------------
# Create tables
# --------------------------
with app.app_context():
    db.create_all()

# --------------------------
# RUN APP
# --------------------------
if __name__ == '__main__':
    app.run(debug=True)