from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- Database ----------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'admission.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
os.makedirs(app.instance_path, exist_ok=True)
db = SQLAlchemy(app)

# ---------------- Mail ----------------
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = 'rajagokilavivek@gmail.com'
app.config["MAIL_PASSWORD"] = 'qpdz nvas kzog akif'  # Gmail App Password
app.config["MAIL_DEFAULT_SENDER"] = 'SchoolEmail <rajagokilavivek@gmail.com>'
mail = Mail(app)

# ---------------- Login ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'



# ---------------- Models ----------------
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    course = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="Pending")

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

@login_manager.user_loader
def load_user(admin_id):
    return Admin.query.get(int(admin_id))

# ---------------- Routes ----------------
@app.route('/')
def home():
    return render_template('register.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        # Save student
        student = Student(
            name=request.form['name'],
            email=request.form['email'],
            phone=request.form['phone'],
            dob=request.form['dob'],
            course=request.form['course']
        )
        db.session.add(student)
        db.session.commit()

        # Send confirmation email
        try:
            msg = Message("Application Received", recipients=[student.email])
            msg.body = f"Hello {student.name},\n\nYour application for {student.course} has been received. Status: Pending."
            mail.send(msg)
        except Exception as e:
            print("Email failed:", e)

        flash("Registration successful! Check your email for confirmation.", "success")
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/status', methods=['GET', 'POST'])
def status():
    student = None
    if request.method == 'POST':
        email = request.form['email']
        student = Student.query.filter_by(email=email).first()
    return render_template('status.html', student=student)

# ---------------- Admin Routes ----------------
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            login_user(admin)
            return redirect(url_for('admin_panel'))
        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for('admin_login'))
    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_panel():
    students = Student.query.all()
    return render_template('admin.html', students=students)

@app.route('/admin/approve/<int:student_id>')
@login_required
def approve_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.status = "Approved"
    db.session.commit()

    # Send approval email
    try:
        msg = Message("Application Approved", recipients=[student.email])
        msg.body = f"Hello {student.name},\n\nYour application for {student.course} has been approved. Congratulations!"
        mail.send(msg)
    except Exception as e:
        print("Email failed:", e)

    flash(f"{student.name} approved.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/reject/<int:student_id>')
@login_required
def reject_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.status = "Rejected"
    db.session.commit()

    # Send rejection email
    try:
        msg = Message("Application Rejected", recipients=[student.email])
        msg.body = f"Hello {student.name},\n\nYour application for {student.course} has been rejected. Contact admin for details."
        mail.send(msg)
    except Exception as e:
        print("Email failed:", e)

    flash(f"{student.name} rejected.", "info")
    return redirect(url_for('admin_panel'))

# ---------------- Init DB ----------------
def create_tables():
    db.create_all()
    if not Admin.query.first():
        admin = Admin(username="admin", password="admin123")
        db.session.add(admin)
        db.session.commit()

# ---------------- Run ----------------
if __name__ == "__main__":
    with app.app_context():
        create_tables()
    app.run(debug=True, port=5001)
