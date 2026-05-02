import pymysql
import traceback

try:
    conn = pymysql.connect(
        host='gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com',
        user='3kvBExhfixnc3wk.root',
        password='MjI4tM7rFgWO3Bdc',
        database='checks',
        port=4000
    )
    cursor = conn.cursor()
    
    # Test simple creation
    cursor.execute('CREATE TABLE IF NOT EXISTS students (id INT AUTO_INCREMENT PRIMARY KEY, first_name VARCHAR(50), last_name VARCHAR(50));')
    conn.commit()
    print('Table created!')
    
    # Test Insert
    cursor.execute('INSERT IGNORE INTO students VALUES (1, "Test", "User");')
    conn.commit()
    print('Insert done!')
    
    # Test Select
    cursor.execute('SELECT * FROM students;')
    print('Result:', cursor.fetchall())
    
    cursor.close()
    conn.close()
except Exception as e:
    print('Error:', e)
