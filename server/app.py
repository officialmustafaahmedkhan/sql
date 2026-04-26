import os
import re
import random
import string
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, 
    get_jwt_identity, get_jwt
)
import pymysql
import bcrypt
from dotenv import load_dotenv

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Load .env from the same directory as the script
load_dotenv(os.path.join(script_dir, '.env'))

app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'your-secret-key-change-this')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

CORS(app)
jwt = JWTManager(app)

# Email Configuration
RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
FROM_EMAIL = os.getenv('EMAIL_FROM', 'onboarding@resend.dev')
FROM_NAME = 'SQL Lab'

def send_email(to_email, subject, html_content):
    """Send email using Resend API"""
    try:
        import resend
        
        resend.api_key = RESEND_API_KEY
        
        params = {
            "from": f"{FROM_NAME} <{FROM_EMAIL}>",
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        response = resend.Emails.send(params)
        print(f"[EMAIL] Sent to {to_email}: {response}")
        return True
        
    except Exception as e:
        print(f"[EMAIL ERROR] {type(e).__name__}: {e}")
        return False

# =====================================================
# =====================================================
# Database Configuration - HYBRID Setup
# =====================================================
# Render: No DB vars → SQLite
# Laptop + Workbench: DB vars set → MySQL (if running)
# Laptop no Workbench: DB vars set → SQLite (auto fallback)
# =====================================================

db_host = os.getenv('DB_HOST', '')
db_user = os.getenv('DB_USER', '')
db_pass = os.getenv('DB_PASSWORD', '')
db_name = os.getenv('DB_NAME', '')

# Default to SQLite
USE_LOCAL_SQLITE = True

# Try MySQL only if credentials are provided
if db_host and db_user:
    try:
        import pymysql
        test_conn = pymysql.connect(
            host=db_host,
            port=int(os.getenv('DB_PORT', 3306)),
            user=db_user,
            password=db_pass,
            database=db_name,
            connect_timeout=2,
            ssl={'ssl_disabled': True}
        )
        test_conn.close()
        USE_LOCAL_SQLITE = False
        print("[DB] MySQL connected")
    except Exception as e:
        print(f"[DB] MySQL not available, using SQLite: {e}")
        USE_LOCAL_SQLITE = True
else:
    print("[DB] SQLite (no MySQL config)")

print(f"[DB] Mode: {'SQLite' if USE_LOCAL_SQLITE else 'MySQL'}")

# SQLite path for practice queries
SQL_DB_PATH = './sqllab.db'

# MySQL Configuration
DB_CONFIG = {
    'host': db_host,
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': db_user,
    'password': db_pass,
    'database': db_name,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'ssl': {'ssl_disabled': True}
}

# MySQL Configuration
DB_CONFIG = {
    'host': db_host,
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': db_user,
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', ''),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'ssl': {'ssl_disabled': True}
}

# Query Security Settings
QUERY_TIMEOUT_MS = int(os.getenv('QUERY_TIMEOUT_MS', 300))
MAX_ROWS = int(os.getenv('MAX_ROWS', 100))
ALLOWED_DOMAIN = os.getenv('ALLOWED_DOMAIN', '')

# =====================================================
# Dual Database Setup
# AUTH_DB = For User Authentication (SQLite)
# SQL_DB = For SQL Practice Queries (MySQL or SQLite)
# =====================================================

USE_LOCAL_SQLITE = os.getenv('USE_LOCAL_SQLITE', 'true').lower() == 'true'

# SQLite for Auth
AUTH_DB_PATH = os.getenv('AUTH_DB_PATH', './sqllab_auth.db')

# SQLite path for practice queries
SQL_DB_PATH = os.getenv('SQL_DB_PATH', './sqllab.db')

# SQL keywords to block (only for non-admin users)
DANGEROUS_KEYWORDS = [
    'INFORMATION_SCHEMA',
    'PERFORMANCE_SCHEMA',
]

# Full SQL statements allowed
ALLOWED_STATEMENTS = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 
                 'CREATE TABLE', 'CREATE DATABASE', 'CREATE VIEW',
                 'DROP TABLE', 'DROP DATABASE', 'DROP VIEW',
                 'ALTER', 'DESCRIBE', 'DESC', 'RENAME', 'TRUNCATE', 
                 'SHOW TABLES', 'SHOW COLUMNS', 'SHOW INDEX', 'SHOW DATABASES',
                 'USE',
                 'BEGIN', 'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'START TRANSACTION',
                 'GRANT', 'REVOKE',
                 'CALL', 'EXPLAIN', 'SOURCE']


def get_db():
    """Get database connection for SQL queries (SQLite or MySQL based on config)"""
    if USE_LOCAL_SQLITE:
        if 'sql_db' not in g:
            import sqlite3
            g.sql_db = sqlite3.connect(SQL_DB_PATH)
            g.sql_db.row_factory = sqlite3.Row
        return g.sql_db
    else:
        if 'db' not in g:
            g.db = pymysql.connect(**DB_CONFIG)
        return g.db

def get_auth_db():
    """Get SQLite connection for Auth database"""
    if 'auth_db' not in g:
        import sqlite3
        g.auth_db = sqlite3.connect(AUTH_DB_PATH)
    return g.auth_db


@app.teardown_appcontext
def close_db(exception):
    if USE_LOCAL_SQLITE:
        sql_db = g.pop('sql_db', None)
        if sql_db is not None:
            sql_db.close()
    else:
        db = g.pop('db', None)
        if db is not None:
            db.close()
    auth_db = g.pop('auth_db', None)
    if auth_db is not None:
        auth_db.close()


def init_database():
    """Initialize database tables"""
    import sqlite3
    
    # =====================================================
    # AUTH DATABASE (SQLite) - For User Management
    # =====================================================
    auth_db = sqlite3.connect(AUTH_DB_PATH)
    auth_cursor = auth_db.cursor()
    
    # Users table (SQLite)
    auth_cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            is_verified INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # OTP codes table (SQLite)
    auth_cursor.execute('''
        CREATE TABLE IF NOT EXISTS otp_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp TEXT NOT NULL,
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    auth_db.commit()
    auth_cursor.close()
    auth_db.close()
    print("Auth database initialized successfully!")
    
    # =====================================================
    # SQL QUERY DATABASE (SQLite) - For Practice Tables
    # =====================================================
    sql_db = sqlite3.connect(SQL_DB_PATH)
    sql_cursor = sql_db.cursor()
    
    if USE_LOCAL_SQLITE:
        # SQLite syntax
        sql_cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query_text TEXT NOT NULL,
                query_type TEXT NOT NULL,
                execution_time_ms INTEGER DEFAULT NULL,
                rows_affected INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                error_message TEXT DEFAULT NULL,
                timestamp DATETIME DEFAULT NULL
            )
        ''')
        
        sql_cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                department TEXT,
                enrollment_year INTEGER,
                gpa REAL
            )
        ''')
        
        sql_cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT UNIQUE NOT NULL,
                course_name TEXT NOT NULL,
                credits INTEGER DEFAULT 3,
                department TEXT,
                instructor TEXT
            )
        ''')
        
        sql_cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                grade TEXT,
                semester TEXT,
                enrolled_at DATETIME DEFAULT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (course_id) REFERENCES courses(id)
            )
        ''')
    else:
        # MySQL syntax
        sql_cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                query_text TEXT NOT NULL,
                query_type VARCHAR(20) NOT NULL,
                execution_time_ms INT DEFAULT NULL,
                rows_affected INT DEFAULT 0,
                status VARCHAR(20) NOT NULL,
                error_message TEXT DEFAULT NULL,
                timestamp DATETIME DEFAULT NULL
            )
        ''')
        
        sql_cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                department VARCHAR(100),
                enrollment_year INT,
                gpa DECIMAL(3,2)
            )
        ''')
        
        sql_cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                course_code VARCHAR(20) UNIQUE NOT NULL,
                course_name VARCHAR(100) NOT NULL,
                credits INT DEFAULT 3,
                department VARCHAR(100),
                instructor VARCHAR(100)
            )
        ''')
        
        sql_cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                course_id INT NOT NULL,
                grade VARCHAR(2),
                semester VARCHAR(20),
                enrolled_at DATETIME DEFAULT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (course_id) REFERENCES courses(id)
            )
        ''')
    
    # Insert sample data if empty
    sql_cursor.execute('SELECT COUNT(*) FROM students')
    students_count = sql_cursor.fetchone()[0]
    
    sql_cursor.execute('SELECT COUNT(*) FROM courses')
    courses_count = sql_cursor.fetchone()[0]
    
    if students_count == 0:
        sql_cursor.execute('''
            INSERT INTO students (first_name, last_name, email, department, enrollment_year, gpa) VALUES
            ('Ahmed', 'Khan', 'ahmed@iobm.edu.pk', 'Computer Science', 2023, 3.75),
            ('Fatima', 'Ali', 'fatima@iobm.edu.pk', 'Business Admin', 2022, 3.90),
            ('Muhammad', 'Hassan', 'hassan@iobm.edu.pk', 'Computer Science', 2023, 3.50)
        ''')
    
    if courses_count == 0:
        sql_cursor.execute('''
            INSERT INTO courses (course_code, course_name, credits, department, instructor) VALUES
            ('CS101', 'Introduction to Programming', 4, 'Computer Science', 'Dr. Ahmad'),
            ('CS201', 'Data Structures', 4, 'Computer Science', 'Dr. Fatima'),
            ('CS301', 'Database Systems', 3, 'Computer Science', 'Dr. Hassan')
        ''')
    
    if students_count > 0 and courses_count > 0:
        sql_cursor.execute('SELECT COUNT(*) FROM enrollments')
        if sql_cursor.fetchone()[0] == 0:
            sql_cursor.execute('''
                INSERT INTO enrollments (student_id, course_id, grade, semester) VALUES
                (1, 1, 'A', 'Fall 2023'),
                (2, 2, 'A-', 'Spring 2024'),
                (3, 1, 'B+', 'Fall 2023')
            ''')
    
    sql_db.commit()
    sql_cursor.close()
    print("Database initialized successfully!")


def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def validate_query(sql, is_admin=False):
    """Validate SQL query for security"""
    sql_upper = sql.upper().strip()
    words = sql_upper.split()
    first_word = words[0] if words else ''
    first_two = ' '.join(words[:2]) if len(words) >= 2 else first_word
    
    # Block system tables for students only
    blocked_keywords = ['INFORMATION_SCHEMA', 'PERFORMANCE_SCHEMA', 'MYSQL']
    if not is_admin:
        for keyword in blocked_keywords:
            if keyword in sql_upper:
                return False, f"Operation '{keyword}' is not allowed (admin only)"
    
    # All standard SQL statements + advanced
    allowed = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'REPLACE', 'REPLACE INTO',
              'CREATE TABLE', 'CREATE DATABASE', 'CREATE VIEW', 'CREATE INDEX', 'CREATE TRIGGER', 'CREATE FUNCTION', 'CREATE PROCEDURE',
              'DROP TABLE', 'DROP DATABASE', 'DROP VIEW', 'DROP INDEX', 'DROP TRIGGER', 'DROP FUNCTION', 'DROP PROCEDURE',
              'ALTER', 'DESCRIBE', 'DESC', 'RENAME', 'TRUNCATE', 'USE',
              'SHOW TABLES', 'SHOW COLUMNS', 'SHOW INDEX', 'SHOW DATABASES', 'SHOW CREATE',
              'BEGIN', 'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'START TRANSACTION',
              'GRANT', 'REVOKE',
              'CALL',
              'EXPLAIN', 'EXPLAIN QUERY PLAN',
              # Advanced querying
              'UNION', 'UNION ALL', 'EXCEPT', 'INTERSECT',
              'ORDER BY', 'GROUP BY', 'HAVING', 'LIMIT', 'OFFSET',
              'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'CROSS JOIN', 'NATURAL JOIN',
              'WHERE', 'AND', 'OR', 'NOT', 'IN', 'BETWEEN', 'LIKE', 'IS NULL', 'IS NOT NULL',
              # Aggregate functions
              'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP_CONCAT',
              # Case expressions
              'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
              'DISTINCT', 'ALL', 'ANY', 'EXISTS',
              # Window functions
              'ROW_NUMBER', 'RANK', 'DENSE_RANK', 'NTILE', 'LEAD', 'LAG', 'FIRST_VALUE', 'LAST_VALUE',
              'OVER', 'PARTITION BY', 'ROWS BETWEEN', 'RANGE BETWEEN',
              # CTEs and subqueries
              'WITH',
              # Stored procedures/functions
              'DECLARE', 'DELIMITER',
              # Other
              'AS', 'ON', 'NULL', 'NOT NULL', 'PRIMARY KEY', 'FOREIGN KEY', 'REFERENCES',
              'DEFAULT', 'AUTO_INCREMENT', 'UNIQUE', 'CHECK', 'CONSTRAINT',
              'IF', 'UNLESS']
    
    if first_word not in allowed and first_two not in allowed:
        return False, f"Statement '{first_word}' is not allowed"
    
    # Add LIMIT to SELECT queries (but not for window functions)
    if sql_upper.startswith('SELECT') and 'LIMIT' not in sql_upper and 'ROW_NUMBER()' not in sql_upper:
        sql = f"{sql.rstrip(';')} LIMIT {MAX_ROWS}"
    
    # Auto-add IF NOT EXISTS for CREATE statements
    create_stmts = ['CREATE TABLE', 'CREATE DATABASE', 'CREATE VIEW']
    for stmt in create_stmts:
        if sql_upper.startswith(stmt) and 'IF NOT EXISTS' not in sql_upper:
            sql = sql.replace(stmt, f'{stmt} IF NOT EXISTS', 1)
    
    return True, sql


# ==================== AUTH ROUTES ====================

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not all([name, email, password]):
        return jsonify({'error': 'All fields required'}), 400
    
    if ALLOWED_DOMAIN and not email.lower().endswith(ALLOWED_DOMAIN):
        return jsonify({'error': f'Only {ALLOWED_DOMAIN} emails allowed'}), 400
    
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    auth_db = get_auth_db()
    auth_cursor = auth_db.cursor()
    
    # Check if user exists
    auth_cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    if auth_cursor.fetchone():
        auth_cursor.close()
        return jsonify({'error': 'Email already registered'}), 409
    
    # Create user
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    auth_cursor.execute(
        'INSERT INTO users (name, email, password, is_verified) VALUES (?, ?, ?, ?)',
        (name, email, hashed, 0)
    )
    
    # Generate OTP
    otp = generate_otp()
    expires = datetime.now() + timedelta(minutes=5)
    
    auth_cursor.execute('DELETE FROM otp_codes WHERE email = ?', (email,))
    auth_cursor.execute(
        'INSERT INTO otp_codes (email, otp, expires_at) VALUES (?, ?, ?)',
        (email, otp, expires)
    )
    
    auth_db.commit()
    auth_cursor.close()
    
    # Send email with OTP
    email_sent = False
    try:
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333;">Welcome to SQL Lab!</h2>
            <p>Your verification code is:</p>
            <div style="background: #f4f4f4; padding: 20px; font-size: 32px; text-align: center; 
                        letter-spacing: 8px; border-radius: 8px; margin: 20px 0;">
                <strong>{otp}</strong>
            </div>
            <p>This code expires in <strong>5 minutes</strong>.</p>
            <p>If you didn't request this code, please ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">SQL Lab Platform - IOBM University</p>
        </body>
        </html>
        """
        print(f"Attempting to send email to {email}...")
        email_sent = send_email(email, "Your SQL Lab Verification Code", html_content)
        print(f"Email send result: {email_sent}")
    except Exception as e:
        print(f"Email sending failed: {type(e).__name__}: {e}")
    
    # Log OTP for development (console only - remove in production!)
    print(f"\n{'='*50}")
    print(f"OTP FOR TESTING: {otp}")
    print(f"Email: {email}")
    print(f"Email sent: {email_sent}")
    print(f"{'='*50}\n")
    
    return jsonify({
        'message': 'Signup successful. Please verify your email.',
        'email': email,
        'otp': otp,  # Remove this in production!
        'emailSent': email_sent
    }), 201


@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    
    if not all([email, otp]):
        return jsonify({'error': 'Email and OTP required'}), 400
    
    auth_db = get_auth_db()
    auth_cursor = auth_db.cursor()
    
    # Verify OTP
    auth_cursor.execute(
        'SELECT * FROM otp_codes WHERE email = ? AND otp = ? AND expires_at > datetime("now")',
        (email, otp)
    )
    otp_record = auth_cursor.fetchone()
    
    if not otp_record:
        auth_cursor.close()
        return jsonify({'error': 'Invalid or expired OTP'}), 400
    
    # Update user verification
    auth_cursor.execute('UPDATE users SET is_verified = 1 WHERE email = ?', (email,))
    auth_cursor.execute('DELETE FROM otp_codes WHERE email = ?', (email,))
    
    # Get user data
    auth_cursor.execute('SELECT id, name, email, role FROM users WHERE email = ?', (email,))
    user = auth_cursor.fetchone()
    
    auth_db.commit()
    auth_cursor.close()
    
    # Create token - SQLite returns tuple, not dict
    user_id = user[0]
    user_name = user[1]
    user_email = user[2]
    user_role = user[3]
    
    access_token = create_access_token(identity=str(user_id))
    
    return jsonify({
        'message': 'Email verified successfully',
        'token': access_token,
        'user': {
            'id': user_id,
            'name': user_name,
            'email': user_email,
            'role': user_role
        }
    })


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not all([email, password]):
        return jsonify({'error': 'Email and password required'}), 400
    
    auth_db = get_auth_db()
    auth_cursor = auth_db.cursor()
    
    auth_cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = auth_cursor.fetchone()
    auth_cursor.close()
    
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # SQLite returns tuple: (id, name, email, password, role, is_verified, created_at)
    user_id = user[0]
    user_name = user[1]
    user_email = user[2]
    user_password = user[3]
    user_role = user[4]
    user_verified = user[5]
    
    if not bcrypt.checkpw(password.encode(), user_password.encode()):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user_verified:
        return jsonify({
            'error': 'Please verify your email first',
            'requiresVerification': True,
            'email': user_email
        }), 403
    
    access_token = create_access_token(identity=str(user_id))
    
    return jsonify({
        'message': 'Login successful',
        'token': access_token,
        'user': {
            'id': user_id,
            'name': user_name,
            'email': user_email,
            'role': user_role
        }
    })


@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    
    auth_db = get_auth_db()
    auth_cursor = auth_db.cursor()
    auth_cursor.execute(
        'SELECT id, name, email, role, is_verified FROM users WHERE id = ?',
        (user_id,)
    )
    user = auth_cursor.fetchone()
    auth_cursor.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # SQLite tuple to dict
    return jsonify({
        'user': {
            'id': user[0],
            'name': user[1],
            'email': user[2],
            'role': user[3],
            'is_verified': user[4]
        }
    })


# ==================== QUERY ROUTES ====================

def split_queries(sql):
    """Split SQL by semicolon, keeping quoted strings intact"""
    queries = []
    current = []
    in_string = False
    string_char = None
    
    for char in sql:
        if char in ("'", '"') and (not in_string or string_char == char):
            if not in_string:
                string_char = char
            in_string = not in_string
        elif char == ';' and not in_string:
            query = ''.join(current).strip()
            if query:
                queries.append(query)
            current = []
            continue
        current.append(char)
    
    # Add last query if exists
    query = ''.join(current).strip()
    if query:
        queries.append(query)
    
    return queries

@app.route('/api/query/execute', methods=['POST'])
@jwt_required()
def execute_query():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    sql = data.get('query', '').strip()
    
    if not sql:
        return jsonify({'error': 'Query required'}), 400
    
    # Check if user is admin
    auth_db = get_auth_db()
    auth_cursor = auth_db.cursor()
    auth_cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
    user_row = auth_cursor.fetchone()
    is_admin = user_row and user_row[3] == 'admin'
    
    # Split queries by semicolon
    queries = split_queries(sql)
    all_results = []
    all_errors = []
    total_time = 0
    
    db = get_db()
    cursor = db.cursor()
    
    for idx, query in enumerate(queries):
        if not query.strip() or query.strip().startswith('--'):
            continue
            
        start_time = datetime.now()
        
        # Validate query with admin status
        is_valid, result = validate_query(query, is_admin)
        if not is_valid:
            all_errors.append({
                'query': query,
                'error': result,
                'queryType': 'BLOCKED'
            })
            continue
        
        query = result
        query_type = query.upper().split()[0]
        
        # Statements that return rows
        RESULT_STATEMENTS = ['SELECT', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN']
        
        try:
            cursor.execute(query)
            
            if query_type in RESULT_STATEMENTS:
                rows = cursor.fetchall()
                # Convert to dict for consistency
                if USE_LOCAL_SQLITE:
                    rows = [dict(row) for row in rows]
                result_data = {
                    'query': query,
                    'queryType': query_type,
                    'success': True,
                    'results': rows,
                    'rowsAffected': len(rows) if rows else 0,
                    'executionTime': int((datetime.now() - start_time).total_seconds() * 1000)
                }
            else:
                db.commit()
                result_data = {
                    'query': query,
                    'queryType': query_type,
                    'success': True,
                    'results': None,
                    'rowsAffected': cursor.rowcount,
                    'executionTime': int((datetime.now() - start_time).total_seconds() * 1000)
                }
            
            total_time += result_data['executionTime']
            all_results.append(result_data)
            
            # Log successful query
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if USE_LOCAL_SQLITE:
                cursor.execute('''
                    INSERT INTO query_logs (user_id, query_text, query_type, execution_time_ms, rows_affected, status, timestamp)
                    VALUES (?, ?, ?, ?, ?, 'success', ?)
                ''', (user_id, query, query_type, result_data['executionTime'], result_data['rowsAffected'], now))
            else:
                cursor.execute('''
                    INSERT INTO query_logs (user_id, query_text, query_type, execution_time_ms, rows_affected, status, timestamp)
                    VALUES (%s, %s, %s, %s, %s, 'success', %s)
                ''', (user_id, query, query_type, result_data['executionTime'], result_data['rowsAffected'], now))
            
        except Exception as e:
            error_msg = str(e)
            exec_time = int((datetime.now() - start_time).total_seconds() * 1000)
            total_time += exec_time
            
            all_errors.append({
                'query': query,
                'error': error_msg,
                'queryType': query_type,
                'executionTime': exec_time
            })
            
            # Log error
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if USE_LOCAL_SQLITE:
                cursor.execute('''
                    INSERT INTO query_logs (user_id, query_text, query_type, execution_time_ms, status, error_message, timestamp)
                    VALUES (?, ?, ?, ?, 'error', ?, ?)
                ''', (user_id, query, query_type, exec_time, error_msg, now))
            else:
                cursor.execute('''
                    INSERT INTO query_logs (user_id, query_text, query_type, execution_time_ms, status, error_message, timestamp)
                    VALUES (%s, %s, %s, %s, 'error', %s, %s)
                ''', (user_id, query, query_type, exec_time, error_msg, now))
    
    db.commit()
    cursor.close()
    
    return jsonify({
        'success': len(all_errors) == 0,
        'queryCount': len(all_results),
        'executionTime': f'{total_time}ms',
        'results': all_results,
        'errors': all_errors if all_errors else None,
        'message': f'{len(all_results)} query(s) executed successfully'
    })


@app.route('/api/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id = int(get_jwt_identity())
    limit = request.args.get('limit', 50, type=int)
    
    db = get_db()
    cursor = db.cursor()
    
    if USE_LOCAL_SQLITE:
        cursor.execute('''
            SELECT * FROM query_logs 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        rows = cursor.fetchall()
        history = [dict(row) for row in rows]
    else:
        cursor.execute('''
            SELECT * FROM query_logs 
            WHERE user_id = %s 
            ORDER BY timestamp DESC 
            LIMIT %s
        ''', (user_id, limit))
        history = cursor.fetchall()
    cursor.close()
    
    return jsonify({'history': history})


@app.route('/api/history/stats', methods=['GET'])
@jwt_required()
def get_stats():
    user_id = int(get_jwt_identity())
    
    db = get_db()
    cursor = db.cursor()
    
    if USE_LOCAL_SQLITE:
        cursor.execute('''
            SELECT 
                COUNT(*) as total_queries,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_queries,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed_queries,
                AVG(execution_time_ms) as avg_execution_time
            FROM query_logs 
            WHERE user_id = ?
        ''', (user_id,))
        stats = dict(cursor.fetchone())
    else:
        cursor.execute('''
            SELECT 
                COUNT(*) as total_queries,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_queries,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed_queries,
                AVG(execution_time_ms) as avg_execution_time
            FROM query_logs 
            WHERE user_id = %s
        ''', (user_id,))
        stats = cursor.fetchone()
    cursor.close()
    
    return jsonify({'stats': stats})


# ==================== ADMIN ROUTES ====================

@app.route('/api/admin/dashboard', methods=['GET'])
@jwt_required()
def admin_dashboard():
    user_id = int(get_jwt_identity())
    
    # Verify admin - use auth_db for users table
    auth_db = get_auth_db()
    auth_cursor = auth_db.cursor()
    auth_cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
    user = auth_cursor.fetchone()
    
    if not user or user[3] != 'admin':
        auth_cursor.close()
        return jsonify({'error': 'Admin access required'}), 403
    
    # Get stats from SQL query database
    db = get_db()
    cursor = db.cursor()
    
    if USE_LOCAL_SQLITE:
        cursor.execute('SELECT COUNT(*) as count FROM query_logs')
        total_queries = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed
            FROM query_logs
        ''')
        query_stats = dict(cursor.fetchone())
        
        cursor.execute('SELECT * FROM query_logs ORDER BY timestamp DESC LIMIT 20')
        rows = cursor.fetchall()
        recent_queries = [dict(row) for row in rows]
    else:
        cursor.execute('SELECT COUNT(*) as count FROM query_logs')
        total_queries = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_queries,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed,
                AVG(execution_time_ms) as avg_time
            FROM query_logs
        ''')
        query_stats = cursor.fetchone()
        
        cursor.execute('''
            SELECT ql.*, u.name, u.email 
            FROM query_logs ql 
            JOIN users u ON ql.user_id = u.id 
            ORDER BY ql.timestamp DESC 
            LIMIT 20
        ''')
        recent_queries = cursor.fetchall()
    
    cursor.close()
    
    return jsonify({
        'totalQueries': total_queries or 0,
        'successfulQueries': query_stats.get('successful', 0) or 0,
        'failedQueries': query_stats.get('failed', 0) or 0,
        'recentQueries': recent_queries
    })


@app.route('/api/admin/otps', methods=['GET'])
@jwt_required()
def admin_otps():
    user_id = int(get_jwt_identity())
    
    # Verify admin
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT role FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    
    if not user or user['role'] != 'admin':
        cursor.close()
        return jsonify({'error': 'Admin access required'}), 403
    
    cursor.execute('''
        SELECT o.*, u.name 
        FROM otp_codes o 
        LEFT JOIN users u ON o.email = u.email 
        WHERE o.expires_at > NOW() 
        ORDER BY o.created_at DESC 
        LIMIT 50
    ''')
    otps = cursor.fetchall()
    cursor.close()
    
    return jsonify({'otps': otps})


# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        # Debug info
        debug_info = {
            'status': 'ok',
            'database': 'MySQL' if not USE_LOCAL_SQLITE else 'SQLite',
            'debug': {
                'USE_LOCAL_SQLITE': USE_LOCAL_SQLITE,
                'DB_HOST': os.getenv('DB_HOST', 'NOT_SET'),
                'DB_USER': os.getenv('DB_USER', 'NOT_SET')
            }
        }
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'status': 'error', 'database': str(e)}), 500


@app.route('/api/debug/config', methods=['GET'])
def debug_config():
    """Debug endpoint to check configuration"""
    return jsonify({
        'resend_token': RESEND_API_KEY[:15] + '...' if RESEND_API_KEY else 'NOT SET',
        'from_email': FROM_EMAIL,
        'allowed_domain': ALLOWED_DOMAIN or 'ALL'
    })


# ==================== MAIN ====================

if __name__ == '__main__':
    print("Starting SQL Lab Backend...")
    with app.app_context():
        init_database()
    app.run(host='0.0.0.0', port=5000, debug=False)
