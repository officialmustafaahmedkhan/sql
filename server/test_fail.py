import requests
base = 'http://127.0.0.1:5000/api'

# Signup & verify
r = requests.post(base + '/auth/signup', json={'name':'Q','email':'q3test@test.com','password':'password123'})
otp = r.json().get('otp')
r = requests.post(base + '/auth/verify-otp', json={'email':'q3test@test.com','otp': otp})
token = r.json().get('token')
headers = {'Authorization': 'Bearer ' + token}

print('=== TEST RESULTS ===')

# Test 1: INSERT
q = "INSERT INTO students (first_name, last_name, email, department, enrollment_year, gpa) VALUES ('Test', 'User', 'new@test.com', 'IT', 2024, 3.0)"
r = requests.post(base + '/query/execute', json={'query': q}, headers=headers)
print('INSERT:', r.json().get('success'))

# Test 2: SELECT
r = requests.post(base + '/query/execute', json={'query': 'SELECT * FROM students'}, headers=headers)
print('SELECT:', r.json().get('success'))

# Test 3: UPDATE
q = "UPDATE students SET gpa = 3.8 WHERE email = 'new@test.com'"
r = requests.post(base + '/query/execute', json={'query': q}, headers=headers)
print('UPDATE:', r.json().get('success'))

# Test 4: DELETE
q = "DELETE FROM students WHERE email = 'new@test.com'"
r = requests.post(base + '/query/execute', json={'query': q}, headers=headers)
print('DELETE:', r.json().get('success'))

# Test 5: CREATE
r = requests.post(base + '/query/execute', json={'query': 'CREATE TABLE test2 (id INT, name TEXT)'}, headers=headers)
print('CREATE:', r.json().get('success'))

# Test 6: DROP
r = requests.post(base + '/query/execute', json={'query': 'DROP TABLE test2'}, headers=headers)
print('DROP:', r.json().get('success'))