from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Claim(BaseModel):
    customer_id: int
    card_id: int
    type_id: int
    status_id: int
    opened_at: datetime
    closed_at: Optional[datetime] = None
    amount: float
    currency: str
    channel: str
    reference_id: str
    description: str
