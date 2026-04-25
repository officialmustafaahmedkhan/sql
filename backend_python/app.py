import os
import time
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import pymysql
import bcrypt
from dotenv import load_dotenv
from datetime import datetime, timedelta

script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, '.env'))

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'sql_lab_jwt_secret_2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

CORS(app, origins="*")
jwt = JWTManager(app)

# ============= MySQL (TiDB Cloud) - SSL Required =============
MYSQL_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', 4000)),
    'user': os.getenv('DB_USER', os.getenv('DB_USERNAME', 'root')),
    'password': os.getenv('DB_PASSWORD', 'admin'),
    'database': os.getenv('DB_NAME', os.getenv('DB_DATABASE', 'sqllab')),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'ssl': {'ssl': {}},
    'ssl_disabled': False
}

def get_mysql():
    return pymysql.connect(**MYSQL_CONFIG)

def is_admin(email):
    admin_emails = os.getenv('ADMIN_EMAILS', 'admin@iobm.edu.pk').split(',')
    return email.strip() in admin_emails

def is_approved(email):
    return is_admin(email)

# ============= Pending Requests Storage =============
PENDING_REQUESTS = []

def init_db():
    try:
        db = get_mysql()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255),
                role VARCHAR(50) DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                query TEXT NOT NULL,
                success BOOLEAN DEFAULT FALSE,
                execution_time VARCHAR(50),
                rows_affected INT DEFAULT 0,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pending_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()
        cursor.close()
        db.close()
        print("Database tables initialized")
        load_pending_requests()
    except Exception as e:
        print(f"DB init error: {e}")

def load_pending_requests():
    global PENDING_REQUESTS
    try:
        db = get_mysql()
        cursor = db.cursor()
        cursor.execute("SELECT name, email, password, created_at FROM pending_requests ORDER BY created_at DESC")
        rows = cursor.fetchall()
        PENDING_REQUESTS = [{'name': r['name'], 'email': r['email'], 'password': r['password'], 'timestamp': r['created_at'].isoformat() if r['created_at'] else datetime.now().isoformat()} for r in rows]
        cursor.close()
        db.close()
    except Exception as e:
        print(f"Load pending error: {e}")

def save_pending_request(name, email, password):
    try:
        db = get_mysql()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO pending_requests (name, email, password) VALUES (%s, %s, %s)",
            (name, email, password)
        )
        db.commit()
        cursor.close()
        db.close()
        load_pending_requests()
    except Exception as e:
        print(f"Save pending error: {e}")
        # Fallback to in-memory
        PENDING_REQUESTS.append({
            'name': name,
            'email': email,
            'password': password,
            'timestamp': datetime.now().isoformat()
        })

def get_pending_requests():
    return PENDING_REQUESTS

def remove_pending_request(email):
    try:
        db = get_mysql()
        cursor = db.cursor()
        cursor.execute("DELETE FROM pending_requests WHERE email = %s", (email,))
        db.commit()
        cursor.close()
        db.close()
        load_pending_requests()
    except Exception as e:
        print(f"Remove pending error: {e}")
        global PENDING_REQUESTS
        PENDING_REQUESTS = [r for r in PENDING_REQUESTS if r['email'] != email]

def add_approved_user(name, email, password):
    try:
        db = get_mysql()
        cursor = db.cursor()
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            db.close()
            return False  # User already exists
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, hashed, 'student')
        )
        db.commit()
        cursor.close()
        db.close()
        return True
    except Exception as e:
        print(f"Add user error: {e}")
        return False

def get_total_users():
    try:
        db = get_mysql()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM users")
        result = cursor.fetchone()
        cursor.close()
        db.close()
        return result.get('count', 0) if result else 0
    except:
        return 0

def get_query_stats():
    try:
        db = get_mysql()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) as total, SUM(success) as successful FROM query_logs")
        result = cursor.fetchone()
        cursor.execute("SELECT AVG(execution_time) as avg_time FROM query_logs WHERE execution_time IS NOT NULL")
        avg_result = cursor.fetchone()
        cursor.close()
        db.close()
        return {
            'total': result.get('count', 0) if result else 0,
            'successful': result.get('successful', 0) if result else 0,
            'avg_time': avg_result.get('avg_time', 0) if avg_result else 0
        }
    except:
        return {'total': 0, 'successful': 0, 'avg_time': 0}

def get_query_type(query):
    q = query.strip().upper()
    if q.startswith('SELECT'): return 'SELECT'
    if q.startswith('INSERT'): return 'INSERT'
    if q.startswith('UPDATE'): return 'UPDATE'
    if q.startswith('DELETE'): return 'DELETE'
    if q.startswith('CREATE'): return 'CREATE'
    if q.startswith('DROP'): return 'DROP'
    if q.startswith('ALTER'): return 'ALTER'
    if q.startswith('SHOW'): return 'SHOW'
    if q.startswith('DESCRIBE') or q.startswith('DESC'): return 'DESCRIBE'
    if q.startswith('USE'): return 'USE'
    if q.startswith('GRANT'): return 'GRANT'
    if q.startswith('REVOKE'): return 'REVOKE'
    if q.startswith('TRUNCATE'): return 'TRUNCATE'
    return 'OTHER'

def is_safe_query(query, user_email):
    forbidden_student = ['DROP', 'GRANT', 'REVOKE', 'TRUNCATE', 'INFORMATION_SCHEMA']
    forbidden_admin = ['DROP DATABASE', 'GRANT ALL', 'REVOKE ALL', 'INFORMATION_SCHEMA']
    
    upper_query = query.upper()
    
    if is_admin(user_email):
        for word in forbidden_admin:
            if word.upper() in upper_query:
                return False, f"Operation {word} not allowed even for admin"
    else:
        for word in forbidden_student:
            if word in upper_query:
                return False, f"Operation {word} not allowed for students"
    
    return True, None

def split_queries(sql):
    queries = []
    current = []
    in_string = False
    string_char = None
    
    for char in sql:
        if in_string:
            current.append(char)
            if char == string_char:
                in_string = False
        elif char in ("'", '"'):
            current.append(char)
            in_string = True
            string_char = char
        elif char == ';':
            query = ''.join(current).strip()
            if query:
                queries.append(query)
            current = []
        else:
            current.append(char)
    
    final_query = ''.join(current).strip()
    if final_query:
        queries.append(final_query)
    
    return queries

# ============= AUTH ROUTES =============

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    password = data.get('password')
    
    if not all([email, name, password]):
        return jsonify({'error': 'All fields required'}), 400
    
    if is_admin(email):
        # Admin can be created directly
        access_token = create_access_token(identity=email)
        return jsonify({
            'message': 'Signup successful',
            'token': access_token,
            'user': {
                'email': email,
                'name': name,
                'role': 'admin'
            }
        }), 201
    else:
        # Save pending request for admin approval
        save_pending_request(name, email, password)
        return jsonify({
            'message': 'Signup request submitted. Waiting for admin approval.',
            'pending': True
        }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not all([email, password]):
        return jsonify({'error': 'Email and password required'}), 400
    
    access_token = create_access_token(identity=email)
    
    return jsonify({
        'message': 'Login successful',
        'token': access_token,
        'user': {
            'email': email,
            'name': email.split('@')[0],
            'role': 'admin' if is_admin(email) else 'student'
        }
    })

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    email = get_jwt_identity()
    return jsonify({
        'user': {
            'email': email,
            'name': email.split('@')[0],
            'role': 'admin' if is_admin(email) else 'student'
        }
    })

# ============= Admin Routes =============

@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
def get_stats():
    user_email = get_jwt_identity()
    if not is_admin(user_email):
        return jsonify({'error': 'Admin access required'}), 403
    
    query_stats = get_query_stats()
    return jsonify({
        'totalUsers': get_total_users(),
        'totalQueries': query_stats['total'],
        'successfulQueries': query_stats['successful'],
        'unsuccessfulQueries': query_stats['total'] - query_stats['successful'],
        'avgTime': f"{query_stats['avg_time']}ms"
    })

@app.route('/api/admin/history', methods=['GET'])
@jwt_required()
def get_query_history():
    user_email = get_jwt_identity()
    if not is_admin(user_email):
        return jsonify({'error': 'Admin access required'}), 403
    
    return jsonify({'history': []})

@app.route('/api/admin/pending', methods=['GET'])
@jwt_required()
def get_pending():
    user_email = get_jwt_identity()
    if not is_admin(user_email):
        return jsonify({'error': 'Admin access required'}), 403
    return jsonify({'pending': get_pending_requests()})

@app.route('/api/admin/approve', methods=['POST'])
@jwt_required()
def approve_user():
    user_email = get_jwt_identity()
    if not is_admin(user_email):
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    email = data.get('email')
    action = data.get('action')
    
    if action == 'reject':
        remove_pending_request(email)
        return jsonify({'message': 'Request rejected'})
    
    pending = [r for r in get_pending_requests() if r['email'] == email]
    if not pending:
        return jsonify({'error': 'Request not found'}), 404
    
    pending_user = pending[0]
    remove_pending_request(email)
    
    # Check if user already exists
    if not add_approved_user(pending_user['name'], pending_user['email'], pending_user['password']):
        return jsonify({'error': 'User already exists with this email', 'email': email}), 409
    
    return jsonify({
        'message': f'User {email} approved and created',
        'user': {
            'email': pending_user['email'],
            'name': pending_user['name']
        }
    })

# ============= SQL QUERY ROUTES =============

@app.route('/api/query/execute', methods=['POST'])
@jwt_required()
def execute_query():
    data = request.get_json()
    sql = data.get('query', '').strip()
    user_email = get_jwt_identity()
    
    if not sql:
        return jsonify({'error': 'Query required'}), 400
    
    start_time = time.time()
    queries = split_queries(sql)
    results = []
    errors = []
    total_queries = len(queries)
    
    db = get_mysql()
    cursor = db.cursor()
    
    try:
        for i, query in enumerate(queries):
            query = query.strip()
            if not query:
                continue
            
            safe, error_msg = is_safe_query(query, user_email)
            if not safe:
                errors.append({'query': query[:50], 'error': error_msg})
                results.append({
                    'query': query[:100],
                    'queryType': get_query_type(query),
                    'success': False,
                    'error': error_msg,
                    'results': None,
                    'rowsAffected': 0
                })
                continue
            
            is_select = query.upper().strip().startswith('SELECT')
            query_with_limit = query
            if is_select and 'LIMIT' not in query.upper():
                query_with_limit = query.rstrip(';') + ' LIMIT 100'
            
            try:
                cursor.execute(query_with_limit)
                
                if is_select:
                    rows = cursor.fetchall()
                    results.append({
                        'query': query,
                        'queryType': get_query_type(query),
                        'success': True,
                        'results': rows,
                        'rowsAffected': len(rows)
                    })
                else:
                    results.append({
                        'query': query,
                        'queryType': get_query_type(query),
                        'success': True,
                        'results': None,
                        'rowsAffected': cursor.rowcount
                    })
            except Exception as e:
                error_msg = str(e)
                errors.append({'query': query[:50], 'error': error_msg})
                results.append({
                    'query': query[:100],
                    'queryType': get_query_type(query),
                    'success': False,
                    'error': error_msg,
                    'results': None,
                    'rowsAffected': 0
                })
        
        db.commit()
        execution_time = f"{(time.time() - start_time)*1000:.2f}ms"
        
        return jsonify({
            'success': len(errors) == 0,
            'message': f"{total_queries} query(s) executed",
            'queryCount': total_queries,
            'executionTime': execution_time,
            'results': results,
            'errors': errors if errors else None
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        cursor.close()
        db.close()

@app.route('/api/tables', methods=['GET'])
@jwt_required()
def get_tables():
    try:
        db = get_mysql()
        cursor = db.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify({'tables': [t[0] for t in tables]})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/schema/<table_name>', methods=['GET'])
@jwt_required()
def get_table_schema(table_name):
    try:
        db = get_mysql()
        cursor = db.cursor()
        cursor.execute(f"DESCRIBE `{table_name}`")
        columns = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify({'columns': columns})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/practices', methods=['GET'])
def get_practices():
    practices = [
        {
            'id': 1,
            'title': 'Basic SELECT',
            'description': 'Retrieve all data from a table',
            'query': 'SELECT * FROM users;',
            'difficulty': 'Easy'
        },
        {
            'id': 2,
            'title': 'WHERE Clause',
            'description': 'Filter results with conditions',
            'query': "SELECT * FROM users WHERE role = 'student';",
            'difficulty': 'Easy'
        },
        {
            'id': 3,
            'title': 'INSERT Data',
            'description': 'Add new records to a table',
            'query': "INSERT INTO users (name, email, role) VALUES ('Test', 'test@test.com', 'student');",
            'difficulty': 'Medium'
        },
        {
            'id': 4,
            'title': 'UPDATE Records',
            'description': 'Modify existing data',
            'query': "UPDATE users SET role = 'student' WHERE email = 'test@test.com';",
            'difficulty': 'Medium'
        },
        {
            'id': 5,
            'title': 'DELETE Data',
            'description': 'Remove records from table',
            'query': "DELETE FROM users WHERE email = 'test@test.com';",
            'difficulty': 'Hard'
        }
    ]
    return jsonify({'practices': practices})

@app.route('/api/health', methods=['GET'])
def health():
    try:
        db = get_mysql()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        db.close()
        return jsonify({'status': 'ok', 'database': 'MySQL (XAMPP 3306)'})
    except Exception as e:
        return jsonify({'status': 'error', 'database': str(e)}), 500

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("SQL Lab Backend")
    print("Database: TiDB Cloud")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)