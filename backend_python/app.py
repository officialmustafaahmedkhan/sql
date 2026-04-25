import os
import time
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

CORS(app, origins=[
    "http://localhost:3000",
    "http://localhost:5173",
    "https://sql-n5k6.onrender.com",
    "https://maksqlcompiler.netlify.app",
    "https://*.netlify.app",
    "https://*.vercel.app"
])
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
    return email.strip() in ADMIN_EMAILS

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
    
    access_token = create_access_token(identity=email)
    
    return jsonify({
        'message': 'Signup successful',
        'token': access_token,
        'user': {
            'email': email,
            'name': name,
            'role': 'admin' if is_admin(email) else 'student'
        }
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
    print("=" * 50)
    print("SQL Lab Backend")
    print("Database: MySQL (XAMPP 3306) - SQL Queries Only")
    print("Auth: Firebase")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)