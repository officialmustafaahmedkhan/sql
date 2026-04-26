import requests

base_url = 'http://127.0.0.1:5000/api'

print('=== SQL Lab Backend Test ===\n')

# 1. Health Check
print('1. Health Check:')
r = requests.get(base_url + '/health')
print('   Status:', r.json())

# 2. Login
print('\n2. Login Test:')
r = requests.post(base_url + '/auth/login', json={'email': 'admin@iobm.edu.pk', 'password': 'test123'})
result = r.json()
print('   Result:', result.get('message'))
token = result.get('token')
headers = {'Authorization': 'Bearer ' + token}

# 3. SELECT Query
print('\n3. SELECT Query:')
r = requests.post(base_url + '/query/execute', json={'query': 'SELECT * FROM users'}, headers=headers)
data = r.json()
print('   Success:', data.get('success'))
print('   Rows:', data.get('results', [{}])[0].get('rowsAffected', 0))

# 4. Get Tables
print('\n4. Get Tables:')
r = requests.get(base_url + '/tables', headers=headers)
print('   Tables:', r.json())

print('\n=== Test Complete ===')