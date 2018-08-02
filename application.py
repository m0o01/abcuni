from flask import Flask, render_template, redirect, url_for, request, flash, session, send_from_directory,  Markup
from flask_mysqldb import MySQL
from functools import wraps
from passlib.hash import sha256_crypt
from flask_mail import Mail, Message
from flask_recaptcha import ReCaptcha
import os
import helpers

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(20)

app.config['UPLOAD_FOLDER'] = '/home/mohamed/Desktop/ABC_UNI/uploads/users_images'

app.config.from_pyfile('config.cfg')

mysql = MySQL(app)

mail = Mail(app)

recaptcha = ReCaptcha(app=app)

@app.route('/login', methods=['GET','POST'])
def login():
    # Loggin out any previous sissions
    session.clear()
    if request.method == "POST":
        # Taking the Loign From data
        role = request.form['role']
        id = request.form['id']
        password_candidate = request.form['password']
        # Connecting to the Database
        cur = mysql.connection.cursor()
        if role == 'student':
            cur.execute('''SELECT * FROM reg_students WHERE student_id = %s''', [id])
            user_data = cur.fetchone()
            # if the user was found
            if user_data:
                hashed_password = user_data['password']
                # Verifying that the password is correct
                if sha256_crypt.verify(password_candidate, hashed_password):
                    # The password is correct. Taking user's data from the database
                    cur.execute('''SELECT * FROM students_db WHERE student_id = %s''', [id])
                    user_data = cur.fetchone()
                    session['logged_in'] = True
                    session['user_type'] = 'student'
                    session['user_id'] = user_data['student_id']
                    flash("You're Now logged in.", "success")
                    cur.close()
                    return redirect(url_for('index'))
                else:
                    flash("Password isn't correct, Please check your password again.", "warning")
            else:
                flash("No student registerd with such ID, Check the ID or regist your account first", "warning")
        elif role == 'teacher':
            cur.execute('''SELECT * FROM professors WHERE staff_id = %s''', [id])
            user_data = cur.fetchone()
            # if the user was found
            if user_data:
                hashed_password = user_data['password']
                # Verifying that the password is correct
                if sha256_crypt.verify(password_candidate, hashed_password):
                    # The password is correct. Taking user's data from the database
                    cur.execute('''SELECT * FROM professordb WHERE staff_id = %s''', [id])
                    user_data = cur.fetchone()
                    session['logged_in'] = True
                    session['user_type'] = 'student'
                    session['user_id'] = user_data['staff_id']
                    flash("You're Now logged in", "success")
                    cur.close()
                    return redirect(url_for('index'))
                else:
                    flash("Password isn't correct, Please check your password again.", "warning")
            else:
                flash("No Professor registerd with such ID, Check the ID or regist your account first", "warning")
        # The user must want to login as an employee
        else:
            cur.execute('''SELECT * FROM reg_employees WHERE staff_id = %s''', [id])
            user_account_data = cur.fetchone()
            # if the user was found
            if user_account_data:
                hashed_password = user_account_data['password']
                # Verifying that the password is correct
                if sha256_crypt.verify(password_candidate, hashed_password):
                    # The password is correct. Taking user's data from the database
                    cur.execute('''SELECT * FROM employees_db WHERE staff_id = %s''', [id])
                    user_data = cur.fetchone()
                    session['logged_in'] = True
                    session['user_type'] = 'employee'
                    session['user_id'] = user_data['staff_id']
                    if user_account_data.get('admin'):
                        session['is_admin'] = True
                    flash("You're Now logged in", "success")
                    cur.close()
                    return redirect(url_for('index'))
                else:
                    flash("Password isn't correct, Please check your password again.", "warning")
            else:
                flash("No Employee registerd with such ID, Check the ID or regist your account first", "warning")
    return render_template('login.html')

def is_logged(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You're Not logged in yet, Please Login first.", "warning")
            return redirect(url_for('login'))
    return wrap

def is_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'is_admin' in session:
            return f(*args, **kwargs)
        else:
            if 'logged_in' in session:
                data = get_user_data()
                return render_template('error403.html', data=data), 403
            return render_template('error403.html'), 403
    return wrap

def get_user_data():
    cur = mysql.connection.cursor()
    if session['user_type'] == 'student':
        cur.execute('''SELECT * FROM students_db WHERE student_id = %s''', [session['user_id']])
    elif session['user_type'] == 'employee':
        cur.execute('''SELECT * FROM employees_db WHERE staff_id = %s''', [session['user_id']])
    data = cur.fetchone()
    cur.close()
    return data

def get_articles():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM articles''')
    articles = cur.fetchall()
    cur.close()
    return articles

def get_index_articles():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM articles JOIN index_articles WHERE index_articles.article_id = articles.id''')
    articles = cur.fetchall()
    cur.close()
    return articles

def get_issues():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM contact''')
    issues = cur.fetchall()
    cur.close()
    return issues

def get_messages():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM messages JOIN users WHERE messages.recipient_id = users.user_id AND sender_id = %s''', [session['user_id']])
    sent = cur.fetchall()
    cur.execute('''SELECT * FROM messages JOIN users WHERE messages.sender_id = users.user_id AND recipient_id = %s''', [session['user_id']])
    received = cur.fetchall()
    cur.close()
    return sent, received

def get_students_IDs():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT student_id FROM reg_students''')
    students = cur.fetchall()
    students_IDs = []
    for student in students:
        students_IDs.append(student['student_id'])
    return students_IDs

def get_employees_IDs():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT staff_id FROM reg_employees''')
    employees = cur.fetchall()
    employees_IDs = []
    for employee in employees:
        employees_IDs.append(employee['staff_id'])
    return employees_IDs
    
def get_unread_messages():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM messages WHERE recipient_id = %s AND read_status = %s''', [session['user_id'], False])
    unread_messages = cur.fetchall()
    cur.close()
    return unread_messages

@app.errorhandler(404)
def error404(error):
    if 'logged_in' in session:
        data = get_user_data()
        return render_template('error404.html', data=data), 404
    return render_template('error404.html'), 404

@app.route('/')
def index():
    articles = get_index_articles()
    if 'logged_in' in session:
        data = get_user_data()
        return render_template('index.html', data=data, articles=articles)
    return render_template('index.html', articles=articles)

@app.route('/profile/<id>')
@is_logged
def profile(id):
    data = get_user_data()
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM users WHERE user_id = %s''', [id])
    user_data = cur.fetchone()
    user_id = session['user_id']
    if user_data == None:
        return render_template('error404.html', data=data), 404
    cur.close()
    return render_template("profile.html", data=data, user_data=user_data, user_id=user_id)

@app.route('/profile/message/<id>', methods=['GET', 'POST'])
@is_logged
def send_message(id):
    data = get_user_data()
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM users WHERE user_id = %s''', [id])
    user_data = cur.fetchone()
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        sender_id = session['user_id']
        cur.execute('''INSERT INTO messages (sender_id, recipient_id, title, message, read_status) VALUES (%s, %s, %s, %s, %s)''', [sender_id, id, title, message, False])
        mysql.connection.commit()
        flash("Message sent successfully.", "success")
        return redirect("/profile/{}".format(id))
    cur.close()
    return render_template("send_message.html", data=data, user_data=user_data)  

@app.route('/articles')
def articles():
    articles = get_articles()
    articles = articles[::-1]
    if 'logged_in' in session:
        data = get_user_data()
        return render_template('articles.html', data=data, articles=articles)
    return render_template('articles.html', articles=articles)

@app.route('/articles/<id>', methods=['GET', 'POST'])
def article_page(id):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM articles WHERE id = %s''', [id])
    article = cur.fetchone()
    article['article'] = Markup(article['article'])
    author_id = article['author']
    cur.execute('''SELECT firstname, lastname, job, photo_path FROM employees_db WHERE staff_id = %s''', [author_id])
    author_data = cur.fetchone()
    cur.execute('''SELECT * FROM comments JOIN users WHERE comments.user_id = users.user_id AND comments.article_id = %s''', [id])
    comments = cur.fetchall()
    comments = comments[::-1]
    if request.method == 'POST':
        if 'delete_comment' in request.form:
            comment_id = request.form.get('id')
            cur.execute('''DELETE FROM comments WHERE id = %s and article_id = %s''', [comment_id, id])
            mysql.connection.commit()
            flash('Comment deleted successfully', 'warning')
            return redirect("/articles/{}#comments".format(id))
        comment = request.form.get('comment')
        user_id = session['user_id']
        cur.execute('''INSERT INTO comments(user_id, article_id, comment) VALUES (%s ,%s, %s)''', [user_id, id, comment])
        mysql.connection.commit()
        return redirect("/articles/{}#comments".format(id))
    if 'logged_in' in session:
        data = get_user_data()
        return render_template('article.html', data=data, article=article, author_data=author_data, comments=comments)
    return render_template('article.html', article=article, author_data=author_data, comments=comments)

@app.route('/control-panel/articles', methods=["GET", "POST"])
@is_admin
def view_articles():
    data = get_user_data()
    issues = get_issues()
    articles = get_articles()
    articles_index = get_index_articles()
    if request.method == 'POST':
        id = request.form.get('id')
        cur = mysql.connection.cursor()
        if 'add' in request.form:
            cur.execute('''SELECT * FROM index_articles''')
            index_articles = cur.fetchall()
            if len(index_articles) > 3:
                flash("There's there articles already in the index, Remove one and add again.", "warning")
                return redirect(url_for("view_articles"))
            else:
                added_before = False
                for article in index_articles:
                    if int(id) == int(article['article_id']):
                        added_before = True
                        break
                if added_before:
                    flash("Article is already at the index page.", "warning")
                    return redirect(url_for("view_articles"))
                else:
                    cur.execute('''INSERT INTO index_articles(article_id) VALUES (%s)''', [id])
                    mysql.connection.commit()
                    flash("Article added to the index page successfully.", "success")
                    return redirect(url_for("view_articles"))
        else:
            cur.execute('''DELETE FROM index_articles WHERE article_id = %s''', [id])
            mysql.connection.commit()
            flash("Article removed from index page successfully", "success")
            return redirect(url_for("view_articles"))
    return render_template('control-panel/articles/view_articles.html', data=data, issues=issues, articles=articles, index_articles=articles_index)

@app.route('/control-panel/new-article', methods=['GET', 'POST'])
@is_admin
def new_article():
    data = get_user_data()
    issues = get_issues()
    if request.method == 'POST':
        author = data['firstname'] + " " + data['lastname']
        job = data['job']
        title = request.form.get('title')
        article = request.form.get('article')
        description = request.form.get('description')
        if 'cover' in request.files:
            cover = request.files.get('cover')
            # Checking if the file exists and format is allowed
            if cover and allowed_file(cover.filename):
                file_extension = cover.filename[cover.filename.find('.') : ]
                filename = "_".join(title.split()) + file_extension
                # Saving the file to server location folder
                cover.save(os.path.join('/home/mohamed/Desktop/ABC_UNI/uploads/articles', filename))
                cover = '/uploads/articles/' + filename
            else:
                flash('Cover Photo format not allowd.', 'warning')
        else:
            cover = None
        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO articles(title, author, article, description ,role,cover_path) VALUES (%s, %s, %s, %s,%s, %s)''', [title, session['user_id'], article, description,job, cover])
        mysql.connection.commit()
        cur.close()
        flash("Article had been added successfully.", "success")
        return redirect(url_for('view_articles'))
    return render_template('control-panel/articles/new_article.html', data=data, issues=issues)

@app.route('/control-panel/articles/edit', methods=['GET', 'POST'])
@is_admin
def edit_article():
    data = get_user_data()
    issues = get_issues()
    id = request.args.get('id')
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM articles WHERE id = %s''', [id])
    article_contents = cur.fetchone()
    article_cover = False
    if article_contents['cover_path'] != None:
        article_cover = True
    if request.method == 'POST':
        title = request.form.get('title')
        article = request.form.get('article')
        description = request.form.get('description')
        if 'cover' in request.files:
            cover = request.files.get('cover')
            # Checking if the file exists and format is allowed
            if cover and allowed_file(cover.filename):
                file_extension = cover.filename[cover.filename.find('.') : ]
                filename = "_".join(title.split()) + file_extension
                # Saving the file to server location folder
                cover.save(os.path.join('/home/mohamed/Desktop/ABC_UNI/uploads/articles', filename))
                cover = '/uploads/articles/' + filename
            else:
                flash('Cover Photo format not allowd.', 'warning')
                return redirect(url_for('edit_article'))
        else:
            cover = article_contents['cover_path']
        cur = mysql.connection.cursor()
        cur.execute('''UPDATE articles SET title = %s, description = %s , article = %s, cover_path = %s WHERE id = %s''', [title, description, article, cover, id])
        mysql.connection.commit()
        cur.close()
        flash("Article had been edited successfully.", "success")
        return redirect(url_for('view_articles'))
    return render_template('control-panel/articles/edit_article.html', data=data, issues=issues, article=article_contents, article_cover=article_cover)

@app.route('/control-panel/articles/delete', methods=['GET', 'POST'])
@is_admin
def delete_article():
    data = get_user_data()
    issues = get_issues()
    id = request.args.get('id')
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM articles WHERE id = %s''', [id])
    article = cur.fetchone()
    if request.method == 'POST':
        if 'back' in request.form:
            return redirect(url_for('view_articles'))
        else:
            cur.execute('''DELETE FROM articles WHERE id = %s''', [id])
            mysql.connection.commit()
            flash('Article has been deleted successfully.', 'success')
            cur.close()
            return redirect(url_for('view_articles'))
    cur.close()
    return render_template('control-panel/articles/delete_article.html', data=data, issues=issues, article=article)

@app.route('/control-panel/public_message', methods=['GET', 'POST'])
@is_admin
def public_message():
    data = get_user_data()
    issues = get_issues()
    recipients = request.args.get('public_message_recipients')
    if request.method == 'POST':
        title = request.form['title']
        message = request.form['message']
        cur = mysql.connection.cursor()
        if recipients == 'students':
            students_IDs = get_students_IDs()
            for student_id in students_IDs:
                cur.execute('''INSERT INTO messages (title, message, sender_id, recipient_id, read_status) VALUES (%s, %s, %s, %s, %s)'''
                ,[title, message, session['user_id'], student_id, False])
            flash('Message sent to all students successfully.','success')
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('students_control'))
        else:
            employees_IDs = get_employees_IDs()
            for employee_id in employees_IDs:
                cur.execute('''INSERT INTO messages (title, message, sender_id, recipient_id, read_status) VALUES (%s, %s, %s, %s, %s)'''
                ,[title, message, session['user_id'], employee_id, False])
            flash('Message sent to all employees successfully.','success')
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('employees_control'))
    return render_template('control-panel/public_message.html', data=data, issues=issues, recipients=recipients)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        title = request.form.get('title')
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO contact(title, name, email, message) VALUES (%s, %s, %s, %s)''', [title, name, email, message])
        mysql.connection.commit()
        cur.close()
        flash("Message Sent Successfuly. You'll get the replay soon.", "success")
        return redirect(url_for('index'))
    if session.get('logged_in'):
        data = get_user_data()
        return render_template("contact.html", data=data)
    return render_template("contact.html")

@app.route('/control-panel')
@is_admin
def control_panel():
    data = get_user_data()
    issues = get_issues()
    return render_template('control-panel/control-panel.html', data=data, issues=issues)

@app.route('/control-panel/students')
@is_admin
def students_control():
    data = get_user_data()
    issues = get_issues()
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM reg_students''')
    reg_students = cur.fetchall()
    cur.execute('''SELECT * FROM students_db''')
    students_db = cur.fetchall()
    cur.close()
    return render_template('control-panel/students.html', data=data, issues=issues, reg_students=reg_students, students_db=students_db)

@app.route('/control-panel/employees')
@is_admin
def employees_control():
    data = get_user_data()
    issues = get_issues()
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM reg_employees''')
    reg_employees = cur.fetchall()
    cur.execute('''SELECT * FROM employees_db''')
    employees_db = cur.fetchall()
    cur.close()
    return render_template('control-panel/employees.html', data=data, issues=issues, reg_employees=reg_employees, employees_db=employees_db)

def generate_student_id():
    cur = mysql.connection.cursor()
    cur.execute("""SELECT * FROM students_db""")
    result = cur.fetchall()
    cur.close()
    if result:
        return 100000 + len(result)
    return 100000

def generate_staff_id():
    cur = mysql.connection.cursor()
    cur.execute("""SELECT * FROM students_db""")
    result = cur.fetchall()
    cur.close()
    if result:
        return 200000 + len(result)
    return 200000

@app.route('/control-panel/students/add-student', methods=['GET', 'POST'])
@is_admin
def add_student():
    data = get_user_data()
    issues = get_issues()
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        gender = request.form['gender']
        faculty = request.form['faculty']
        department = request.form['department']
        year = request.form['year']
        semester = request.form['semester']
        contact_info = request.form['contact_info']
        student_id = generate_student_id()
        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO students_db(firstname, lastname, student_id, gender, faculty, department, year, semester, contact_info)\
                        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)''', [firstname, lastname, student_id, gender, faculty, department,
                        year, semester, contact_info])
        mysql.connection.commit()
        cur.close()
        flash("Student Add Successfully, Student ID: {}".format(student_id), "success")
        return redirect(url_for('students_control'))
    return render_template('control-panel/add-student.html', data=data, issues=issues)

@app.route('/control-panel/employees/add-employee', methods=['GET', 'POST'])
@is_admin
def add_employee():
    data = get_user_data()
    issues = get_issues()
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        gender = request.form['gender']
        job = request.form['job']
        contact_info = request.form['contact_info']
        staff_id = generate_staff_id()
        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO employees_db(firstname, lastname, staff_id, gender, job, contact_info)\
                        VALUES(%s, %s, %s, %s, %s, %s)''', [firstname, lastname, staff_id, gender, job, contact_info])
        mysql.connection.commit()
        cur.close()
        flash("Employee Add Successfully, Staff ID: {}".format(staff_id), "warning")
        return redirect(url_for('employees_control'))
    return render_template('control-panel/add_employee.html', data=data, issues=issues)

@app.route('/control-panel/employees/delete', methods=['GET','POST'])
@is_admin
def delete_employee():
    data = get_user_data()
    issues = get_issues()
    id = request.args['id']
    reg = request.args['reg']
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM employees_db WHERE staff_id = %s ''', [id])
    employee = cur.fetchone()
    if request.method == 'POST':
        if not 'back' in request.form:
            if reg == 'true':
                cur.execute('''DELETE FROM reg_employees WHERE staff_id = %s''', [id])
                flash('Employee Account with ID: {} Deleted Successfuly.'.format(id), 'warning')
            else:
                cur.execute('''DELETE FROM reg_employees WHERE staff_id = %s''', [id])
                cur.execute('''DELETE FROM employees_db WHERE staff_id = %s''', [id])
                flash('Employee with ID: {} deleted successfully from the database.'.format(id), 'warning')
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('employees_control'))
        else:
            return redirect(url_for('employees_control'))
    if reg == 'true' :
        return render_template('control-panel/delete_employee.html', data=data, issues=issues, employee=employee, reg=True)
    else:
        return render_template('control-panel/delete_employee.html', data=data, issues=issues, employee=employee, reg=False)

@app.route('/control-panel/students/delete', methods=['GET','POST'])
@is_admin
def delete_student():
    data = get_user_data()
    issues = get_issues()
    id = request.args['id']
    reg = request.args['reg']
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM students_db WHERE student_id = %s ''', [id])
    student = cur.fetchone()
    if request.method == 'POST':
        if not 'back' in request.form:
            if reg == 'true':
                cur.execute('''DELETE FROM reg_students WHERE student_id = %s''', [id])
                cur.execute('''DELETE FROM users WHERE user_id = %s''', [id])
                flash('Student Account with ID: {} Deleted Successfuly.'.format(id), 'primary')
            else:
                cur.execute('''DELETE FROM reg_students WHERE student_id = %s''', [id])
                cur.execute('''DELETE FROM students_db WHERE student_id = %s''', [id])
                flash('Student with ID: {} Deleted Successfuly.'.format(id), 'primary')
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('students_control'))
        else:
            return redirect(url_for('students_control'))
    if reg == 'true' :
        return render_template('control-panel/delete.html', data=data, issues=issues, student=student, reg=True)
    else:
        return render_template('control-panel/delete.html', data=data, issues=issues, student=student, reg=False)

@app.route('/control-panel/students/edit', methods=['GET', 'POST'])
@is_admin
def edit_student():
    data = get_user_data()
    issues = get_issues()
    id = request.args['id']
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM students_db WHERE student_id = %s ''', [id])
    student = cur.fetchone()
    student_gender = student['gender']
    student_faculty = student['faculty']
    faculties = ['Medicine', 'Computer Science', 'Engineering']
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        gender = request.form['gender']
        faculty = request.form['faculty']
        department = request.form['department']
        year = request.form['year']
        semester = request.form['semester']
        contact_info = request.form['contact_info']
        cur.execute('''UPDATE students_db SET firstname = %s, lastname = %s, gender = %s, faculty = %s, department = %s,
                       year = %s, semester = %s, contact_info = %s WHERE student_id = %s''', [firstname, lastname, gender, faculty,
                       department, year, semester, contact_info, id])
        mysql.connection.commit()
        cur.close()
        flash('Student Info Updated successfully.', 'success')
        return redirect(url_for('students_control'))
    return render_template('control-panel/edit.html', data=data, issues=issues ,student=student, student_gender=student_gender, student_faculty=student_faculty, faculties=faculties)

@app.route('/control-panel/employees/edit', methods=['GET', 'POST'])
@is_admin
def edit_employee():
    data = get_user_data()
    issues = get_issues()
    id = request.args['id']
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM employees_db WHERE staff_id = %s ''', [id])
    employee = cur.fetchone()
    employee_gender = employee['gender']
    employee_job = employee['job']
    jobs = ['IT Technical', 'Accounter', 'Organizer']
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        gender = request.form['gender']
        job = request.form['job']
        contact_info = request.form['contact_info']
        cur.execute('''UPDATE employees_db SET firstname = %s, lastname = %s, gender = %s, job = %s, contact_info = %s WHERE staff_id = %s''', [firstname, lastname, gender, job,
                     contact_info, id])
        mysql.connection.commit()
        cur.close()
        flash('Employee Info Updated successfully.', 'success')
        return redirect(url_for('employees_control'))
    return render_template('control-panel/edit_employee.html', data=data, issues=issues ,employee=employee, employee_gender=employee_gender, employee_job=employee_job, jobs=jobs)

@app.route('/control-panel/issues', methods=['GET', 'POST'])
@is_admin
def issues():
    data = get_user_data()
    issues = get_issues()
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM contact_solved''')
    solved_issues = cur.fetchall()
    cur.close()
    return render_template('control-panel/issues/issues.html', data=data, issues=issues, solved_issues=solved_issues)

@app.route('/control-panel/issues/<id>', methods=['GET', 'POST'])
@is_admin
def read_issue(id):
    data = get_user_data()
    issues = get_issues()
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        if 'solved' in request.form:
            cur.execute('''SELECT * FROM contact_solved WHERE id = %s''', [id])
            solve = True
        else:
            cur.execute('''SELECT * FROM contact WHERE id = %s''', [id])
            solve = False
        issue = cur.fetchone()
        issue['message'] = Markup(issue['message'])
        cur.close()
    return render_template('control-panel/issues/read_issue.html', data=data, issue=issue, issues=issues, solve=solve)

@app.route('/control-panel/issues/replay/<id>', methods=['GET', 'POST'])
@is_admin
def replay_issue(id):
    data = get_user_data()
    issues = get_issues()
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM contact WHERE id = %s''', [id])
    issue = cur.fetchone()
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        msg = Message(title, sender=("ABC University", "mohamedmamoon01@gmail.com"), recipients=[issue['email']])
        msg.html = message
        try:
            mail.send(msg)
        except:
            flash('Error while sending message, Try Later.', 'warning')
            return redirect(url_for('issues'))
        flash('Replay Message Sent Successfuly.', 'success')
        cur.execute('''INSERT INTO contact_solved(id, title, name, email, message, receive_date, solved_by) VALUES (%s, %s, %s, %s, %s, %s, %s)''', [issue['id'],
                       issue['title'], issue['name'], issue['email'], message, issue['date'], data['firstname'] + " " + data['lastname'] + " - " + data['job']])
        cur.execute('''DELETE FROM contact WHERE id = %s''', [issue['id']])
        mysql.connection.commit()
        return redirect(url_for('issues'))
    return render_template('control-panel/issues/replay_issue.html', data=data, issues=issues, issue=issue)

@app.route('/control-panel/issues/delete', methods=['GET', 'POST'])
@is_admin
def delete_issue():
    data = get_user_data()
    issues = get_issues()
    id = request.args.get('id')
    cur = mysql.connection.cursor()
    if 'solved' in request.args:
        cur.execute('''SELECT * FROM contact_solved WHERE id = %s''', [id])
        solve = True
    else:
        cur.execute('''SELECT * FROM contact WHERE id = %s''', [id])
        solve = False
    issue = cur.fetchone()
    issue['message'] = Markup(issue['message'])
    if request.method == 'POST':
        if 'solved' in request.args:
            if 'back' in request.form:
                return redirect(url_for('issues'))
            else:
                cur.execute('''DELETE FROM contact_solved WHERE id = %s''', [id])
                mysql.connection.commit()
                cur.close()
                flash('Issue Deleted Successfully', 'success')
                return redirect(url_for('issues'))
        else:
            if 'back' in request.form:
                return redirect(url_for('issues'))
            else:
                cur.execute('''DELETE FROM contact WHERE id = %s''', [id])
                mysql.connection.commit()
                cur.close()
                flash('Issue Deleted Successfully', 'success')
                return redirect(url_for('issues'))
    return render_template('control-panel/issues/delete_issue.html', data=data, issues=issues, issue=issue, solve=solve)

@app.route('/logout')
@is_logged
def logout():
    session.clear()
    flash("You logged Out.", "primary")
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def regesiter():
    return render_template("registerType.html")

@app.route('/dashboard')
@is_logged
def dashboard():
    data = get_user_data()
    unread_messages = get_unread_messages()
    return render_template("dashboard/dashboard.html", data=data, unread_messages=unread_messages)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)

@app.route('/uploads/articles/<filename>')
def uploaded_article_file(filename):
    return send_from_directory('/home/mohamed/Desktop/ABC_UNI/uploads/articles',filename)

@app.route('/dashboard/manage', methods=['GET', 'POST'])
@is_logged
def manage():
    data = get_user_data()
    unread_messages = get_unread_messages()
    # Submitting A Form
    if request.method == "POST":
        # Checking if the user want to change their profile photo
        if 'profile_photo_update' in request.form:
            # Checking if the user want to delere the current photo
            if 'delete_photo' in request.form:
                # Connecting to the database and executing query
                cur = mysql.connection.cursor()
                if session['user_type'] == 'student':
                    cur.execute('''UPDATE students_db SET photo_path = NULL WHERE student_id = %s''', [session['user_id']])
                else:
                    cur.execute('''UPDATE employees_db SET photo_path = NULL WHERE staff_id = %s''', [session['user_id']])
                cur.execute('''UPDATE users SET photo_path = NULL WHERE user_id = %s''', [session['user_id']])
                mysql.connection.commit()
                cur.close()
                data = get_user_data()
                flash('Photo Removed Successfully.', 'success')
            # The user want to upload a photo
            else:
                # Getting file from the form
                file = request.files.get('file')
                # Checking if the file was empty
                if file is None:
                    flash('No Selected Photo', 'warning')
                else:
                    # Checking if the file exists and format is allowed
                    if file and allowed_file(file.filename):
                        file_extension = file.filename[file.filename.find('.') : ]
                        filename = str(session['user_id']) + file_extension
                        # Saving the file to server location folder
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        filepath = '/uploads/' + filename
                        # Connecting to the database and updating the profile photo URL
                        cur = mysql.connection.cursor()
                        if session['user_type'] == 'student':
                            cur.execute('''UPDATE students_db SET photo_path = %s WHERE student_id = %s''', [filepath, session['user_id']])
                            cur.execute('''UPDATE users SET photo_path = %s WHERE user_id = %s''', [filepath, session['user_id']])
                        else:
                            cur.execute('''UPDATE employees_db SET photo_path = %s WHERE staff_id = %s''', [filepath, session['user_id']])
                            cur.execute('''UPDATE users SET photo_path = %s WHERE user_id = %s''', [filepath, session['user_id']])
                        mysql.connection.commit()
                        cur.close()
                        flash('Photo uploaded successfully!', 'success')
                        data = get_user_data()
                    else:
                        flash('File Format Not Allowed.', 'warning')
        # The user want to change their bio
        elif 'change_bio' in request.form:
            bio = request.form.get('bio')
            cur = mysql.connection.cursor()
            cur.execute('''UPDATE users SET BIO = %s WHERE user_id = %s''', [bio, session['user_id']])
            mysql.connection.commit()
            cur.close()
            flash('Bio Updated Successfully.', 'success')
        # The user want to change their password
        else:
            old_password = request.form['old_password']
            new_password = request.form['new_password']
            confirmed_pass = request.form['confirm_password']
            cur = mysql.connection.cursor()
            if session['user_type'] == 'student':
                cur.execute('''SELECT * FROM reg_students WHERE student_id = %s''', [session['user_id']])
            elif session['user_type'] == 'employee':
                cur.execute('''SELECT * FROM reg_employees WHERE staff_id = %s''', [session['user_id']])
            user_data = cur.fetchone()
            hashed_password = user_data['password']
            if sha256_crypt.verify(old_password, hashed_password):
                if confirmed_pass == new_password:
                    new_hashed_password = sha256_crypt.encrypt(new_password)
                    if session['user_type'] == 'student':
                        cur.execute('''UPDATE reg_students SET password = %s WHERE student_id = %s''', (new_hashed_password, session['user_id']))
                    elif session['user_type'] == 'employee':
                        cur.execute('''UPDATE reg_employees SET password = %s WHERE staff_id = %s''', (new_hashed_password, session['user_id']))
                    mysql.connection.commit()
                    cur.close()
                    flash('Your password changed successfully.', 'success')
                else:
                    flash("New password don't match confirm.", "warning")
            else:
                flash("Old password isn't correct!", "danger")
    return render_template("dashboard/manage.html", data=data, unread_messages=unread_messages)

@app.route('/dashboard/inbox')
@is_logged
def inbox():
    data = get_user_data()
    sent, received = get_messages()
    sent = sent[::-1]
    received = received[::-1]
    unread_messages = get_unread_messages()
    return render_template("dashboard/inbox.html", data=data, sent=sent, received=received, unread_messages=unread_messages)

@app.route('/dashboard/inbox/replay/<id>', methods=['GET', 'POST'])
@is_logged
def replay_message(id):
    data = get_user_data()
    unread_messages = get_unread_messages()
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM messages JOIN users WHERE messages.sender_id = users.user_id and messages.id = %s''', [id])
    message = cur.fetchone()
    if request.method == 'POST':
        title = request.form.get('title')
        replay_message = request.form.get('message')
        sender_id = session['user_id']
        recipient_id = message['sender_id']
        cur.execute('''INSERT INTO messages (sender_id, recipient_id, title, message, read_status) VALUES (%s, %s, %s, %s, %s)''', [sender_id, recipient_id, title, replay_message, False])
        mysql.connection.commit()
        cur.close()
        flash("Message Replay sent successfully.", "success")
        return redirect(url_for('inbox'))
    cur.close()
    return render_template("dashboard/replay_message.html", data=data, unread_messages=unread_messages, message=message)

@app.route('/dashboard/indox/message/<id>', methods=['GET','POST'])
@is_logged
def read_message(id):
    data = get_user_data()
    cur = mysql.connection.cursor()
    unread_messages = get_unread_messages()
    if request.method == 'POST':
        if 'received' in request.form:
            cur.execute('''UPDATE messages SET read_status = %s WHERE id = %s''', [True, id])
            mysql.connection.commit()
            unread_messages = get_unread_messages()
            cur.execute('''SELECT * FROM messages JOIN users WHERE messages.sender_id=users.user_id and messages.id = %s''', [id])
            message = cur.fetchone()
            cur.close()
            return render_template('dashboard/read_message.html', data=data, unread_messages=unread_messages, message=message, received=True)
        else:
            cur.execute('''SELECT * FROM messages JOIN users WHERE messages.recipient_id=users.user_id and messages.id = %s''', [id])
            message = cur.fetchone()
            return render_template('dashboard/read_message.html', data=data, unread_messages=unread_messages, message=message, received=False)

@app.route('/dashboard/duties')
@is_logged
def duties():
    data = get_user_data()
    sent, received = get_messages()
    unread_messages = get_unread_messages()
    return render_template("dashboard/duties.html", data=data, received=received, unread_messages=unread_messages)

@app.route('/dashboard/academic_result')
@is_logged
def academic_results():
    data = get_user_data()
    unread_messages = get_unread_messages()
    return render_template("dashboard/acares.html", data=data, unread_messages=unread_messages)

@app.route('/dashboard/classes')
@is_logged
def classes():
    data = get_user_data()
    unread_messages = get_unread_messages()
    return render_template("dashboard/classes.html", data=data, unread_messages=unread_messages)

@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == "POST":
        # Taking the Form data
        student_id = request.form['student_id']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']
        # Checking Password is matched
        if password == confirm:
            # Hashing User's Password using SHA256-bit
            hased_password = sha256_crypt.encrypt(password)
            # Creating Connection to the Database
            cur = mysql.connection.cursor()
            # Checking if the user is in the Database
            cur.execute('''SELECT * FROM students_db WHERE student_id = %s''', [student_id])
            db_result = cur.fetchone()
            # If there is actual student with such ID
            if db_result:
                # Checking if the user is already registerd
                cur.execute('''SELECT * FROM reg_students WHERE student_id = %s''', [student_id])
                student_result = cur.fetchone()
                # if student's already registerd
                if student_result:
                    flash("You're registerd Already. Please Loing.", "warning")
                # insrting student's data into the database
                else:
                    cur.execute('''INSERT INTO reg_students (student_id, email, password) VALUES (%s, %s, %s)''', (student_id, email, hased_password))
                    cur.execute('''INSERT INTO users (user_id, firstname, lastname, role,facultyAndDepartment, yearAndSemester) VALUES (%s, %s, %s, %s, %s, %s)'''\
                                 ,[db_result['student_id'], db_result['firstname'], db_result['lastname'], "Student", db_result['faculty'] + "/" + db_result['department'], db_result['year'] + "/" + db_result['semester']])
                    cur.execute('''INSERT INTO messages (title, sender_id, recipient_id, message, read_status) VALUES (%s, %s, %s, %s,%s)'''\
                                 ,["ABC University - Welcome!", 111111, db_result['student_id'], helpers.abc_welcome_message, False])
                    # commiting changes to the Database and closing connection
                    mysql.connection.commit()
                    cur.close()
                    flash("You've successfuly registerd, You Can Login Now.", "success")
                    return redirect(url_for('index'))
            # There's no student with such ID
            else:
                flash("There's No student with such ID. Please check the ID Number.", "warning")
        else:
            flash("Password Doesn't Match, Try Again", "warning")
    return render_template('register/register_student.html')

@app.route('/register/professor', methods=['GET', 'POST'])
def register_professor():
    if request.method == "POST":
        # Taking the Form data
        staff_id = request.form['staff_id']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']
        # Checking Password is matched
        if password == confirm:
            # Hashing User's Password using SHA256-bit
            hased_password = sha256_crypt.encrypt(password)
            # Creating Connection to the Database
            cur = mysql.connection.cursor()
            # Checking if the user is in the Database
            cur.execute('''SELECT * FROM professordb WHERE staff_id = %s''', [staff_id])
            db_result = cur.fetchone()
            # If there is actual professor with such ID
            if db_result:
                # Checking if the user is already registerd
                cur.execute('''SELECT * FROM professors WHERE staff_id = %s''', [staff_id])
                professor_result = cur.fetchone()
                # if professor's already registerd
                if professor_result:
                    flash("You're registerd Already. Please Loing.", "warning")
                # insrting professor's data into the database
                else:
                    cur.execute('''INSERT INTO professors (staff_id, email, password) VALUES (%s, %s, %s)''', (staff_id, email, hased_password))
                    # commiting changes to the Database and closing connection
                    mysql.connection.commit()
                    cur.close()
                    flash("You've successfuly registerd, You Can Login Now.", "success")
                    return redirect(url_for('index'))
            # There's no professor with such ID
            else:
                flash("There's no professor with such ID. Please check the ID Number.", "warning")
        else:
            flash("Passwords Doen't Match, Try Again", "warning")
    return render_template('register/register_professor.html')

@app.route('/register/employee', methods=['GET', 'POST'])
def register_worker():
    if request.method == "POST":
        # Taking the Form data
        staff_id = request.form['staff_id']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']
        # Checking Password is matched
        if password == confirm:
            # Hashing User's Password using SHA256-bit
            hashed_password = sha256_crypt.encrypt(password)
            # Creating Connection to the Database
            cur = mysql.connection.cursor()
            # Checking if the user is in the Database
            cur.execute('''SELECT * FROM employees_db WHERE staff_id = %s''', [staff_id])
            db_result = cur.fetchone()
            # If there is actual student with such ID
            if db_result:
                # Checking if the user is already registerd
                cur.execute('''SELECT * FROM reg_employees WHERE staff_id = %s''', [staff_id])
                employee_result = cur.fetchone()
                # if student's already registerd
                if employee_result:
                    flash("You're registerd Already. Please Loing.", "warning")
                # insrting student's data into the database
                else:
                    cur.execute('''INSERT INTO reg_employees (staff_id, email, password) VALUES (%s, %s, %s)''', (staff_id, email, hashed_password))
                    cur.execute('''INSERT INTO users (user_id, firstname, lastname, role, job) VALUES (%s, %s, %s, %s, %s)'''\
                                 ,[db_result['staff_id'], db_result['firstname'], db_result['lastname'], "Employee", db_result['job']])
                    # commiting changes to the Database and closing connection
                    mysql.connection.commit()
                    cur.close()
                    flash("You've successfuly registerd, You Can Login Now.", "success")
                    return redirect(url_for('index'))
            # There's no student with such ID
            else:
                flash("There's No Employee with such ID. Please check the ID Number.", "warning")
        else:
            flash("Password Doesn't Match, Try Again", "warning")
    return render_template('register/register_worker.html')

if __name__ == "__main__":
    app.run(debug=True)