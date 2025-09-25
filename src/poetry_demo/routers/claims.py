from fastapi import APIRouter, Depends
from ..db import get_connection
from ..models.schemas import Claim
from ..utils.pagination import pagination_params

router = APIRouter()

@router.get("/claims")
def get_claims(pagination: dict = Depends(pagination_params)):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM claims LIMIT %s OFFSET %s", (pagination["limit"], pagination["skip"]))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"claims": result, **pagination}

@router.get("/claims/{id}")
def get_claim(id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM claims WHERE id = %s", (id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return {"claim": result}

@router.post("/claims")
def add_claim(item: Claim):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO claims (customer_id, card_id, type_id, status_id, opened_at, closed_at,
        amount, currency, channel, reference_id, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    val = (
        item.customer_id, item.card_id, item.type_id, item.status_id,
        item.opened_at, item.closed_at, item.amount, item.currency,
        item.channel, item.reference_id, item.description
    )
    cursor.execute(sql, val)
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Claim added successfully"}

@router.put("/claims/{id}")
def update_claim(id: int, item: Claim):
    conn = get_connection()
    cursor = conn.cursor()
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
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Claim updated successfully"}

@router.delete("/claims/{id}")
def delete_claim(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM claims WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Claim deleted successfully"}
