from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User, Course
from forms import LoginForm, RegisterForm, newCourse, EditCourseForm

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
            role=form.role.data,
#            classes = {}
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

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        if form.password.data:
            user.password = form.password.data
        user.role = form.role.data
        db.session.commit()
        flash("User updated successfully.", "success")
    else:
        flash("Invalid form data", "danger")

    return redirect(url_for('admin_users'))

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
# COURSE MANAGEMENT (CRUD)
# --------------------------

@app.route('/admin/courses',methods = ["GET","POST"])
@login_required
def admin_courses():
    if current_user.role != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))
    
    form = newCourse()

    instructors = User.query.filter_by(role='instructor').all()
    form.teacher.choices = [(instr.username, instr.username) for instr in instructors]

    if form.validate_on_submit():
        new_course = Course(
            title = form.title.data,
            teacher = form.teacher.data,
            time = form.time.data,
            currStudents = 0,
            capacity = form.capacity.data,
            students = {}
        )
        db.session.add(new_course)
        db.session.commit()
        flash(f"Course '{new_course.title}' created successfully.", 'success')
        return redirect(url_for('admin_courses'))
    courses = Course.query.all()
    return render_template('course_management.html', courses=courses, form=form)

@app.route('/admin/edit_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    course = Course.query.get_or_404(course_id)
    form = EditCourseForm()

    # Populate dropdown
    form.teacher.choices = [(user.username, user.username) for user in User.query.filter_by(role='instructor').all()]

    if form.validate_on_submit():
        course.title = form.title.data
        course.teacher = form.teacher.data
        course.time = form.time.data
        course.capacity = form.capacity.data
        db.session.commit()
        return redirect(url_for('admin_courses'))

    # Prefill form for GET
    form.title.data = course.title
    form.teacher.data = course.teacher
    form.time.data = course.time
    form.capacity.data = course.capacity

    return render_template('edit_course.html', form=form, course=course)

@app.route('/admin/delete_course/<int:course_id>', methods=['POST'])
@login_required
def delete_course(course_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    return redirect(url_for('admin_courses'))


@app.route('/api/instructors')
@login_required
def get_instructors():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    instructors = User.query.filter_by(role='instructor').all()
    return jsonify([{'username': i.username} for i in instructors])

@app.route('/admin/courses/<int:course_id>/update', methods=['POST'])
@login_required
def update_course(course_id):
    data = request.get_json()
    course = Course.query.get_or_404(course_id)

    course.title = data.get("title", course.title)
    course.teacher = data.get("teacher", course.teacher)
    course.time = data.get("time", course.time)
    course.capacity = data.get("capacity", course.capacity)

    db.session.commit()
    return jsonify({"success": True}), 200

# --------------------------
# Create tables
# --------------------------
with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        admin_user = User(
            username="admin",
            email="admin@ucmerced.edu",
            password="admin123",
            role="admin"
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created: admin / admin123")

# --------------------------
# RUN APP
# --------------------------
if __name__ == '__main__':
    app.run(debug=True)