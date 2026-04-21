-- SQL Lab Platform Database Schema
-- Compatible with MySQL 5.7+ and MySQL 8.0+

-- Note: Database 'if0_41654374_sql_lab' already exists on InfinityFree

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
    INDEX idx_expires (expires_at),
    FOREIGN KEY (email) REFERENCES users(email) ON DELETE CASCADE
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

-- Student Data table (for tracking student-created tables)
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

-- Sample tables for students to practice with
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    department VARCHAR(100),
    enrollment_year INT,
    gpa DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    credits INT DEFAULT 3,
    department VARCHAR(100),
    instructor VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

-- Insert sample data for students
INSERT INTO students (first_name, last_name, email, department, enrollment_year, gpa) VALUES
('Ahmed', 'Khan', 'ahmed.khan@iobm.edu.pk', 'Computer Science', 2023, 3.75),
('Fatima', 'Ali', 'fatima.ali@iobm.edu.pk', 'Business Administration', 2022, 3.90),
('Muhammad', 'Hassan', 'muhammad.hassan@iobm.edu.pk', 'Computer Science', 2023, 3.50),
('Ayesha', ' Malik', 'ayesha.malik@iobm.edu.pk', 'Data Science', 2024, 3.80),
('Ali', 'Raza', 'ali.raza@iobm.edu.pk', 'Computer Science', 2022, 3.65),
('Zainab', 'Bibi', 'zainab.bibi@iobm.edu.pk', 'Marketing', 2023, 3.45),
('Usman', 'Gul', 'usman.gul@iobm.edu.pk', 'Finance', 2024, 3.70),
('Hira', 'Shahid', 'hira.shahid@iobm.edu.pk', 'Computer Science', 2023, 3.95);

INSERT INTO courses (course_code, course_name, credits, department, instructor) VALUES
('CS101', 'Introduction to Programming', 4, 'Computer Science', 'Dr. Ahmad'),
('CS201', 'Data Structures', 4, 'Computer Science', 'Dr. Fatima'),
('CS301', 'Database Systems', 3, 'Computer Science', 'Dr. Hassan'),
('BUS101', 'Principles of Management', 3, 'Business Administration', 'Prof. Sarah'),
('MKT201', 'Digital Marketing', 3, 'Marketing', 'Prof. John'),
('FIN301', 'Financial Accounting', 3, 'Finance', 'Dr. Khan');

INSERT INTO enrollments (student_id, course_id, grade, semester) VALUES
(1, 1, 'A', 'Fall 2023'),
(1, 2, 'A-', 'Spring 2024'),
(2, 4, 'A', 'Fall 2023'),
(2, 5, 'A+', 'Spring 2024'),
(3, 1, 'B+', 'Fall 2023'),
(3, 2, 'B', 'Spring 2024'),
(4, 1, 'A', 'Fall 2024'),
(5, 1, 'A-', 'Fall 2022'),
(5, 2, 'B+', 'Spring 2023'),
(5, 3, 'A', 'Fall 2023'),
(6, 4, 'B', 'Fall 2023'),
(7, 6, 'A-', 'Fall 2024'),
(8, 1, 'A+', 'Fall 2023'),
(8, 2, 'A', 'Spring 2024');

-- Create admin user (password: admin123 - should be changed immediately)
-- Password hash generated with bcrypt (cost factor 12)
-- INSERT INTO users (name, email, password, role, is_verified) 
-- VALUES ('Administrator', 'admin@iobm.edu.pk', '$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.X4.X4.X4.X4.X4', 'admin', TRUE);

-- Cleanup procedure for expired OTPs
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS cleanup_expired_otps()
BEGIN
    DELETE FROM otp_codes WHERE expires_at < NOW();
END //
DELIMITER ;

-- Event to run cleanup daily
CREATE EVENT IF NOT EXISTS cleanup_otp_event
ON SCHEDULE EVERY 1 DAY
DO CALL cleanup_expired_otps();

-- Create views for admin dashboard
CREATE OR REPLACE VIEW student_summary AS
SELECT 
    u.id,
    u.name,
    u.email,
    u.created_at,
    COUNT(DISTINCT ql.id) as total_queries,
    SUM(CASE WHEN ql.status = 'success' THEN 1 ELSE 0 END) as successful_queries,
    SUM(CASE WHEN ql.status = 'error' THEN 1 ELSE 0 END) as failed_queries,
    AVG(ql.execution_time_ms) as avg_execution_time
FROM users u
LEFT JOIN query_logs ql ON u.id = ql.user_id
WHERE u.role = 'student'
GROUP BY u.id, u.name, u.email, u.created_at;

-- Grant appropriate permissions (for production)
-- CREATE USER IF NOT EXISTS 'sqllab_app'@'%' IDENTIFIED BY 'strong_password_here';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON sql_lab.* TO 'sqllab_app'@'%';
-- FLUSH PRIVILEGES;
