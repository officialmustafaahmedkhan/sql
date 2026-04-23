import requests

base = 'http://127.0.0.1:5000/api'
results = {}

print('=== COMPLETE TESTING ===')

# Signup & Verify
r = requests.post(base + '/auth/signup', json={'name': 'Final Test', 'email': 'final2@test.com', 'password': 'password123'})
otp = r.json().get('otp')
r = requests.post(base + '/auth/verify-otp', json={'email': 'final2@test.com', 'otp': otp})
token = r.json().get('token')
headers = {'Authorization': 'Bearer ' + token}

# Login
r = requests.post(base + '/auth/login', json={'email': 'final2@test.com', 'password': 'password123'})
results['login'] = r.status_code == 200
print('Login:', results['login'])

# SELECT
r = requests.post(base + '/query/execute', json={'query': 'SELECT * FROM students'}, headers=headers)
results['select'] = r.json().get('success') == True
print('SELECT:', results['select'])

# INSERT with proper quotes
query = "INSERT INTO students (first_name, last_name, email, department, enrollment_year, gpa) VALUES ('Ahmed', 'Khan', 'new@test.com', 'CS', 2024, 3.5)"
r = requests.post(base + '/query/execute', json={'query': query}, headers=headers)
results['insert'] = r.json().get('success') == True
print('INSERT:', results['insert'])

# UPDATE
query = "UPDATE students SET gpa = 4.0 WHERE email = 'new@test.com'"
r = requests.post(base + '/query/execute', json={'query': query}, headers=headers)
results['update'] = r.json().get('success') == True
print('UPDATE:', results['update'])

# DELETE
query = "DELETE FROM students WHERE email = 'new@test.com'"
r = requests.post(base + '/query/execute', json={'query': query}, headers=headers)
results['delete'] = r.json().get('success') == True
print('DELETE:', results['delete'])

# CREATE TABLE
r = requests.post(base + '/query/execute', json={'query': 'CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)'}, headers=headers)
results['create'] = r.json().get('success') == True
print('CREATE:', results['create'])

# DROP TABLE
r = requests.post(base + '/query/execute', json={'query': 'DROP TABLE test_table'}, headers=headers)
results['drop'] = r.json().get('success') == True
print('DROP:', results['drop'])

# MULTIPLE QUERIES
r = requests.post(base + '/query/execute', json={'query': 'SELECT * FROM students; SELECT * FROM courses'}, headers=headers)
results['multi'] = r.json().get('queryCount') >= 2
print('MULTI:', results['multi'])

# HISTORY
r = requests.get(base + '/history', headers=headers)
results['history'] = r.status_code == 200
print('HISTORY:', results['history'], r.status_code)

# STATS
r = requests.get(base + '/history/stats', headers=headers)
results['stats'] = r.status_code == 200
print('STATS:', results['stats'])

print()
print('=== SUMMARY ===')
passed = sum(results.values())
print('Passed:', passed, '/', len(results))
for k, v in results.items():
    print(k, ':', 'PASS' if v else 'FAIL')