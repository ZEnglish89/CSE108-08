from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User, Course, enrollments
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
    
    enrolled_courses = current_user.enrolled_courses
    return render_template('dashboard_student.html', enrolled_courses=enrolled_courses)

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
# STUDENT COURSE MANAGEMENT
# --------------------------

@app.route('/courses')
@login_required
def view_courses():
    """View all available courses"""
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    
    courses = Course.query.all()
    course_data = []
    for course in courses:
        enrolled_count = len(course.enrolled_students)
        is_enrolled = current_user in course.enrolled_students
        course_data.append({
            'course': course,
            'enrolled_count': enrolled_count,
            'is_enrolled': is_enrolled,
            'has_space': enrolled_count < course.capacity
        })
    
    return render_template('view_courses.html', courses=course_data)


@app.route('/enroll/<int:course_id>')
@login_required
def enroll_course(course_id):
    """Enroll student in a course"""
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    
    course = Course.query.get_or_404(course_id)
    enrolled_count = len(course.enrolled_students)
    
    if current_user in course.enrolled_students:
        flash(f'You are already enrolled in {course.title}.', 'warning')
        return redirect(url_for('view_courses'))
    
    if enrolled_count >= course.capacity:
        flash(f'{course.title} is full. Cannot enroll.', 'danger')
        return redirect(url_for('view_courses'))
    
    course.enrolled_students.append(current_user)
    db.session.commit()
    
    flash(f'Successfully enrolled in {course.title}!', 'success')
    return redirect(url_for('dashboard_student'))

@app.route('/drop/<int:course_id>')
@login_required
def drop_course(course_id):
    """Drop a course"""
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    
    course = Course.query.get_or_404(course_id)
    
    if current_user in course.enrolled_students:
        course.enrolled_students.remove(current_user)
        db.session.commit()
        flash(f'Dropped {course.title}.', 'info')
    else:
        flash('You are not enrolled in this course.', 'warning')
    
    return redirect(url_for('dashboard_student'))

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
            capacity = form.capacity.data,
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
# Grade Management
# --------------------------

@app.route('/admin/courses/<int:course_id>/grades',methods = ['GET','POST'])
@login_required
def course_grades(course_id):
    if not (current_user.role == 'admin' or current_user.role == 'instructor'):
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    course = Course.query.get_or_404(course_id)
    students = []

    # Handle Add Student
    if request.method == 'POST':
        if 'add_student' in request.form:
            student_id = int(request.form.get('student_id'))
            existing = db.session.execute(
                enrollments.select().where(
                    enrollments.c.student_id == student_id,
                    enrollments.c.course_id == course.id
                )
            ).fetchone()

            if not existing:
                db.session.execute(
                    enrollments.insert().values(
                        student_id=student_id,
                        course_id=course.id,
                        grade=0
                    )
                )
                db.session.commit()
                flash("Student enrolled successfully!", "success")
                return redirect(url_for('course_grades', course_id=course.id))

        elif 'remove_student' in request.form:
            student_id = int(request.form.get('remove_student'))
            db.session.execute(
                enrollments.delete().where(
                    enrollments.c.student_id == student_id,
                    enrollments.c.course_id == course.id
                )
            )
            db.session.commit()
            flash("Student removed from course.", "success")
            return redirect(url_for('course_grades', course_id=course.id))

    # Display currently enrolled students
    for student in course.enrolled_students:
        link = db.session.execute(
            enrollments.select().where(
                enrollments.c.student_id == student.id,
                enrollments.c.course_id == course.id
            )
        ).fetchone()
        students.append({
            "user": student,
            "grade": link.grade if link else 0
        })

    # Get students NOT in this course
    enrolled_ids = [student.id for student in course.enrolled_students]
    available_students = User.query.filter(
        User.role == 'student',
        ~User.id.in_(enrolled_ids)
    ).all()

    return render_template("grade_management.html",
                           course=course,
                           students=students,
                           available_students=available_students)

@app.route('/courses/<int:course_id>/grade/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_grade(course_id, student_id):
    if current_user.role not in ['admin', 'instructor']:
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    course = Course.query.get_or_404(course_id)
    student = User.query.get_or_404(student_id)

    link = db.session.execute(
        enrollments.select().where(
            enrollments.c.student_id == student_id,
            enrollments.c.course_id == course_id
        )
    ).fetchone()

    grade = link.grade if link else 0

    if request.method == 'POST':
        new_grade = int(request.form['grade'])
        db.session.execute(
            enrollments.update().where(
                enrollments.c.student_id == student_id,
                enrollments.c.course_id == course_id
            ).values(grade=new_grade)
        )
        db.session.commit()
        flash("Grade updated!", "success")
        return redirect(url_for('course_grades', course_id=course_id))

    return render_template("edit_grade.html",
                           course=course,
                           student=student,
                           grade=grade)

@app.route('/instructor/courses',methods = ['GET','POST'])
@login_required
def instructor_courses():
    if current_user.role != 'instructor':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))
    courses = Course.query.filter_by(teacher = current_user.username).all()

    return render_template('course_list.html',courses = courses)

# --------------------------
# Create tables and sample data
# --------------------------
with app.app_context():
    db.create_all()

    # Create admin user if it doesn't exist
    if not User.query.filter_by(username="admin").first():
        admin_user = User(
            username="admin",
            email="admin@ucmerced.edu",
            password="admin123",
            role="admin"
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created: admin / admin123")

    # Create some sample instructors and courses
    if not User.query.filter_by(username="instructor").first():
        instructor_user = User(
            username="instructor",
            email="instructor@ucmerced.edu",
            password="instructor123",
            role="instructor"
        )
        db.session.add(instructor_user)
        
        # Create sample student
        student_user = User(
            username="student",
            email="student@ucmerced.edu", 
            password="student123",
            role="student"
        )
        db.session.add(student_user)
        
        # Create sample courses
        if not Course.query.first():
            sample_courses = [
                Course(title="Math 101", teacher="instructor", time="MWF 10:00-10:50 AM", capacity=30),
                Course(title="Physics 121", teacher="instructor", time="TR 11:00-11:50 AM", capacity=25),
                Course(title="CSE 106", teacher="instructor", time="MWF 2:00-2:50 PM", capacity=20),
                Course(title="CSE 162", teacher="instructor", time="TR 3:00-3:50 PM", capacity=15),
            ]
            for course in sample_courses:
                db.session.add(course)
        
        db.session.commit()
        print("Sample users and courses created")

# --------------------------
# RUN APP
# --------------------------
if __name__ == '__main__':
    app.run(debug=True)