from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from deta import Deta
import pymysql
import bcrypt
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============== DETA NoSQL (Auth/User) ===============
deta = Deta()
users_db = deta.Base("users")

# =============== MySQL (SQL Queries) ===============
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'admin'),
    'database': os.getenv('MYSQL_DATABASE', 'sqllab')
}

def get_mysql():
    return pymysql.connect(**MYSQL_CONFIG)

# =============== AUTH ROUTES ===============

@app.post("/api/auth/signup")
def signup(data: dict):
    email = data.get("email")
    name = data.get("name")
    password = data.get("password")
    
    if not all([email, name, password]):
        raise HTTPException(status_code=400, detail="All fields required")
    
    # Check if user exists
    existing = users_db.get(email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    # Hash password
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    # Save to Deta (NoSQL)
    users_db.put({
        "key": email,
        "name": name,
        "password": hashed,
        "role": "student"
    })
    
    return {"message": "Signup successful", "email": email}

@app.post("/api/auth/login")
def login(data: dict):
    email = data.get("email")
    password = data.get("password")
    
    if not all([email, password]):
        raise HTTPException(status_code=400, detail="All fields required")
    
    # Get from Deta
    user = users_db.get(email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check password
    if not bcrypt.checkpw(password.encode(), user["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return {
        "message": "Login successful",
        "user": {
            "email": user["key"],
            "name": user["name"],
            "role": user.get("role", "student")
        }
    }

@app.get("/api/auth/profile/{email}")
def get_profile(email: str):
    user = users_db.get(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": {"email": user["key"], "name": user["name"], "role": user.get("role")}}

# =============== SQL QUERY ROUTES ===============

@app.post("/api/query/execute")
def execute_query(data: dict):
    query = data.get("query", "")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query required")
    
    # Security - block dangerous
    forbidden = ['DROP DATABASE', 'GRANT', 'REVOKE', 'INFORMATION_SCHEMA']
    for word in forbidden:
        if word in query.upper():
            raise HTTPException(status_code=400, detail=f"Blocked: {word}")
    
    # Auto add LIMIT to SELECT
    if query.upper().strip().startswith('SELECT') and 'LIMIT' not in query.upper():
        query = query.rstrip(';') + ' LIMIT 100'
    
    try:
        db = get_mysql()
        cursor = db.cursor()
        cursor.execute(query)
        
        if query.upper().strip().startswith('SELECT'):
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return {
                "success": True,
                "columns": columns,
                "results": results,
                "row_count": len(results)
            }
        else:
            db.commit()
            return {
                "success": True,
                "row_count": cursor.rowcount,
                "message": "Query executed successfully"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        try:
            db.close()
        except:
            pass

@app.get("/api/tables")
def get_tables():
    try:
        db = get_mysql()
        cursor = db.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        db.close()
        return {"tables": [t[0] for t in tables]}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/health")
def health():
    try:
        db = get_mysql()
        db.close()
        return {"status": "ok", "mysql": "connected", "deta": "connected"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)