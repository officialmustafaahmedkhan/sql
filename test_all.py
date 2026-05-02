import requests, time, random
time.sleep(15)

base = 'https://sql-lab-new.onrender.com/api'
print('=== TESTING ALL NEW FEATURES ===')

# 1. Health
r = requests.get(base + '/health')
print('1. Health:', 'OK' if r.status_code == 200 else 'FAIL')

# 2. Signup + verify to get admin token
email = f'admin{random.randint(10000,99999)}@test.com'
r = requests.post(base + '/auth/signup', json={'name':'Admin','email':email,'password':'123456'})
if r.status_code == 201:
    otp = r.json().get('otp')
    r = requests.post(base + '/auth/verify-otp', json={'email':email,'otp':otp})
    if r.status_code == 200:
        token = r.json().get('token')
        
        # 3. Admin stats
        r = requests.get(base + '/admin/stats', headers={'Authorization': 'Bearer ' + token})
        print('2. Admin Stats:', 'OK' if r.status_code == 200 else 'FAIL')
        if r.status_code == 200:
            print('   ', r.json())
        
        # 4. Get users
        r = requests.get(base + '/admin/users', headers={'Authorization': 'Bearer ' + token})
        print('3. Get Users:', 'OK' if r.status_code == 200 else 'FAIL')
        
        # 5. Practices
        r = requests.get(base + '/practices')
        data = r.json()
        count = len(data.get('practices', []))
        print('4. Practices:', 'OK' if r.status_code == 200 else 'FAIL', f'({count} exercises)')
        
        # 6. Query
        r = requests.post(base + '/query/execute', json={'query': 'SELECT * FROM students'}, headers={'Authorization': 'Bearer ' + token})
        print('5. Query:', 'OK' if r.json().get('success') else 'FAIL')
        
        print('=== ALL TESTS DONE ===')
