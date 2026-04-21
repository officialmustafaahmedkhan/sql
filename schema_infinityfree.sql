-- SQL Lab Platform Database Schema
-- For InfinityFree Hosting

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('student', 'admin') DEFAULT 'student',
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_verified (is_verified)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- OTP Codes table
CREATE TABLE IF NOT EXISTS otp_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    otp VARCHAR(6) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Query Logs table
CREATE TABLE IF NOT EXISTS query_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    query_text TEXT NOT NULL,
    query_type VARCHAR(20) NOT NULL,
    execution_time_ms INT DEFAULT NULL,
    rows_affected INT DEFAULT 0,
    status ENUM('success', 'error') NOT NULL,
    error_message TEXT DEFAULT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Student Data table
CREATE TABLE IF NOT EXISTS student_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    UNIQUE KEY unique_user_table (user_id, table_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample Practice Tables
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    department VARCHAR(100),
    enrollment_year INT,
    gpa DECIMAL(3,2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    credits INT DEFAULT 3,
    department VARCHAR(100),
    instructor VARCHAR(100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS enrollments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    grade VARCHAR(2),
    semester VARCHAR(20),
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_enrollment (student_id, course_id, semester)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample data
INSERT INTO students (first_name, last_name, email, department, enrollment_year, gpa) VALUES
('Ahmed', 'Khan', 'ahmed.khan@iobm.edu.pk', 'Computer Science', 2023, 3.75),
('Fatima', 'Ali', 'fatima.ali@iobm.edu.pk', 'Business Administration', 2022, 3.90),
('Muhammad', 'Hassan', 'muhammad.hassan@iobm.edu.pk', 'Computer Science', 2023, 3.50),
('Ayesha', 'Malik', 'ayesha.malik@iobm.edu.pk', 'Data Science', 2024, 3.80),
('Ali', 'Raza', 'ali.raza@iobm.edu.pk', 'Computer Science', 2022, 3.65);

INSERT INTO courses (course_code, course_name, credits, department, instructor) VALUES
('CS101', 'Introduction to Programming', 4, 'Computer Science', 'Dr. Ahmad'),
('CS201', 'Data Structures', 4, 'Computer Science', 'Dr. Fatima'),
('CS301', 'Database Systems', 3, 'Computer Science', 'Dr. Hassan'),
('BUS101', 'Principles of Management', 3, 'Business Administration', 'Prof. Sarah');

INSERT INTO enrollments (student_id, course_id, grade, semester) VALUES
(1, 1, 'A', 'Fall 2023'),
(1, 2, 'A-', 'Spring 2024'),
(2, 4, 'A', 'Fall 2023'),
(3, 1, 'B+', 'Fall 2023'),
(3, 2, 'B', 'Spring 2024'),
(4, 1, 'A', 'Fall 2024'),
(5, 1, 'A-', 'Fall 2022'),
(5, 2, 'B+', 'Spring 2023'),
(5, 3, 'A', 'Fall 2023');
