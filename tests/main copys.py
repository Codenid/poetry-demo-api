from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
import schemas

app = FastAPI()

origins = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

host_name = "localhost"
port_number = "3306"
user_name = "root"
password_db = "rootpass"
database_name = "creditcard_claims"

@app.get("/")
def get_echo_test():
    return {"message": "Echo Test OK"}

@app.get("/claims")
def get_claims():
    mydb = mysql.connector.connect(host=host_name, port=port_number, user=user_name, password=password_db, database=database_name)
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM claims")
    result = cursor.fetchall()
    cursor.close()
    mydb.close()
    return {"claims": result}

@app.get("/claims/{id}")
def get_claim(id: int):
    mydb = mysql.connector.connect(host=host_name, port=port_number, user=user_name, password=password_db, database=database_name)
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM claims WHERE id = %s", (id,))
    result = cursor.fetchone()
    cursor.close()
    mydb.close()
    return {"claim": result}

@app.post("/claims")
def add_claim(item: schemas.Claim):
    mydb = mysql.connector.connect(host=host_name, port=port_number, user=user_name, password=password_db, database=database_name)
    cursor = mydb.cursor()
    sql = """
        INSERT INTO claims (customer_id, card_id, type_id, status_id, opened_at, closed_at, amount, currency, channel, reference_id, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    val = (
        item.customer_id, item.card_id, item.type_id, item.status_id,
        item.opened_at, item.closed_at, item.amount, item.currency,
        item.channel, item.reference_id, item.description
    )
    cursor.execute(sql, val)
    mydb.commit()
    cursor.close()
    mydb.close()
    return {"message": "Claim added successfully"}

@app.put("/claims/{id}")
def update_claim(id: int, item: schemas.Claim):
    mydb = mysql.connector.connect(host=host_name, port=port_number, user=user_name, password=password_db, database=database_name)
    cursor = mydb.cursor()
    sql = """
        UPDATE claims SET customer_id=%s, card_id=%s, type_id=%s, status_id=%s,
        opened_at=%s, closed_at=%s, amount=%s, currency=%s, channel=%s,
        reference_id=%s, description=%s WHERE id=%s
    """
    val = (
        item.customer_id, item.card_id, item.type_id, item.status_id,
        item.opened_at, item.closed_at, item.amount, item.currency,
        item.channel, item.reference_id, item.description, id
    )
    cursor.execute(sql, val)
    mydb.commit()
    cursor.close()
    mydb.close()
    return {"message": "Claim updated successfully"}

@app.delete("/claims/{id}")
def delete_claim(id: int):
    mydb = mysql.connector.connect(host=host_name, port=port_number, user=user_name, password=password_db, database=database_name)
    cursor = mydb.cursor()
    cursor.execute("DELETE FROM claims WHERE id = %s", (id,))
    mydb.commit()
    cursor.close()
    mydb.close()
    return {"message": "Claim deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
