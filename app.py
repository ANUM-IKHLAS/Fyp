from flask import Flask, render_template, request, redirect, url_for, make_response  # Added make_response
from flask_mysqldb import MySQL
import MySQLdb.cursors

# Initialize Flask app
app = Flask(__name__)

# Configure MySQL connection (XAMPP settings)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # Default MySQL username in XAMPP
app.config['MYSQL_PASSWORD'] = ''  # Default password for MySQL in XAMPP
app.config['MYSQL_DB'] = 'timetable_attendance'  # Database name

# Initialize MySQL
mysql = MySQL(app)

# Home route - Redirect to dashboard
@app.route('/')
def home():
    return redirect(url_for('dashboard'))

# Route for the index page
@app.route('/index')
def index():
    return redirect(url_for('dashboard'))  # Redirect to the dashboard

# Route for the dashboard
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# -------------------- Departments --------------------

# Route to list departments
@app.route('/departments')
def list_departments():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.close()
    print(f"Fetched departments: {departments}")  # Debugging log
    return render_template('departments/list_departments.html', departments=departments)

# Route to add a new department
@app.route('/departments/add', methods=['GET', 'POST'])
def add_department():
    if request.method == 'POST':
        department_name = request.form['DepartmentName']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO departments (DepartmentName) VALUES (%s)", (department_name,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_departments'))  # Redirect to the department list after adding
    return render_template('departments/add_department.html')

# Route to update a department
@app.route('/departments/update/<int:id>', methods=['GET', 'POST'])
def update_department(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM departments WHERE DepartmentID = %s", (id,))
    department = cur.fetchone()
    if request.method == 'POST':
        department_name = request.form['DepartmentName']
        cur.execute("UPDATE departments SET DepartmentName = %s WHERE DepartmentID = %s", (department_name, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_departments'))
    cur.close()
    return render_template('departments/update_department.html', department=department)

# Route to delete a department
@app.route('/departments/delete/<int:id>', methods=['POST'])
def delete_department(id):
    try:
        cur = mysql.connection.cursor()
        
        # Check for dependent records in related tables
        cur.execute("SELECT COUNT(*) AS count FROM faculty WHERE DepartmentID = %s", (id,))
        faculty_count = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) AS count FROM courses WHERE DepartmentID = %s", (id,))
        courses_count = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) AS count FROM students WHERE DepartmentID = %s", (id,))
        students_count = cur.fetchone()['count']

        if faculty_count > 0 or courses_count > 0 or students_count > 0:
            return "Error: Cannot delete department. It has dependent records in faculty, courses, or students.", 400

        # Delete the department
        cur.execute("DELETE FROM departments WHERE DepartmentID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_departments'))  # Redirect to the department list after deletion
    except Exception as e:
        print(f"Error deleting department: {e}")
        return "An error occurred while deleting the department.", 500

# -------------------- Faculty --------------------

# Route to list faculty
@app.route('/faculty')
def list_faculty():
    cur = mysql.connection.cursor()
    cur.execute("SELECT f.FacultyID, f.FirstName, f.LastName, f.Email, d.DepartmentName FROM faculty f LEFT JOIN departments d ON f.DepartmentID = d.DepartmentID")
    faculty_members = cur.fetchall()
    cur.close()
    return render_template('faculty/list_faculty.html', faculty_members=faculty_members)

# Route to add a new faculty
@app.route('/faculty/add', methods=['GET', 'POST'])
def add_faculty():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        first_name = request.form['FirstName']
        last_name = request.form['LastName']
        email = request.form['Email']
        department_id = request.form['DepartmentID']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO faculty (FirstName, LastName, Email, DepartmentID) VALUES (%s, %s, %s, %s)", (first_name, last_name, email, department_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_faculty'))
    return render_template('faculty/add_faculty.html', departments=departments)

# Route to update a faculty
@app.route('/faculty/update/<int:id>', methods=['GET', 'POST'])
def update_faculty(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM faculty WHERE FacultyID = %s", (id,))
    faculty = cur.fetchone()
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        first_name = request.form['FirstName']
        last_name = request.form['LastName']
        email = request.form['Email']
        department_id = request.form['DepartmentID']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE faculty SET FirstName = %s, LastName = %s, Email = %s, DepartmentID = %s WHERE FacultyID = %s", (first_name, last_name, email, department_id, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_faculty'))
    return render_template('faculty/update_faculty.html', faculty=faculty, departments=departments)

# Route to delete a faculty
@app.route('/faculty/delete/<int:id>', methods=['POST'])
def delete_faculty(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM faculty WHERE FacultyID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_faculty'))
    except Exception as e:
        print(f"Error deleting faculty: {e}")
        return "An error occurred while deleting the faculty.", 500

# -------------------- Courses --------------------

# Route to list courses
@app.route('/courses')
def list_courses():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor
    cur.execute("SELECT c.CourseID, c.CourseName, d.DepartmentName, f.FirstName, f.LastName FROM courses c LEFT JOIN departments d ON c.DepartmentID = d.DepartmentID LEFT JOIN faculty f ON c.FacultyID = f.FacultyID")
    courses = cur.fetchall()
    cur.close()
    return render_template('courses/list_courses.html', courses=courses)

# Route to add a new course
@app.route('/courses/add', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        try:
            course_name = request.form['CourseName']
            department_id = request.form['DepartmentID']
            faculty_id = request.form['FacultyID']
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO courses (CourseName, DepartmentID, FacultyID) VALUES (%s, %s, %s)", (course_name, department_id, faculty_id))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('list_courses'))  # Redirect to the course list after adding
        except Exception as e:
            print(f"Error adding course: {e}")
            return "An error occurred while adding the course.", 500

    # Fetch updated list of departments and faculty
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor
    cur.execute("SELECT DepartmentID, DepartmentName FROM departments")
    departments = cur.fetchall()
    cur.execute("SELECT FacultyID, FirstName, LastName FROM faculty")
    faculty = cur.fetchall()
    cur.close()
    return render_template('courses/add_course.html', departments=departments, faculty=faculty)

# Route to update a course
@app.route('/courses/update/<int:id>', methods=['GET', 'POST'])
def update_course(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor
    cur.execute("SELECT * FROM courses WHERE CourseID = %s", (id,))
    course = cur.fetchone()
    cur.execute("SELECT DepartmentID, DepartmentName FROM departments")
    departments = cur.fetchall()
    cur.execute("SELECT FacultyID, FirstName, LastName FROM faculty")
    faculty = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        course_name = request.form['CourseName']
        department_id = request.form['DepartmentID']
        faculty_id = request.form['FacultyID']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE courses SET CourseName = %s, DepartmentID = %s, FacultyID = %s WHERE CourseID = %s", (course_name, department_id, faculty_id, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_courses'))
    return render_template('courses/update_course.html', course=course, departments=departments, faculty=faculty)

# Route to delete a course
@app.route('/courses/delete/<int:id>', methods=['POST'])
def delete_course(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM courses WHERE CourseID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_courses'))
    except Exception as e:
        print(f"Error deleting course: {e}")
        return "An error occurred while deleting the course.", 500

# Route to list enrolled students for a course
@app.route('/courses/enrolled_students/<int:course_id>')
def enrolled_students(course_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT s.StudentID, s.FirstName, s.LastName, s.EnrollmentNo, s.Email
        FROM EnrolledStudents es
        JOIN Students s ON es.StudentID = s.StudentID
        WHERE es.CourseID = %s
    """, (course_id,))
    students = cur.fetchall()
    cur.execute("SELECT CourseName FROM Courses WHERE CourseID = %s", (course_id,))
    course = cur.fetchone()
    cur.close()
    return render_template('courses/enrolled_students.html', students=students, course=course)

# -------------------- Students --------------------

# Route to list students
@app.route('/students')
def list_students():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor
    cur.execute("SELECT s.StudentID, s.FirstName, s.LastName, s.EnrollmentNo, s.Email, d.DepartmentName FROM students s LEFT JOIN departments d ON s.DepartmentID = d.DepartmentID")
    students = cur.fetchall()
    cur.close()
    return render_template('students/list_students.html', students=students)

# Route to add a new student
@app.route('/students/add', methods=['GET', 'POST'])
def add_student():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        first_name = request.form['FirstName']
        last_name = request.form['LastName']
        enrollment_no = request.form['EnrollmentNo']
        email = request.form['Email']
        department_id = request.form['DepartmentID']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO students (FirstName, LastName, EnrollmentNo, Email, DepartmentID) VALUES (%s, %s, %s, %s, %s)", (first_name, last_name, enrollment_no, email, department_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_students'))  # Redirect to the student list after adding
    return render_template('students/add_student.html', departments=departments)

# Route to update a student
@app.route('/students/update/<int:id>', methods=['GET', 'POST'])
def update_student(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM students WHERE StudentID = %s", (id,))
    student = cur.fetchone()
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        first_name = request.form['FirstName']
        last_name = request.form['LastName']
        enrollment_no = request.form['EnrollmentNo']
        email = request.form['Email']
        department_id = request.form['DepartmentID']
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE students
            SET FirstName = %s, LastName = %s, EnrollmentNo = %s, Email = %s, DepartmentID = %s
            WHERE StudentID = %s
        """, (first_name, last_name, enrollment_no, email, department_id, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_students'))
    return render_template('students/update_student.html', student=student, departments=departments)

# Route to delete a student
@app.route('/students/delete/<int:id>', methods=['POST'])
def delete_student(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM students WHERE StudentID = %s", (id,))  # Corrected column name
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_students'))
    except Exception as e:
        print(f"Error deleting student: {e}")
        return "An error occurred while deleting the student.", 500

# -------------------- Attendance --------------------

# Route to list attendance records
@app.route('/attendance')
def list_attendance():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT a.AttendanceID, s.FirstName, s.LastName, c.CourseName, a.AttendanceDate, a.AttendanceStatus
        FROM attendance a
        LEFT JOIN students s ON a.StudentID = s.StudentID
        LEFT JOIN courses c ON a.CourseID = c.CourseID
    """)  # Updated to use CourseID
    attendance_records = cur.fetchall()
    cur.close()
    return render_template('attendance/list_attendance.html', attendance_records=attendance_records)

# Route to add a new attendance record
@app.route('/attendance/add', methods=['GET', 'POST'])
def add_attendance():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.execute("SELECT * FROM courses")  # Ensure this query fetches the correct column names
    courses = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        student_id = request.form['StudentID']
        course_id = request.form['CourseID']  # Updated to 'CourseID'
        attendance_date = request.form['AttendanceDate']
        attendance_status = 'Present' if 'AttendanceStatus' in request.form else 'Absent'
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO attendance (StudentID, CourseID, AttendanceDate, AttendanceStatus) VALUES (%s, %s, %s, %s)", (student_id, course_id, attendance_date, attendance_status))  # Updated query
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_attendance'))  # Redirect to the attendance list after adding
    return render_template('attendance/add_attendance.html', students=students, courses=courses)

# Route to update an attendance record
@app.route('/attendance/update/<int:id>', methods=['GET', 'POST'])
def update_attendance(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM attendance WHERE AttendanceID = %s", (id,))
    attendance = cur.fetchone()
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.execute("SELECT * FROM courses")  # Ensure this query fetches the correct column names
    courses = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        student_id = request.form['StudentID']
        course_id = request.form['CourseID']  # Updated to 'CourseID'
        attendance_date = request.form['AttendanceDate']
        attendance_status = 'Present' if 'AttendanceStatus' in request.form else 'Absent'
        cur = mysql.connection.cursor()
        cur.execute("UPDATE attendance SET StudentID = %s, CourseID = %s, AttendanceDate = %s, AttendanceStatus = %s WHERE AttendanceID = %s", (student_id, course_id, attendance_date, attendance_status, id))  # Updated query
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_attendance'))
    return render_template('attendance/update_attendance.html', attendance=attendance, students=students, courses=courses)

# Route to delete an attendance record
@app.route('/attendance/delete/<int:id>', methods=['POST'])
def delete_attendance(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM attendance WHERE AttendanceID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_attendance'))
    except Exception as e:
        print(f"Error deleting attendance record: {e}")
        return "An error occurred while deleting the attendance record.", 500

# -------------------- Timetables --------------------

# Route to list timetables
@app.route('/timetables')
def list_timetables():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT t.TimetableID, c.CourseName, t.DayOfWeek, t.StartTime, t.EndTime, t.RoomNumber FROM timetables t LEFT JOIN courses c ON t.CourseID = c.CourseID")
    timetables = cur.fetchall()
    cur.close()
    return render_template('timetables/list_timetables.html', timetables=timetables)

# Route to add a new timetable
@app.route('/timetables/add', methods=['GET', 'POST'])
def add_timetable():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM courses")
    courses = cur.fetchall()
    cur.execute("SELECT FacultyID, CONCAT(FirstName, ' ', LastName) AS FullName FROM faculty")  # Fetch faculty names
    faculty = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        course_id = request.form['CourseID']
        day_of_week = request.form['DayOfWeek']
        start_time = request.form['StartTime']
        end_time = request.form['EndTime']
        room_number = request.form['RoomNumber']
        taught_by = request.form['TaughtBy']  # Foreign key (FacultyID)

        # Validate overlapping time slots for the teacher and the classroom
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT t.*
            FROM timetables t
            WHERE t.DayOfWeek = %s
            AND (
                (t.StartTime < t.EndTime AND (%s < t.EndTime AND %s > t.StartTime)) OR
                (t.StartTime > t.EndTime AND (%s < t.EndTime OR %s > t.StartTime))  -- Handle crossing midnight
            )
            AND (t.RoomNumber = %s OR t.TaughtBy = %s)
        """, (day_of_week, end_time, start_time, end_time, start_time, room_number, taught_by))
        conflict = cur.fetchone()
        cur.close()

        if conflict:
            return "Error: Time slot conflicts with an existing timetable entry for the same teacher or classroom.", 400

        # Insert new timetable entry
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO timetables (CourseID, DayOfWeek, StartTime, EndTime, RoomNumber, TaughtBy)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (course_id, day_of_week, start_time, end_time, room_number, taught_by))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_timetables'))
    return render_template('timetables/add_timetable.html', courses=courses, faculty=faculty)

# Route to update a timetable
@app.route('/timetables/update/<int:id>', methods=['GET', 'POST'])
def update_timetable(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM timetables WHERE TimetableID = %s", (id,))
    timetable = cur.fetchone()
    cur.execute("SELECT * FROM courses")
    courses = cur.fetchall()
    cur.execute("SELECT FacultyID, CONCAT(FirstName, ' ', LastName) AS FullName FROM faculty")  # Fetch faculty names
    faculty = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        course_id = request.form['CourseID']
        day_of_week = request.form['DayOfWeek']
        start_time = request.form['StartTime']
        end_time = request.form['EndTime']
        room_number = request.form['RoomNumber']
        taught_by = request.form['TaughtBy']  # Foreign key (FacultyID)

        # Validate overlapping time slots for the teacher and the classroom
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT t.*
            FROM timetables t
            WHERE t.DayOfWeek = %s
            AND (
                (t.StartTime < t.EndTime AND (%s < t.EndTime AND %s > t.StartTime)) OR
                (t.StartTime > t.EndTime AND (%s < t.EndTime OR %s > t.StartTime))  -- Handle crossing midnight
            )
            AND (t.RoomNumber = %s OR t.TaughtBy = %s)
            AND t.TimetableID != %s
        """, (day_of_week, end_time, start_time, end_time, start_time, room_number, taught_by, id))
        conflict = cur.fetchone()
        cur.close()

        if conflict:
            return "Error: Time slot conflicts with an existing timetable entry for the same teacher or classroom.", 400

        # Update timetable entry
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE timetables
            SET CourseID = %s, DayOfWeek = %s, StartTime = %s, EndTime = %s, RoomNumber = %s, TaughtBy = %s
            WHERE TimetableID = %s
        """, (course_id, day_of_week, start_time, end_time, room_number, taught_by, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_timetables'))
    return render_template('timetables/update_timetable.html', timetable=timetable, courses=courses, faculty=faculty)

# Route to delete a timetable
@app.route('/timetables/delete/<int:id>', methods=['POST'])
def delete_timetable(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM timetables WHERE TimetableID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_timetables'))
    except Exception as e:
        print(f"Error deleting timetable: {e}")
        return "An error occurred while deleting the timetable.", 500

# -------------------- Enrolled Students --------------------

# Route to list enrolled students
@app.route('/enrolled_students')
def list_enrolled_students():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT es.EnrollmentID, s.FirstName, s.LastName, c.CourseName
        FROM enrolledstudents es
        JOIN students s ON es.StudentID = s.StudentID
        JOIN courses c ON es.CourseID = c.CourseID
    """)  # Corrected column names
    enrolled_students = cur.fetchall()
    cur.close()
    return render_template('enrolled_students/list_enrolled_students.html', enrolled_students=enrolled_students)

# Route to add a new enrolled student
@app.route('/enrolled_students/add', methods=['GET', 'POST'])
def add_enrolled_student():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.execute("SELECT * FROM courses")
    courses = cur.fetchall()
    cur.execute("SELECT * FROM semesters")  # Added semesters for SemesterID
    semesters = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        student_id = request.form['StudentID']
        course_id = request.form['CourseID']
        semester_id = request.form['SemesterID']  # Added SemesterID
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO enrolledstudents (StudentID, CourseID, SemesterID) VALUES (%s, %s, %s)", (student_id, course_id, semester_id))  # Corrected query
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_enrolled_students'))
    return render_template('enrolled_students/add_enrolled_student.html', students=students, courses=courses, semesters=semesters)

# Route to delete an enrolled student
@app.route('/enrolled_students/delete/<int:id>', methods=['POST'])
def delete_enrolled_student(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM enrolledstudents WHERE EnrollmentID = %s", (id,))  # Corrected column name
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_enrolled_students'))
    except Exception as e:
        print(f"Error deleting enrolled student: {e}")
        return "An error occurred while deleting the enrolled student.", 500

# -------------------- Enrolled Teachers --------------------

# Route to list enrolled teachers
@app.route('/enrolled_teachers')
def list_enrolled_teachers():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT et.TeacherID, f.FirstName, f.LastName, c.CourseName
        FROM enrolledteachers et
        JOIN faculty f ON et.FacultyID = f.FacultyID
        JOIN courses c ON et.OfferedCourseID = c.CourseID
    """)
    enrolled_teachers = cur.fetchall()
    cur.close()
    return render_template('enrolled_teachers/list_enrolled_teachers.html', enrolled_teachers=enrolled_teachers)

# -------------------- Offered Courses --------------------

# Route to list offered courses
@app.route('/offered_courses')
def list_offered_courses():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT c.CourseID, c.CourseName, d.DepartmentName, f.FirstName, f.LastName
        FROM courses c
        JOIN departments d ON c.DepartmentID = d.DepartmentID
        JOIN faculty f ON c.FacultyID = f.FacultyID
    """)  # Corrected query
    offered_courses = cur.fetchall()
    cur.close()
    return render_template('offered_courses/list_offered_courses.html', offered_courses=offered_courses)

# -------------------- Semesters --------------------

# Route to list semesters
@app.route('/semesters')
def list_semesters():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM semesters")
    semesters = cur.fetchall()
    cur.close()
    return render_template('semesters/list_semesters.html', semesters=semesters)

# Route to add a new semester
@app.route('/semesters/add', methods=['GET', 'POST'])
def add_semester():
    if request.method == 'POST':
        semester_name = request.form['SemesterName']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO semesters (SemesterName) VALUES (%s)", (semester_name,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_semesters'))
    return render_template('semesters/add_semester.html')

# Route to update a semester
@app.route('/semesters/update/<int:id>', methods=['GET', 'POST'])
def update_semester(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM semesters WHERE SemesterID = %s", (id,))
    semester = cur.fetchone()
    cur.close()
    if request.method == 'POST':
        semester_name = request.form['SemesterName']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE semesters SET SemesterName = %s WHERE SemesterID = %s", (semester_name, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_semesters'))
    return render_template('semesters/update_semester.html', semester=semester)

# Route to delete a semester
@app.route('/semesters/delete/<int:id>', methods=['POST'])
def delete_semester(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM semesters WHERE SemesterID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_semesters'))
    except Exception as e:
        print(f"Error deleting semester: {e}")
        return "An error occurred while deleting the semester.", 500

# -------------------- Sessions --------------------

# Route to list sessions
@app.route('/sessions')
def list_sessions():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM sessions")
    sessions = cur.fetchall()
    cur.close()
    return render_template('sessions/list_sessions.html', sessions=sessions)

# Route to add a new session
@app.route('/sessions/add', methods=['GET', 'POST'])
def add_session():
    if request.method == 'POST':
        start_year = request.form['StartYear']
        end_year = request.form['EndYear']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO sessions (StartYear, EndYear) VALUES (%s, %s)", (start_year, end_year))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_sessions'))
    return render_template('sessions/add_session.html')

# Route to update a session
@app.route('/sessions/update/<int:id>', methods=['GET', 'POST'])
def update_session(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM sessions WHERE SessionID = %s", (id,))
    session = cur.fetchone()
    cur.close()
    if request.method == 'POST':
        start_year = request.form['StartYear']
        end_year = request.form['EndYear']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE sessions SET StartYear = %s, EndYear = %s WHERE SessionID = %s", (start_year, end_year, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_sessions'))
    return render_template('sessions/update_session.html', session=session)

# Route to delete a session
@app.route('/sessions/delete/<int:id>', methods=['POST'])
def delete_session(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM sessions WHERE SessionID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_sessions'))
    except Exception as e:
        print(f"Error deleting session: {e}")
        return "An error occurred while deleting the session.", 500

# -------------------- Offered Programs --------------------

# Route to list offered programs
@app.route('/offered_programs')
def list_offered_programs():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT op.ProgramID, op.ProgramName, s.StartYear, s.EndYear
        FROM offered_programs op
        JOIN sessions s ON op.SessionID = s.SessionID
    """)
    programs = cur.fetchall()
    cur.close()
    return render_template('offered_programs/list_offered_programs.html', programs=programs)

# Route to add a new offered program
@app.route('/offered_programs/add', methods=['GET', 'POST'])
def add_offered_program():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM sessions")
    sessions = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        program_name = request.form['ProgramName']
        session_id = request.form['SessionID']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO offered_programs (ProgramName, SessionID) VALUES (%s, %s)", (program_name, session_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_offered_programs'))
    return render_template('offered_programs/add_offered_program.html', sessions=sessions)

# Route to update an offered program
@app.route('/offered_programs/update/<int:id>', methods=['GET', 'POST'])
def update_offered_program(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM offered_programs WHERE ProgramID = %s", (id,))
    program = cur.fetchone()
    cur.execute("SELECT * FROM sessions")
    sessions = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        program_name = request.form['ProgramName']
        session_id = request.form['SessionID']
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE offered_programs
            SET ProgramName = %s, SessionID = %s
            WHERE ProgramID = %s
        """, (program_name, session_id, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_offered_programs'))
    return render_template('offered_programs/update_offered_program.html', program=program, sessions=sessions)

# Route to delete an offered program
@app.route('/offered_programs/delete/<int:id>', methods=['POST'])
def delete_offered_program(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM offered_programs WHERE ProgramID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_offered_programs'))
    except Exception as e:
        print(f"Error deleting offered program: {e}")
        return "An error occurred while deleting the offered program.", 500

# -------------------- Current Semester --------------------

# Route to list current semesters
@app.route('/current_semester')
def list_current_semester():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT cs.CurrentSemesterID, op.ProgramName, s.SemesterName, cs.StartDate, cs.EndDate
        FROM current_semester cs
        JOIN offered_programs op ON cs.ProgramID = op.ProgramID
        JOIN semesters s ON cs.SemesterID = s.SemesterID
    """)  # Fixed SQL query
    current_semesters = cur.fetchall()
    cur.close()
    return render_template('current_semester/list_current_semester.html', current_semesters=current_semesters)

# Route to add a new current semester
@app.route('/current_semester/add', methods=['GET', 'POST'])
def add_current_semester():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM offered_programs")
    programs = cur.fetchall()
    cur.execute("SELECT * FROM semesters")
    semesters = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        program_id = request.form['ProgramID']
        semester_id = request.form['SemesterID']
        start_date = request.form['StartDate']
        end_date = request.form['EndDate']
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO current_semester (ProgramID, SemesterID, StartDate, EndDate)
            VALUES (%s, %s, %s, %s)
        """, (program_id, semester_id, start_date, end_date))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_current_semester'))
    return render_template('current_semester/add_current_semester.html', programs=programs, semesters=semesters)

# Route to delete a current semester
@app.route('/current_semester/delete/<int:id>', methods=['POST'])
def delete_current_semester(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM current_semester WHERE CurrentSemesterID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_current_semester'))
    except Exception as e:
        print(f"Error deleting current semester: {e}")
        return "An error occurred while deleting the current semester.", 500

# -------------------- Assign Courses to Students --------------------

# Route to list assigned courses to students
@app.route('/assign_courses_to_student')
def list_assign_courses_to_student():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Fetch filter options
    cur.execute("SELECT ProgramID, ProgramName FROM offered_programs")
    programs = cur.fetchall()
    cur.execute("SELECT SessionID, StartYear, EndYear FROM sessions")
    sessions = cur.fetchall()
    cur.execute("""
        SELECT cs.CurrentSemesterID, op.ProgramName, s.SemesterName
        FROM current_semester cs
        JOIN offered_programs op ON cs.ProgramID = op.ProgramID
        JOIN semesters s ON cs.SemesterID = s.SemesterID
    """)
    current_semesters = cur.fetchall()

    # Get filter values from query string
    program_id = request.args.get('program_id')
    session_id = request.args.get('session_id')
    current_semester_id = request.args.get('current_semester_id')

    # Build dynamic WHERE clause
    where_clauses = []
    params = []
    if program_id:
        where_clauses.append("a.ProgramID = %s")
        params.append(program_id)
    if session_id:
        where_clauses.append("a.SessionID = %s")
        params.append(session_id)
    if current_semester_id:
        where_clauses.append("a.CurrentSemesterID = %s")
        params.append(current_semester_id)
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    query = f"""
        SELECT a.AssignID, s.FirstName, s.LastName, op.ProgramName, se.StartYear, se.EndYear,
               sem.SemesterName, c.CourseName
        FROM assign_courses_to_student a
        JOIN students s ON a.StudentID = s.StudentID
        JOIN offered_programs op ON a.ProgramID = op.ProgramID
        JOIN sessions se ON a.SessionID = se.SessionID
        JOIN current_semester cs ON a.CurrentSemesterID = cs.CurrentSemesterID
        JOIN semesters sem ON cs.SemesterID = sem.SemesterID
        JOIN courses c ON a.CourseID = c.CourseID
        {where_sql}
    """
    cur.execute(query, tuple(params))
    assignments = cur.fetchall()
    cur.close()
    return render_template(
        'assign_courses_to_student/list_assign_courses_to_student.html',
        assignments=assignments,
        programs=programs,
        sessions=sessions,
        current_semesters=current_semesters,
        selected_program_id=program_id,
        selected_session_id=session_id,
        selected_current_semester_id=current_semester_id
    )

# Route to assign a course to a student
@app.route('/assign_courses_to_student/add', methods=['GET', 'POST'])
def add_assign_courses_to_student():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.execute("SELECT op.ProgramID, op.ProgramName, op.SessionID, s.StartYear, s.EndYear FROM offered_programs op JOIN sessions s ON op.SessionID = s.SessionID")
    programs = cur.fetchall()
    cur.execute("SELECT * FROM courses")
    courses = cur.fetchall()
    cur.close()

    # For GET, show all current semesters (with program/session info for filtering in JS)
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT cs.CurrentSemesterID, cs.ProgramID, cs.SemesterID, op.ProgramName, s.SemesterName
        FROM current_semester cs
        JOIN offered_programs op ON cs.ProgramID = op.ProgramID
        JOIN semesters s ON cs.SemesterID = s.SemesterID
    """)
    current_semesters = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        student_id = request.form['StudentID']
        program_id = request.form['ProgramID']
        # Find session_id for the selected program
        session_id = None
        for p in programs:
            if str(p['ProgramID']) == str(program_id):
                session_id = p['SessionID']
                break
        current_semester_id = request.form['CurrentSemesterID']
        course_id = request.form['CourseID']
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO assign_courses_to_student
            (StudentID, ProgramID, SessionID, CurrentSemesterID, CourseID)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, program_id, session_id, current_semester_id, course_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_assign_courses_to_student'))
    return render_template(
        'assign_courses_to_student/add_assign_courses_to_student.html',
        students=students, programs=programs, current_semesters=current_semesters, courses=courses
    )

if __name__ == '__main__':
    print("Starting Flask application...")
    app.run(debug=True)
