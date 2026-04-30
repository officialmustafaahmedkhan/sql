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

# Load .env file
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, '.env'))

app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'your-secret-key-change-this')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
jwt = JWTManager(app)

# Email Configuration
RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
FROM_EMAIL = os.getenv('EMAIL_FROM', 'onboarding@resend.dev')
FROM_NAME = 'SQL Lab'

def send_email(to_email, subject, html_content):
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
# Database Configuration - FINAL VERSION
# =====================================================
print("[START] Initializing database config...")

# Get env vars
db_host = os.getenv('DB_HOST', '')
db_user = os.getenv('DB_USER', '')
db_pass = os.getenv('DB_PASSWORD', '')
db_name = os.getenv('DB_NAME', '')
db_port = int(os.getenv('DB_PORT', 3306))

# =====================================================
# ALWAYS USE SQLITE FOR DEPLOYMENT
# =====================================================
USE_LOCAL_SQLITE = os.getenv('USE_LOCAL_SQLITE', 'true').lower() == 'true'

print(f"[DB] FORCE SQLite: USE_LOCAL_SQLITE = {USE_LOCAL_SQLITE}")

# SQLite paths
SQL_DB_PATH = './sqllab.db'
AUTH_DB_PATH = './sqllab_auth.db'

# MySQL config - NOT USED
DB_CONFIG = {
    'host': 'NOT_USED',
    'port': 3306,
    'user': 'NOT_USED',
    'password': 'NOT_USED',
    'database': 'NOT_USED',
}

# SQLite paths
SQL_DB_PATH = './sqllab.db'
AUTH_DB_PATH = './sqllab_auth.db'

# MySQL config (not used when USE_LOCAL_SQLITE=True)
DB_CONFIG = {
    'host': db_host,
    'port': db_port,
    'user': db_user,
    'password': db_pass,
    'database': db_name,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'ssl': {'verify_cert': True}
}

print("[DB] Database config initialized!")

# Query Settings
QUERY_TIMEOUT_MS = int(os.getenv('QUERY_TIMEOUT_MS', 300))
MAX_ROWS = int(os.getenv('MAX_ROWS', 100))
ALLOWED_DOMAIN = os.getenv('ALLOWED_DOMAIN', '')

# SQL keywords to block
DANGEROUS_KEYWORDS = ['INFORMATION_SCHEMA', 'PERFORMANCE_SCHEMA']

# Full SQL statements allowed
ALLOWED_STATEMENTS = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 
                  'CREATE TABLE', 'CREATE DATABASE', 'CREATE VIEW',
                  'DROP TABLE', 'DROP DATABASE', 'DROP VIEW',
                  'ALTER', 'DESCRIBE', 'DESC', 'RENAME', 'TRUNCATE', 
                  'SHOW TABLES', 'SHOW COLUMNS', 'SHOW INDEX', 'SHOW DATABASES',
                  'USE', 'BEGIN', 'COMMIT', 'ROLLBACK', 'SAVEPOINT', 
                  'START TRANSACTION', 'GRANT', 'REVOKE', 'CALL', 'EXPLAIN',
                  'UNION', 'UNION ALL', 'ORDER BY', 'GROUP BY', 'HAVING',
                  'LIMIT', 'OFFSET', 'JOIN', 'WHERE', 'AND', 'OR', 'NOT',
                  'IN', 'BETWEEN', 'LIKE', 'IS NULL', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX']

def get_db():
    if USE_LOCAL_SQLITE:
        if 'sql_db' not in g:
            import sqlite3
            g.sql_db = sqlite3.connect(SQL_DB_PATH)
            g.sql_db.row_factory = sqlite3.Row
            # Auto-create tables
            cursor = g.sql_db.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT UNIQUE, department TEXT, enrollment_year INTEGER, gpa REAL)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, course_code TEXT UNIQUE, course_name TEXT, credits INTEGER, department TEXT, instructor TEXT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, student_id INTEGER, course_id INTEGER, grade TEXT, semester TEXT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS query_logs (id INTEGER PRIMARY KEY, user_id INTEGER, query_text TEXT, query_type TEXT, execution_time_ms INTEGER, rows_affected INTEGER, status TEXT, error_message TEXT, timestamp TEXT)''')
            # Sample data
            cursor.execute('SELECT COUNT(*) FROM students')
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO students VALUES (1, 'Ahmed', 'Khan', 'ahmed@iobm.edu.pk', 'Computer Science', 2023, 3.75)")
                cursor.execute("INSERT INTO students VALUES (2, 'Fatima', 'Ali', 'fatima@iobm.edu.pk', 'Business Admin', 2022, 3.90)")
                cursor.execute("INSERT INTO students VALUES (3, 'Muhammad', 'Hassan', 'hassan@iobm.edu.pk', 'Computer Science', 2023, 3.50)")
                cursor.execute("INSERT INTO courses VALUES (1, 'CS101', 'Introduction to Programming', 4, 'Computer Science', 'Dr. Ahmad')")
                cursor.execute("INSERT INTO courses VALUES (2, 'CS201', 'Data Structures', 4, 'Computer Science', 'Dr. Fatima')")
                cursor.execute("INSERT INTO courses VALUES (3, 'CS301', 'Database Systems', 3, 'Computer Science', 'Dr. Hassan')")
            g.sql_db.commit()
        return g.sql_db
    else:
        if 'db' not in g:
            g.db = pymysql.connect(**DB_CONFIG)
            
            cursor = g.db.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS students (id INT AUTO_INCREMENT PRIMARY KEY, first_name VARCHAR(50), last_name VARCHAR(50), email VARCHAR(100) UNIQUE, department VARCHAR(50), enrollment_year INT, gpa FLOAT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS courses (id INT AUTO_INCREMENT PRIMARY KEY, course_code VARCHAR(20) UNIQUE, course_name VARCHAR(100), credits INT, department VARCHAR(50), instructor VARCHAR(50))''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS enrollments (id INT AUTO_INCREMENT PRIMARY KEY, student_id INT, course_id INT, grade VARCHAR(5), semester VARCHAR(20))''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS query_logs (id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, query_text TEXT, query_type VARCHAR(50), execution_time_ms INT, rows_affected INT DEFAULT 0, status VARCHAR(20), error_message TEXT, timestamp DATETIME)''')
            
            cursor.execute('SELECT COUNT(*) as cnt FROM students')
            if cursor.fetchone()['cnt'] == 0:
                cursor.execute("INSERT INTO students (id, first_name, last_name, email, department, enrollment_year, gpa) VALUES (1, 'Ahmed', 'Khan', 'ahmed@iobm.edu.pk', 'CS', 2023, 3.75)")
                cursor.execute("INSERT INTO students (id, first_name, last_name, email, department, enrollment_year, gpa) VALUES (2, 'Fatima', 'Ali', 'fatima@iobm.edu.pk', 'Business', 2022, 3.90)")
                cursor.execute("INSERT INTO students (id, first_name, last_name, email, department, enrollment_year, gpa) VALUES (3, 'Muhammad', 'Hassan', 'hassan@iobm.edu.pk', 'CS', 2023, 3.50)")
                cursor.execute("INSERT INTO courses (id, course_code, course_name, credits, department, instructor) VALUES (1, 'CS101', 'Intro to Programming', 4, 'CS', 'Dr. Ahmad')")
                cursor.execute("INSERT INTO courses (id, course_code, course_name, credits, department, instructor) VALUES (2, 'CS201', 'Data Structures', 4, 'CS', 'Dr. Fatima')")
                cursor.execute("INSERT INTO courses (id, course_code, course_name, credits, department, instructor) VALUES (3, 'CS301', 'Database Systems', 3, 'CS', 'Dr. Hassan')")
                g.db.commit()
            cursor.close()
            
        return g.db

def get_auth_db():
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
    import sqlite3
    
    # Auth database
    auth_db = sqlite3.connect(AUTH_DB_PATH)
    auth_cursor = auth_db.cursor()
    
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
    print("[DB] Auth database initialized!")
    
    # SQL Practice database
    sql_db = sqlite3.connect(SQL_DB_PATH)
    sql_cursor = sql_db.cursor()
    
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
            enrolled_at DATETIME DEFAULT NULL
        )
    ''')
    
    # Sample data
    sql_cursor.execute('SELECT COUNT(*) FROM students')
    if sql_cursor.fetchone()[0] == 0:
        sql_cursor.execute('''
            INSERT INTO students (first_name, last_name, email, department, enrollment_year, gpa) VALUES
            ('Ahmed', 'Khan', 'ahmed@iobm.edu.pk', 'Computer Science', 2023, 3.75),
            ('Fatima', 'Ali', 'fatima@iobm.edu.pk', 'Business Admin', 2022, 3.90),
            ('Muhammad', 'Hassan', 'hassan@iobm.edu.pk', 'Computer Science', 2023, 3.50)
        ''')
    
    sql_cursor.execute('SELECT COUNT(*) FROM courses')
    if sql_cursor.fetchone()[0] == 0:
        sql_cursor.execute('''
            INSERT INTO courses (course_code, course_name, credits, department, instructor) VALUES
            ('CS101', 'Introduction to Programming', 4, 'Computer Science', 'Dr. Ahmad'),
            ('CS201', 'Data Structures', 4, 'Computer Science', 'Dr. Fatima'),
            ('CS301', 'Database Systems', 3, 'Computer Science', 'Dr. Hassan')
        ''')
    
    sql_db.commit()
    sql_cursor.close()
    print("[DB] SQL Practice database initialized!")

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def validate_query(sql, is_admin=False):
    sql_upper = sql.upper().strip()
    words = sql_upper.split()
    first_word = words[0] if words else ''
    second_word = words[1] if len(words) > 1 else ''
    
    first_two = f"{first_word} {second_word}"
    
    blocked_keywords = ['INFORMATION_SCHEMA', 'PERFORMANCE_SCHEMA']
    if not is_admin:
        for keyword in blocked_keywords:
            if keyword in sql_upper:
                return False, f"Operation '{keyword}' is not allowed"
    
    allowed_sqlite = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE TABLE', 'DROP TABLE', 
                   'ALTER', 'SHOW', 'DESCRIBE', 'DESC', 'USE', 'BEGIN', 'COMMIT', 
                   'ROLLBACK', 'UNION', 'ORDER BY', 'GROUP BY', 'HAVING', 'LIMIT', 'JOIN']
    
    allowed_mysql = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE TABLE', 'DROP TABLE', 
                     'CREATE DATABASE', 'DROP DATABASE', 'ALTER', 'SHOW', 'DESCRIBE', 'DESC', 
                     'USE', 'BEGIN', 'COMMIT', 'ROLLBACK', 'UNION', 'ORDER BY', 
                     'GROUP BY', 'HAVING', 'LIMIT', 'JOIN']
    
    allowed = allowed_mysql if not USE_LOCAL_SQLITE else allowed_sqlite
    
    is_allowed = first_two in allowed or first_word in allowed
    
    if not is_allowed:
        return False, f"Statement '{first_word}' is not allowed"
    
    if sql_upper.startswith('SELECT') and 'LIMIT' not in sql_upper:
        import os
        sql = f"{sql.rstrip(';')} LIMIT {os.getenv('MAX_ROWS', '100')}"
    
    return True, sql

def split_queries(sql):
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
    
    query = ''.join(current).strip()
    if query:
        queries.append(query)
    
    return queries

# ==================== AUTH ROUTES ====================

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        # Ensure tables exist
        auth_db = get_auth_db()
        cursor = auth_db.cursor()
        
        cursor.execute('''
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS otp_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                otp TEXT NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        auth_db.commit()
        
        # Now get data
        data = request.get_json() or {}
        name = data.get('name', '')
        email = data.get('email', '')
        password = data.get('password', '')
        
        if not name or not email or not password:
            return jsonify({'error': 'All fields required'}), 400
        
        # Hash
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        # Check
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Email registered'}), 409
        
        # Insert
        # Insert - first user is admin
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        role = 'admin' if count == 1 else 'student'
        
        cursor.execute('INSERT INTO users (name, email, password, is_verified, role) VALUES (?, ?, ?, ?, ?)',
            (name, email, hashed, 1, role))
        
        # OTP
        otp = generate_otp()
        cursor.execute('INSERT INTO otp_codes (email, otp, expires_at) VALUES (?, ?, ?)',
            (email, otp, datetime.now()))
        
        auth_db.commit()
        cursor.close()
        
        return jsonify({'message': 'OK', 'email': email, 'otp': otp}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    
    if not all([email, otp]):
        return jsonify({'error': 'Email and OTP required'}), 400
    
    auth_db = get_auth_db()
    auth_cursor = auth_db.cursor()
    
    auth_cursor.execute(
        'SELECT * FROM otp_codes WHERE email = ? AND otp = ?',
        (email, otp)
    )
    otp_record = auth_cursor.fetchone()
    
    if not otp_record:
        auth_cursor.close()
        return jsonify({'error': 'Invalid OTP'}), 400
    
    auth_cursor.execute('UPDATE users SET is_verified = 1 WHERE email = ?', (email,))
    auth_cursor.execute('DELETE FROM otp_codes WHERE email = ?', (email,))
    
    auth_cursor.execute('SELECT id, name, email, role FROM users WHERE email = ?', (email,))
    user = auth_cursor.fetchone()
    
    auth_db.commit()
    auth_cursor.close()
    
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
    import traceback
    try:
        data = request.get_json()
        email = data.get('email', '')
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        auth_db = get_auth_db()
        auth_cursor = auth_db.cursor()
        
        auth_cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = auth_cursor.fetchone()
        auth_cursor.close()
        
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        user_id = user[0]
        user_name = user[1]
        user_password = user[3]
        user_role = user[4]
        user_verified = user[5]
        
        if not bcrypt.checkpw(password.encode(), user_password.encode()):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user_verified:
            return jsonify({'error': 'Please verify email first'}), 403
        
        access_token = create_access_token(identity=str(user_id))
        
        return jsonify({
            'message': 'Login successful',
            'token': access_token,
            'user': {'id': user_id, 'name': user_name, 'email': email, 'role': user_role}
        })
    except Exception as e:
        print(f"[LOGIN ERROR] {type(e).__name__}: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
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
        
        return jsonify({
            'user': {
                'id': user[0],
                'name': user[1],
                'email': user[2],
                'role': user[3],
                'is_verified': user[4]
            }
        })
    except Exception as e:
        print(f"[PROFILE ERROR] {type(e).__name__}: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== QUERY ROUTES ====================

@app.route('/api/query/execute', methods=['POST'])
@jwt_required()
def execute_query():
    import traceback
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json(silent=True)
        if data is None or not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON'}), 400
        sql = data.get('query', '').strip()
        
        if not sql:
            return jsonify({'error': 'Query required'}), 400
        
        queries = split_queries(sql)
        all_results = []
        all_errors = []
        total_time = 0
        
        db = get_db()
        cursor = db.cursor()
        
        for query in queries:
            if not query.strip() or query.strip().startswith('--'):
                continue
            
            start_time = datetime.now()
            query_upper = query.upper().strip()
            
            if query_upper.startswith('USE '):
                db_name = queryUpper = query.strip().split()[1].strip(';')
                try:
                    if not USE_LOCAL_SQLITE:
                        cursor.execute(f'USE {db_name}')
                        db.commit()
                    result_data = {
                        'query': query,
                        'queryType': 'USE',
                        'success': True,
                        'results': [{'message': f'Switched to database: {db_name}'}],
                        'rowsAffected': 0,
                        'executionTime': int((datetime.now() - start_time).total_seconds() * 1000)
                    }
                    all_results.append(result_data)
                    continue
                except Exception as e:
                    all_errors.append({'query': query, 'error': str(e)})
                    continue
            
            is_valid, result = validate_query(query)
            if not is_valid:
                all_errors.append({'query': query, 'error': result})
                continue
            
            query = result
            query_type = query.upper().split()[0]
            
            if USE_LOCAL_SQLITE:
                query_norm = query_upper.replace(';', '').strip()
                if query_norm == 'SHOW TABLES':
                    query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                    query_type = 'SELECT'
                elif query_norm == 'SHOW DATABASES':
                    query = "SELECT 'sqllab.db' as database_name"
                    query_type = 'SELECT'
            
            RESULT_STATEMENTS = ['SELECT', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN']
            
            try:
                cursor.execute(query)
                
                if query_type in RESULT_STATEMENTS:
                    rows = cursor.fetchall()
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
                all_errors.append({'query': query, 'error': error_msg})
        
        db.commit()
        cursor.close()
        
        return jsonify({
            'success': len(all_errors) == 0,
            'queryCount': len(all_results),
            'executionTime': f'{total_time}ms',
            'results': all_results,
            'errors': all_errors if all_errors else None
        })
    except Exception as e:
        import traceback
        print(f"[QUERY ERROR] Type: {type(e).__name__}, Value: {e}")
        print(f"[QUERY ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'{type(e).__name__}: {e}'}), 500

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
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed
            FROM query_logs 
            WHERE user_id = ?
        ''', (user_id,))
        stats = dict(cursor.fetchone())
    else:
        cursor.execute('''
            SELECT 
                COUNT(*) as total_queries,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed
            FROM query_logs 
            WHERE user_id = %s
        ''', (user_id,))
        stats = cursor.fetchone()
    cursor.close()
    
    return jsonify({'stats': stats})

# ==================== TABLES ====================

@app.route('/api/tables', methods=['GET'])
@jwt_required()
def get_tables():
    try:
        db = get_db()
        cursor = db.cursor()
        if USE_LOCAL_SQLITE:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        else:
            cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        return jsonify({'tables': tables})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== SCHEMA ====================

@app.route('/api/schema/<table_name>', methods=['GET'])
@jwt_required()
def get_schema(table_name):
    try:
        db = get_db()
        cursor = db.cursor()
        if USE_LOCAL_SQLITE:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [{'name': row[1], 'type': row[2]} for row in cursor.fetchall()]
        else:
            cursor.execute(f"DESCRIBE {table_name}")
            columns = [{'name': row[0], 'type': row[1]} for row in cursor.fetchall()]
        return jsonify({'table': table_name, 'columns': columns})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== PRACTICES ====================

@app.route('/api/practices', methods=['GET'])
def get_practices():
    db = get_db()
    cursor = db.cursor()
    
    if USE_LOCAL_SQLITE:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='practices'")
    else:
        cursor.execute("SHOW TABLES LIKE 'practices'")
    
    if not cursor.fetchone():
        cursor.execute('''CREATE TABLE practices (id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(100), description TEXT, query TEXT, difficulty VARCHAR(20), category VARCHAR(50))''')
        cursor.execute("INSERT INTO practices (title, description, query, difficulty, category) VALUES ('Basic SELECT', 'Fetch all columns from students table', 'SELECT * FROM students LIMIT 10', 'Easy', 'SELECT')")
        cursor.execute("INSERT INTO practices (title, description, query, difficulty, category) VALUES ('Filter with WHERE', 'Find students with GPA above 3.5', 'SELECT * FROM students WHERE gpa > 3.5', 'Easy', 'WHERE')")
        cursor.execute("INSERT INTO practices (title, description, query, difficulty, category) VALUES ('Order Results', 'List courses by credits descending', 'SELECT * FROM courses ORDER BY credits DESC', 'Easy', 'ORDER BY')")
        cursor.execute("INSERT INTO practices (title, description, query, difficulty, category) VALUES ('Count Records', 'Count total students', 'SELECT COUNT(*) as total FROM students', 'Medium', 'Aggregate')")
        cursor.execute("INSERT INTO practices (title, description, query, difficulty, category) VALUES ('Group By Department', 'Average GPA per department', 'SELECT department, AVG(gpa) as avg_gpa FROM students GROUP BY department', 'Medium', 'GROUP BY')")
        db.commit()
    
    if USE_LOCAL_SQLITE:
        cursor.execute('SELECT * FROM practices ORDER BY id')
        rows = cursor.fetchall()
        practices = [dict(row) for row in rows]
    else:
        cursor.execute('SELECT * FROM practices ORDER BY id')
        practices = cursor.fetchall()
    
    cursor.close()
    return jsonify({'practices': practices})

# ==================== ADMIN ROUTES ====================

def is_admin(user_id):
    try:
        auth_db = get_auth_db()
        auth_cursor = auth_db.cursor()
        auth_cursor.execute('SELECT role FROM users WHERE id = ?', (int(user_id),))
        user = auth_cursor.fetchone()
        auth_cursor.close()
        return user and user[0] == 'admin'
    except Exception:
        return False

@app.route('/api/admin/claim', methods=['POST'])
@jwt_required()
def claim_admin():
    """Make yourself admin if no admin exists yet"""
    try:
        user_id = int(get_jwt_identity())
        auth_db = get_auth_db()
        auth_cursor = auth_db.cursor()
        
        auth_cursor.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('admin',))
        admin_count = auth_cursor.fetchone()[0]
        
        if admin_count == 0:
            auth_cursor.execute('UPDATE users SET role = ? WHERE id = ?', ('admin', user_id))
            auth_db.commit()
            auth_cursor.close()
            return jsonify({'message': 'You are now admin!'})
        
        auth_cursor.close()
        return jsonify({'error': 'Admin already exists'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
def admin_stats():
    try:
        user_id = int(get_jwt_identity())
        if not is_admin(user_id):
            return jsonify({'error': 'Admin access required'}), 403
        
        auth_db = get_auth_db()
        auth_cursor = auth_db.cursor()
        auth_cursor.execute('SELECT COUNT(*) as total_users FROM users')
        row = auth_cursor.fetchone()
        total_users = row[0] if USE_LOCAL_SQLITE else row['total_users']
        auth_cursor.close()
        
        db = get_db()
        cursor = db.cursor()
        
        if USE_LOCAL_SQLITE:
            cursor.execute('SELECT COUNT(*) as total, SUM(CASE WHEN status = "success" THEN 1 ELSE 0 END) as success, SUM(CASE WHEN status = "error" THEN 1 ELSE 0 END) as failed, AVG(execution_time_ms) as avg_time FROM query_logs')
            stats = dict(cursor.fetchone())
            total_queries = stats.get('total', 0)
            successful = stats.get('success', 0)
            failed = stats.get('failed', 0)
            avg_time = stats.get('avg_time', 0)
        else:
            cursor.execute('SELECT COUNT(*) as total_queries, SUM(CASE WHEN status = "success" THEN 1 ELSE 0 END) as successful, SUM(CASE WHEN status = "error" THEN 1 ELSE 0 END) as failed, AVG(execution_time_ms) as avg_time FROM query_logs')
            stats = cursor.fetchone()
            total_queries = stats['total_queries'] or 0
            successful = stats['successful'] or 0
            failed = stats['failed'] or 0
            avg_time = stats['avg_time'] or 0
        
        cursor.close()
        
        return jsonify({
            'totalUsers': total_users,
            'totalQueries': stats.get('total', 0) or stats.get('total_queries', 0),
            'successfulQueries': stats.get('success', 0) or stats.get('successful', 0),
            'unsuccessfulQueries': stats.get('failed', 0),
            'avgTime': f"{int(stats.get('avg_time', 0) or 0)}ms"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/pending', methods=['GET'])
@jwt_required()
def get_pending_requests():
    try:
        user_id = int(get_jwt_identity())
        if not is_admin(user_id):
            return jsonify({'error': 'Admin access required'}), 403
        
        auth_db = get_auth_db()
        auth_cursor = auth_db.cursor()
        
        auth_cursor.execute('CREATE TABLE IF NOT EXISTS pending_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)')
        auth_db.commit()
        
        if USE_LOCAL_SQLITE:
            auth_cursor.execute('SELECT * FROM pending_requests ORDER BY created_at DESC')
            rows = auth_cursor.fetchall()
            requests = [dict(row) for row in rows]
        else:
            auth_cursor.execute('SELECT * FROM pending_requests ORDER BY created_at DESC')
            requests = auth_cursor.fetchall()
        
        auth_cursor.close()
        return jsonify({'pending': requests})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/approve', methods=['POST'])
@jwt_required()
def approve_user():
    try:
        user_id = int(get_jwt_identity())
        if not is_admin(user_id):
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        email = data.get('email')
        action = data.get('action')
        
        if not email or action not in ['approve', 'reject']:
            return jsonify({'error': 'Email and action required'}), 400
        
        auth_db = get_auth_db()
        auth_cursor = auth_db.cursor()
        
        auth_cursor.execute('SELECT * FROM pending_requests WHERE email = ?', (email,))
        pending = auth_cursor.fetchone()
        
        if not pending:
            auth_cursor.close()
            return jsonify({'error': 'Request not found'}), 404
        
        if action == 'approve':
            if USE_LOCAL_SQLITE:
                name = pending[1]
                password = pending[3]
            else:
                name = pending[1]
                password = pending[3]
            
            auth_cursor.execute('SELECT COUNT(*) as cnt FROM users')
            count = auth_cursor.fetchone()
            count = count[0] if USE_LOCAL_SQLITE else count['cnt']
            role = 'admin' if count == 0 else 'student'
            
            auth_cursor.execute('INSERT INTO users (name, email, password, role, is_verified) VALUES (?, ?, ?, ?, 1)', (name, email, password, role))
            auth_cursor.execute('DELETE FROM pending_requests WHERE email = ?', (email,))
        else:
            auth_cursor.execute('DELETE FROM pending_requests WHERE email = ?', (email,))
        
        auth_db.commit()
        auth_cursor.close()
        
        return jsonify({'message': f'User {action}d successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/history', methods=['GET'])
@jwt_required()
def admin_history():
    try:
        user_id = int(get_jwt_identity())
        if not is_admin(user_id):
            return jsonify({'error': 'Admin access required'}), 403
        
        limit = request.args.get('limit', 50, type=int)
        db = get_db()
        cursor = db.cursor()
        
        if USE_LOCAL_SQLITE:
            cursor.execute('''
                SELECT ql.*, u.name as user_name, u.email as user_email 
                FROM query_logs ql 
                LEFT JOIN users u ON ql.user_id = u.id 
                ORDER BY ql.timestamp DESC LIMIT ?
            ''', (limit,))
            history = [dict(row) for row in cursor.fetchall()]
        else:
            cursor.execute('''
                SELECT ql.*, u.name as user_name, u.email as user_email 
                FROM query_logs ql 
                LEFT JOIN auth_db.users u ON ql.user_id = u.id 
                ORDER BY ql.timestamp DESC LIMIT %s
            ''', (limit,))
            history = cursor.fetchall()
        
        cursor.close()
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/make-admin', methods=['POST'])
@jwt_required()
def make_admin():
    try:
        user_id = int(get_jwt_identity())
        if not is_admin(user_id):
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        target_email = data.get('email')
        
        if not target_email:
            return jsonify({'error': 'Email required'}), 400
        
        auth_db = get_auth_db()
        auth_cursor = auth_db.cursor()
        auth_cursor.execute('UPDATE users SET role = "admin" WHERE email = ?', (target_email,))
        auth_db.commit()
        auth_cursor.close()
        
        return jsonify({'message': f'{target_email} is now an admin'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def get_all_users():
    try:
        user_id = int(get_jwt_identity())
        if not is_admin(user_id):
            return jsonify({'error': 'Admin access required'}), 403
        
        auth_db = get_auth_db()
        auth_cursor = auth_db.cursor()
        
        if USE_LOCAL_SQLITE:
            auth_cursor.execute('SELECT id, name, email, role, is_verified, created_at FROM users ORDER BY created_at DESC')
            users = [dict(row) for row in auth_cursor.fetchall()]
        else:
            auth_cursor.execute('SELECT id, name, email, role, is_verified, created_at FROM users ORDER BY created_at DESC')
            users = auth_cursor.fetchall()
        
        auth_cursor.close()
        return jsonify({'users': users})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'database': 'MySQL' if not USE_LOCAL_SQLITE else 'SQLite',
        'use_sqlite': USE_LOCAL_SQLITE,
        'db_host': os.getenv('DB_HOST', 'NOT_SET'),
        'raw_env_use_sqlite': os.getenv('USE_LOCAL_SQLITE', 'NOT_SET')
    })

@app.route('/api/db-status', methods=['GET'])
def db_status():
    if USE_LOCAL_SQLITE:
        return jsonify({'status': 'connected', 'type': 'SQLite'})
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        conn.close()
        return jsonify({'status': 'connected', 'type': 'MySQL', 'host': DB_CONFIG['host']})
    except Exception as e:
        return jsonify({'status': 'disconnected', 'type': 'MySQL', 'error': str(e)})

# ==================== MAIN ====================

if __name__ == '__main__':
    print("Starting SQL Lab Backend...")
    with app.app_context():
        init_database()
    app.run(host='0.0.0.0', port=5000, debug=False)