-- =====================================================
-- SQL LAB - COMPLETE DATABASE SETUP
-- All SQL Topics for Students
-- =====================================================

-- =====================================================
-- 1. CREATE TABLES
-- =====================================================

-- Students Table
CREATE TABLE IF NOT EXISTS students (
    student_id INT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    dob DATE,
    gpa DECIMAL(3,2),
    enrollment_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'active'
);

-- Courses Table
CREATE TABLE IF NOT EXISTS courses (
    course_id INT PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    credits INT DEFAULT 3,
    department VARCHAR(50),
    instructor VARCHAR(100),
    fee DECIMAL(10,2)
);

-- Enrollments Table (for JOINs)
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    course_id INT,
    grade VARCHAR(2),
    semester VARCHAR(20),
    enrolled_date DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- Employees Table (for more examples)
CREATE TABLE IF NOT EXISTS employees (
    emp_id INT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20),
    hire_date DATE,
    salary DECIMAL(10,2),
    department VARCHAR(50),
    manager_id INT
);

-- Departments Table
CREATE TABLE IF NOT EXISTS departments (
    dept_id INT PRIMARY KEY,
    dept_name VARCHAR(50),
    location VARCHAR(50)
);

-- Products Table (for DML examples)
CREATE TABLE IF NOT EXISTS products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    category VARCHAR(50),
    price DECIMAL(10,2),
    stock INT,
    created_date DATE DEFAULT CURRENT_DATE
);

-- Sample Data - Students
INSERT INTO students (student_id, first_name, last_name, email, dob, gpa, enrollment_date) VALUES
(1, 'Ali', 'Ahmed', 'ali@iobm.edu.pk', '2002-03-15', 3.75, '2023-09-01'),
(2, 'Sara', 'Khan', 'sara@iobm.edu.pk', '2001-07-22', 3.90, '2022-09-01'),
(3, 'Bilal', 'Hassan', 'bilal@iobm.edu.pk', '2000-11-05', 2.85, '2021-09-01'),
(4, 'Fatima', 'Ali', 'fatima@iobm.edu.pk', '2003-01-30', 3.90, '2023-09-01'),
(5, 'Usman', 'Raza', 'usman@iobm.edu.pk', '2001-09-10', 3.50, '2022-09-01'),
(6, 'Aisha', 'Malik', 'aisha@iobm.edu.pk', '2002-06-18', 3.25, '2023-09-01'),
(7, 'Omer', 'Farooq', 'omer@iobm.edu.pk', '2000-02-28', 3.00, '2021-09-01'),
(8, 'Hira', 'Nawaz', 'hira@iobm.edu.pk', '2003-04-12', 3.80, '2023-09-01'),
(9, 'Zain', 'Abbas', 'zain@iobm.edu.pk', '2001-12-25', 3.15, '2022-09-01'),
(10, 'Mariam', 'Saeed', 'mariam@iobm.edu.pk', '2002-08-08', 3.65, '2023-09-01');

-- Sample Data - Courses
INSERT INTO courses (course_id, course_code, course_name, credits, department, instructor, fee) VALUES
(1, 'CS101', 'Introduction to Programming', 4, 'Computer Science', 'Dr. Ahmad', 15000),
(2, 'CS201', 'Data Structures', 4, 'Computer Science', 'Dr. Fatima', 16000),
(3, 'CS301', 'Database Systems', 3, 'Computer Science', 'Dr. Hassan', 14000),
(4, 'MATH101', 'Calculus I', 4, 'Mathematics', 'Dr. Qadir', 12000),
(5, 'MATH201', 'Linear Algebra', 3, 'Mathematics', 'Dr. Raza', 11000),
(6, 'ENG101', 'English Composition', 3, 'English', 'Ms. Sara', 8000),
(7, 'ECO101', 'Principles of Economics', 3, 'Business', 'Dr. Khan', 10000);

-- Sample Data - Enrollments
INSERT INTO enrollments (student_id, course_id, grade, semester) VALUES
(1, 1, 'A', 'Fall 2023'),
(1, 2, 'A-', 'Fall 2023'),
(1, 4, 'B+', 'Spring 2024'),
(2, 1, 'A', 'Fall 2023'),
(2, 3, 'A', 'Fall 2023'),
(2, 7, 'A-', 'Spring 2024'),
(3, 1, 'B', 'Fall 2023'),
(3, 2, 'B+', 'Spring 2024'),
(4, 1, 'A', 'Fall 2023'),
(4, 2, 'A', 'Fall 2023'),
(4, 3, 'A', 'Spring 2024'),
(5, 3, 'B+', 'Fall 2023'),
(5, 6, 'A-', 'Spring 2024'),
(6, 1, 'B+', 'Fall 2023'),
(7, 2, 'C', 'Spring 2024'),
(8, 1, 'A', 'Fall 2023'),
(8, 4, 'A', 'Spring 2024'),
(9, 7, 'B', 'Fall 2023'),
(10, 1, 'A-', 'Fall 2023');

-- Sample Data - Employees
INSERT INTO employees (emp_id, first_name, last_name, email, phone, hire_date, salary, department, manager_id) VALUES
(1, ' Ahmad', 'Khan', 'ahmad@company.com', '03001234567', '2020-01-15', 150000, 'IT', NULL),
(2, 'Fatima', 'Ali', 'fatima@company.com', '03001234568', '2020-03-20', 120000, 'IT', 1),
(3, 'Hassan', 'Raza', 'hassan@company.com', '03001234569', '2021-06-10', 100000, 'HR', NULL),
(4, 'Sara', 'Malik', 'sara@company.com', '03001234570', '2021-09-01', 90000, 'HR', 3),
(5, 'Ali', 'Butt', 'ali@company.com', '03001234571', '2022-01-05', 80000, 'Finance', NULL),
(6, 'Aisha', 'Javed', 'aisha@company.com', '03001234572', '2022-04-15', 75000, 'Finance', 5),
(7, 'Omer', 'Syed', 'omer@company.com', '03001234573', '2023-02-01', 60000, 'Marketing', NULL),
(8, 'Zain', 'Akhtar', 'zain@company.com', '03001234574', '2023-05-10', 55000, 'Marketing', 7);

-- Sample Data - Departments
INSERT INTO departments (dept_id, dept_name, location) VALUES
(1, 'IT', 'Building A - Floor 1'),
(2, 'HR', 'Building A - Floor 2'),
(3, 'Finance', 'Building B - Floor 1'),
(4, 'Marketing', 'Building B - Floor 2');

-- Sample Data - Products
INSERT INTO products (product_id, product_name, category, price, stock) VALUES
(1, 'Laptop', 'Electronics', 75000, 50),
(2, 'Mouse', 'Electronics', 1500, 200),
(3, 'Keyboard', 'Electronics', 3500, 150),
(4, 'Monitor', 'Electronics', 25000, 75),
(5, 'Desk', 'Furniture', 15000, 30),
(6, 'Chair', 'Furniture', 8000, 60),
(7, 'Table', 'Furniture', 20000, 25),
(8, 'Pencil', 'Stationery', 50, 1000),
(9, 'Notebook', 'Stationery', 100, 500),
(10, 'Pen', 'Stationery', 80, 800);

-- View for Student Grades
CREATE OR REPLACE VIEW student_grades_view AS
SELECT 
    s.student_id,
    CONCAT(s.first_name, ' ', s.last_name) AS student_name,
    c.course_name,
    e.grade,
    e.semester
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses c ON e.course_id = c.course_id;

-- View for Employee Hierarchy
CREATE OR REPLACE VIEW employee_hierarchy AS
SELECT 
    e.emp_id,
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    e.department,
    e.salary,
    m.first_name AS manager_name
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.emp_id;

SELECT 'Database Setup Complete!' AS message;