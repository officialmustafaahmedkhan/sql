import pymysql

conn = pymysql.connect(
    host='gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com',
    user='3kvBExhfixnc3wk.root',
    password='MjI4tM7rFgWO3Bdc',
    database='checks',
    port=4000,
    ssl={'check_hostname': True}
)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS students (id INT AUTO_INCREMENT PRIMARY KEY, first_name VARCHAR(50), last_name VARCHAR(50));')
conn.commit()
print('Success!')
cursor.close()
conn.close()
