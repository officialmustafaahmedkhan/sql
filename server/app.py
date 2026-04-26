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

CORS(app)
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

# FORCED to use SQLite by default
# Only use MySQL if USE_LOCAL_SQLITE=false AND db_host is real external server
force_sqlite = os.getenv('USE_LOCAL_SQLITE', 'true').lower() != 'false'

if force_sqlite:
    USE_LOCAL_SQLITE = True
    print("[DB] FORCED SQLite (default)")
elif db_host:
    try:
        import pymysql
        test = pymysql.connect(host=db_host, port=db_port, user=db_user, 
                          password=db_pass, connect_timeout=2, ssl={'ssl_disabled': True})
        test.close()
        USE_LOCAL_SQLITE = False
        print("[DB] MySQL connected!")
    except Exception as e:
        print(f"[DB] MySQL failed: {e}")
        USE_LOCAL_SQLITE = True
else:
    USE_LOCAL_SQLITE = True

print(f"[DB] DB_HOST: '{db_host}' -> SQLite: {USE_LOCAL_SQLITE}")

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
    'ssl': {'ssl_disabled': True}
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
        return g.sql_db
    else:
        if 'db' not in g:
            g.db = pymysql.connect(**DB_CONFIG)
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
    
    blocked_keywords = ['INFORMATION_SCHEMA', 'PERFORMANCE_SCHEMA']
    if not is_admin:
        for keyword in blocked_keywords:
            if keyword in sql_upper:
                return False, f"Operation '{keyword}' is not allowed"
    
    allowed = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE TABLE', 'DROP TABLE', 'ALTER', 
              'SHOW TABLES', 'DESCRIBE', 'DESC', 'USE', 'BEGIN', 'COMMIT', 'ROLLBACK',
              'UNION', 'ORDER BY', 'GROUP BY', 'HAVING', 'LIMIT', 'JOIN']
    
    if first_word not in allowed:
        return False, f"Statement '{first_word}' is not allowed"
    
    if sql_upper.startswith('SELECT') and 'LIMIT' not in sql_upper:
        sql = f"{sql.rstrip(';')} LIMIT {MAX_ROWS}"
    
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
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not all([name, email, password]):
        return jsonify({'error': 'All fields required'}), 400
    
    if ALLOWED_DOMAIN and not email.lower().endswith(ALLOWED_DOMAIN):
        return jsonify({'error': f'Only {ALLOWED_DOMAIN} emails allowed'}), 400
    
    auth_db = get_auth_db()
    auth_cursor = auth_db.cursor()
    
    auth_cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    if auth_cursor.fetchone():
        auth_cursor.close()
        return jsonify({'error': 'Email already registered'}), 409
    
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    auth_cursor.execute(
        'INSERT INTO users (name, email, password, is_verified) VALUES (?, ?, ?, ?)',
        (name, email, hashed, 0)
    )
    
    otp = generate_otp()
    expires = datetime.now() + timedelta(minutes=5)
    
    auth_cursor.execute('DELETE FROM otp_codes WHERE email = ?', (email,))
    auth_cursor.execute(
        'INSERT INTO otp_codes (email, otp, expires_at) VALUES (?, ?, ?)',
        (email, otp, expires)
    )
    
    auth_db.commit()
    auth_cursor.close()
    
    print(f"\n{'='*50}")
    print(f"OTP FOR TESTING: {otp}")
    print(f"Email: {email}")
    print(f"{'='*50}\n")
    
    return jsonify({
        'message': 'Signup successful. Please verify your email.',
        'email': email,
        'otp': otp
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
        'user': {
            'id': user_id,
            'name': user_name,
            'email': email,
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

@app.route('/api/query/execute', methods=['POST'])
@jwt_required()
def execute_query():
    user_id = int(get_jwt_identity())
    data = request.get_json()
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
        
        is_valid, result = validate_query(query)
        if not is_valid:
            all_errors.append({'query': query, 'error': result})
            continue
        
        query = result
        query_type = query.upper().split()[0]
        
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

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'database': 'FORCED_SQLITE',
        'use_sqlite': USE_LOCAL_SQLITE,
        'db_host': os.getenv('DB_HOST', 'NOT_SET')
    })

# ==================== MAIN ====================

if __name__ == '__main__':
    print("Starting SQL Lab Backend...")
    with app.app_context():
        init_database()
    app.run(host='0.0.0.0', port=5000, debug=False)