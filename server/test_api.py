import requests

base_url = 'http://127.0.0.1:5000/api'

print('=== SQL Lab Backend - Complete Test Suite ===\n')

# 1. Health Check
print('1. Health Check:')
r = requests.get(base_url + '/health')
print('   Status:', r.json())

# 2. Signup
print('\n2. Signup:')
r = requests.post(base_url + '/auth/signup', json={'name': 'Final Test', 'email': 'finaltest99@gmail.com', 'password': 'password123'})
print('   Response:', r.json())
otp = r.json()['otp']

# 3. Verify OTP
print('\n3. Verify OTP:')
r = requests.post(base_url + '/auth/verify-otp', json={'email': 'finaltest99@gmail.com', 'otp': otp})
result = r.json()
print('   Success:', result.get('success'))
token = result.get('token')
headers = {'Authorization': 'Bearer ' + token}

# 4. SELECT Query
print('\n4. SELECT Query:')
r = requests.post(base_url + '/query/execute', json={'query': 'SELECT * FROM students'}, headers=headers)
data = r.json()
print('   Success:', data.get('success'))
print('   Rows:', len(data.get('results', [{}])[0].get('results', [])))

# 5. Multiple Queries
print('\n5. Multiple Queries:')
r = requests.post(base_url + '/query/execute', json={'query': 'SELECT 1; SELECT 2; SELECT 3;'}, headers=headers)
data = r.json()
print('   Success:', data.get('success'))
print('   Query Count:', data.get('queryCount'))

# 6. CREATE TABLE
print('\n6. CREATE TABLE:')
r = requests.post(base_url + '/query/execute', json={'query': 'CREATE TABLE test_items (id INT, name VARCHAR(50))'}, headers=headers)
print('   Success:', r.json().get('success'))

# 7. INSERT + SELECT
print('\n7. INSERT + SELECT:')
r = requests.post(base_url + '/query/execute', json={'query': 'INSERT INTO test_items VALUES (1, "Item1"); SELECT * FROM test_items;'}, headers=headers)
data = r.json()
print('   Success:', data.get('success'))
print('   Rows Inserted:', data.get('results', [{}])[0].get('rowsAffected'))

# 8. DROP TABLE
print('\n8. DROP TABLE:')
r = requests.post(base_url + '/query/execute', json={'query': 'DROP TABLE test_items'}, headers=headers)
print('   Success:', r.json().get('success'))

# 9. Blocked Query
print('\n9. Blocked Query (DROP DATABASE):')
r = requests.post(base_url + '/query/execute', json={'query': 'DROP DATABASE students'}, headers=headers)
data = r.json()
print('   Blocked:', 'errors' in str(data))

# 10. Login
print('\n10. Login Test:')
r = requests.post(base_url + '/auth/login', json={'email': 'finaltest99@gmail.com', 'password': 'password123'})
print('   Result:', r.json().get('message'))

print('\n=== All Tests Complete ===')
