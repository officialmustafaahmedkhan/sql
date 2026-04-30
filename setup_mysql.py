import pymysql

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='admin')
c = conn.cursor()
c.execute('CREATE DATABASE IF NOT EXISTS sqllab')
print('Database sqllab created!')

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='admin', database='sqllab')
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS students (
    id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100) UNIQUE,
    department VARCHAR(50),
    enrollment_year INT,
    gpa FLOAT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    course_code VARCHAR(20) UNIQUE,
    course_name VARCHAR(100),
    credits INT DEFAULT 3,
    department VARCHAR(50),
    instructor VARCHAR(50)
)""")

c.execute("""CREATE TABLE IF NOT EXISTS enrollments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    course_id INT,
    grade VARCHAR(5),
    semester VARCHAR(20)
)""")

c.execute("""CREATE TABLE IF NOT EXISTS query_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    query_text TEXT,
    query_type VARCHAR(50),
    execution_time_ms INT,
    rows_affected INT DEFAULT 0,
    status VARCHAR(20),
    error_message TEXT,
    timestamp DATETIME
)""")

c.execute('SELECT COUNT(*) FROM students')
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO students VALUES (1, 'Ahmed', 'Khan', 'ahmed@iobm.edu.pk', 'CS', 2023, 3.75)")
    c.execute("INSERT INTO students VALUES (2, 'Fatima', 'Ali', 'fatima@iobm.edu.pk', 'Business', 2022, 3.90)")
    c.execute("INSERT INTO students VALUES (3, 'Muhammad', 'Hassan', 'hassan@iobm.edu.pk', 'CS', 2023, 3.50)")
    c.execute("INSERT INTO courses VALUES (1, 'CS101', 'Intro to Programming', 4, 'CS', 'Dr. Ahmad')")
    c.execute("INSERT INTO courses VALUES (2, 'CS201', 'Data Structures', 4, 'CS', 'Dr. Fatima')")
    c.execute("INSERT INTO courses VALUES (3, 'CS301', 'Database Systems', 3, 'CS', 'Dr. Hassan')")
    conn.commit()
    print('Sample data inserted!')

c.execute('SHOW TABLES')
print('Tables:', [r[0] for r in c.fetchall()])
conn.close()
print('Done!')
