# main.py
import os
import random
import string
from datetime import datetime, timedelta
from typing import List, Optional

#from dotenv import load_dotenv
#load_dotenv()

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import (
    create_engine, Column, Integer, BigInteger, String, Enum, DateTime, DECIMAL, CHAR,
    ForeignKey, select, and_, or_
)
from sqlalchemy.orm import declarative_base, relationship, Session

# --- Config ---
DB_HOST = os.getenv("MYSQL_HOST", "mysql_c")
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DB", "creditcard_claims")
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASS = os.getenv("MYSQL_PASSWORD", "rootpass")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

Base = declarative_base()
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

# --- ORM Models ---
class Customer(Base):
    __tablename__ = "customers"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_type = Column(Enum("DNI", "CE", "PAS"), nullable=False)
    document_number = Column(String(20), nullable=False)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120))
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Card(Base):
    __tablename__ = "cards"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id"), nullable=False)
    issuer = Column(String(60), nullable=False)
    network = Column(Enum("VISA", "MASTERCARD", "AMEX"), nullable=False)
    last4 = Column(CHAR(4), nullable=False)
    pan_tokenized = Column(String(64), nullable=False)
    status = Column(Enum("ACTIVE", "BLOCKED", "EXPIRED"), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    customer = relationship("Customer")

class ClaimType(Base):
    __tablename__ = "claim_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(80), nullable=False)
    description = Column(String(255))

class ClaimStatus(Base):
    __tablename__ = "claim_statuses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(80), nullable=False)

class Claim(Base):
    __tablename__ = "claims"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id"), nullable=False)
    card_id = Column(BigInteger, ForeignKey("cards.id"), nullable=False)
    type_id = Column(Integer, ForeignKey("claim_types.id"), nullable=False)
    status_id = Column(Integer, ForeignKey("claim_statuses.id"), nullable=False)
    opened_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime)
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(CHAR(3), nullable=False)
    channel = Column(Enum("WEB", "CALL_CENTER", "BRANCH", "APP"), nullable=False)
    reference_id = Column(String(40), unique=True, nullable=False)
    description = Column(String(500), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customer = relationship("Customer")
    card = relationship("Card")
    type = relationship("ClaimType")
    status = relationship("ClaimStatus")

# --- Pydantic Schemas ---
class ClaimOut(BaseModel):
    id: int
    reference_id: str
    opened_at: datetime
    closed_at: Optional[datetime]
    amount: float
    currency: str
    channel: str
    description: str
    type_code: str
    type_name: str
    status_code: str
    status_name: str
    customer_document_type: str
    customer_document_number: str
    customer_full_name: str
    card_last4: str
    card_network: str
    card_issuer: str

    class Config:
        from_attributes = True

class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int

class ClaimsResponse(BaseModel):
    data: List[ClaimOut]
    meta: PageMeta

# --- Embedded dataset (fallback if DB empty) ---
random.seed(42)

TYPE_CATALOG = [
    ("FRAUD", "Transacción fraudulenta"),
    ("CHARGE_BACK", "Reversión de cargo"),
    ("DOUBLE_CHARGE", "Doble cargo"),
    ("NOT_RECEIVED", "Producto no recibido"),
    ("SERVICE_QUALITY", "Calidad de servicio"),
]
STATUS_CATALOG = [
    ("OPEN", "Abierto"),
    ("IN_REVIEW", "En revisión"),
    ("RESOLVED", "Resuelto"),
    ("REJECTED", "Rechazado"),
]
NETWORKS = ["VISA", "MASTERCARD", "AMEX"]
CHANNELS = ["WEB", "CALL_CENTER", "BRANCH", "APP"]
ISSUERS = ["Banco Uno", "Banco Dos", "Banco Tres"]

def _rand_last4():
    return "".join(random.choices(string.digits, k=4))

def _token():
    return "".join(random.choices(string.ascii_letters + string.digits, k=32))

def generate_sample_claims(n: int = 100) -> List[ClaimOut]:
    base_date = datetime.utcnow() - timedelta(days=120)
    data: List[ClaimOut] = []
    for i in range(n):
        tcode, tname = random.choice(TYPE_CATALOG)
        scode, sname = random.choice(STATUS_CATALOG)
        network = random.choice(NETWORKS)
        channel = random.choice(CHANNELS)
        issuer = random.choice(ISSUERS)
        opened = base_date + timedelta(days=random.randint(0, 120), hours=random.randint(0, 23))
        closed = opened + timedelta(days=random.randint(1, 30)) if scode in ("RESOLVED", "REJECTED") else None
        amount = round(random.uniform(10, 2500), 2)
        currency = random.choice(["PEN", "USD"])
        last4 = _rand_last4()
        doc_type = random.choice(["DNI", "CE", "PAS"])
        doc_number = "".join(random.choices(string.digits, k=8))
        full_name = f"Cliente {i+1}"
        reference = f"REF-{i+1:05d}"
        desc = f"{tname} sobre compra en establecimiento {random.randint(1000, 9999)}"
        data.append(ClaimOut(
            id=i+1,
            reference_id=reference,
            opened_at=opened,
            closed_at=closed,
            amount=amount,
            currency=currency,
            channel=channel,
            description=desc,
            type_code=tcode,
            type_name=tname,
            status_code=scode,
            status_name=sname,
            customer_document_type=doc_type,
            customer_document_number=doc_number,
            customer_full_name=full_name,
            card_last4=last4,
            card_network=network,
            card_issuer=issuer
        ))
    return data

EMBEDDED_DATASET = generate_sample_claims(100)

# --- App ---
app = FastAPI(
    title="API de Reclamos de Tarjetas de Crédito",
    version="1.0.0",
    description="Consulta de reclamos con filtros por fechas, id, tipo, documento de cliente, estado y tarjeta.",
)

def db_has_claims(session: Session) -> bool:
    return session.execute(select(Claim.id).limit(1)).scalar() is not None

@app.get("/claims", response_model=ClaimsResponse, summary="Listar reclamos con filtros")
def list_claims(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    claim_id: Optional[int] = None,
    type_code: Optional[str] = None,
    status_code: Optional[str] = None,
    customer_document_type: Optional[str] = None,
    customer_document_number: Optional[str] = None,
    card_last4: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Filtros soportados:
    - claim_id: id del reclamo exacto
    - type_code: FRAUD, CHARGE_BACK, DOUBLE_CHARGE, NOT_RECEIVED, SERVICE_QUALITY
    - status_code: OPEN, IN_REVIEW, RESOLVED, REJECTED
    - customer_document_type: DNI, CE, PAS
    - customer_document_number: número del documento
    - card_last4: últimos 4 dígitos
    - start_date / end_date: rango de fechas sobre opened_at
    """
    with Session(engine) as session:
        if not db_has_claims(session):
            # Fallback: filtrar sobre dataset embebido
            items = EMBEDDED_DATASET
            def match(c: ClaimOut) -> bool:
                conds = []
                if claim_id is not None: conds.append(c.id == claim_id)
                if type_code: conds.append(c.type_code == type_code)
                if status_code: conds.append(c.status_code == status_code)
                if customer_document_type: conds.append(c.customer_document_type == customer_document_type)
                if customer_document_number: conds.append(c.customer_document_number == customer_document_number)
                if card_last4: conds.append(c.card_last4 == card_last4)
                if start_date: conds.append(c.opened_at >= start_date)
                if end_date: conds.append(c.opened_at <= end_date)
                return all(conds)
            filtered = list(filter(match, items))
            total = len(filtered)
            start = (page - 1) * page_size
            endi = start + page_size
            return ClaimsResponse(
                data=filtered[start:endi],
                meta=PageMeta(page=page, page_size=page_size, total=total)
            )

        # Query sobre BD
        stmt = (
            select(
                Claim.id, Claim.reference_id, Claim.opened_at, Claim.closed_at,
                Claim.amount, Claim.currency, Claim.channel, Claim.description,
                ClaimType.code, ClaimType.name, ClaimStatus.code, ClaimStatus.name,
                Customer.document_type, Customer.document_number, Customer.full_name,
                Card.last4, Card.network, Card.issuer
            )
            .join(ClaimType, Claim.type_id == ClaimType.id)
            .join(ClaimStatus, Claim.status_id == ClaimStatus.id)
            .join(Customer, Claim.customer_id == Customer.id)
            .join(Card, Claim.card_id == Card.id)
        )

        filters = []
        if claim_id is not None:
            filters.append(Claim.id == claim_id)
        if type_code:
            filters.append(ClaimType.code == type_code)
        if status_code:
            filters.append(ClaimStatus.code == status_code)
        if customer_document_type:
            filters.append(Customer.document_type == customer_document_type)
        if customer_document_number:
            filters.append(Customer.document_number == customer_document_number)
        if card_last4:
            filters.append(Card.last4 == card_last4)
        if start_date:
            filters.append(Claim.opened_at >= start_date)
        if end_date:
            filters.append(Claim.opened_at <= end_date)

        if filters:
            stmt = stmt.where(and_(*filters))

        total = session.execute(
            select(func_count := Integer).select_from(stmt.subquery())  # placeholder count
        )
        # SQLAlchemy 2.x no permite contar así directamente; hacemos count con subquery real:
        subq = stmt.subquery()
        total = session.execute(select(func_count := func_count).where(False))  # dummy
        # Simpler: compute total with second query
        total = session.execute(select(func_count := func_count)).fetchall()  # workaround (we'll compute via length of all fetch)

        rows = session.execute(stmt).all()
        total_count = len(rows)
        start = (page - 1) * page_size
        endi = start + page_size
        page_rows = rows[start:endi]

        def to_out(r) -> ClaimOut:
            return ClaimOut(
                id=r[0],
                reference_id=r[1],
                opened_at=r[2],
                closed_at=r[3],
                amount=float(r[4]),
                currency=r[5],
                channel=r[6],
                description=r[7],
                type_code=r[8],
                type_name=r[9],
                status_code=r[10],
                status_name=r[11],
                customer_document_type=r[12],
                customer_document_number=r[13],
                customer_full_name=r[14],
                card_last4=r[15],
                card_network=r[16],
                card_issuer=r[17]
            )

        return ClaimsResponse(
            data=[to_out(r) for r in page_rows],
            meta=PageMeta(page=page, page_size=page_size, total=total_count)
        )

@app.post("/seed", summary="Sembrar dataset embebido en la BD")
def seed_db():
    with Session(engine) as session:
        # cargar catálogos si no existen
        ct_map = {c[0]: c[1] for c in TYPE_CATALOG}
        cs_map = {c[0]: c[1] for c in STATUS_CATALOG}

        for code, name in TYPE_CATALOG:
            if not session.execute(select(ClaimType).where(ClaimType.code == code)).scalar():
                session.add(ClaimType(code=code, name=name, description=None))

        for code, name in STATUS_CATALOG:
            if not session.execute(select(ClaimStatus).where(ClaimStatus.code == code)).scalar():
                session.add(ClaimStatus(code=code, name=name))

        session.commit()

        # mapas id de catálogos
        type_ids = {t.code: t.id for t in session.execute(select(ClaimType)).scalars()}
        status_ids = {s.code: s.id for s in session.execute(select(ClaimStatus)).scalars()}

        created = 0
        for c in EMBEDDED_DATASET:
            # cliente
            cust = session.execute(
                select(Customer).where(
                    Customer.document_type == c.customer_document_type,
                    Customer.document_number == c.customer_document_number
                )
            ).scalar()
            if not cust:
                cust = Customer(
                    document_type=c.customer_document_type,
                    document_number=c.customer_document_number,
                    full_name=c.customer_full_name,
                    email=None, phone=None
                )
                session.add(cust)
                session.flush()

            # tarjeta (una por last4/issuer/network)
            card = session.execute(
                select(Card).where(
                    Card.customer_id == cust.id,
                    Card.last4 == c.card_last4,
                    Card.issuer == c.card_issuer,
                    Card.network == c.card_network
                )
            ).scalar()
            if not card:
                card = Card(
                    customer_id=cust.id,
                    issuer=c.card_issuer,
                    network=c.card_network,
                    last4=c.card_last4,
                    pan_tokenized=_token(),
                    status="ACTIVE"
                )
                session.add(card)
                session.flush()

            # reclamo (por referencia única)
            exists = session.execute(
                select(Claim).where(Claim.reference_id == c.reference_id)
            ).scalar()
            if not exists:
                claim = Claim(
                    customer_id=cust.id,
                    card_id=card.id,
                    type_id=type_ids[c.type_code],
                    status_id=status_ids[c.status_code],
                    opened_at=c.opened_at,
                    closed_at=c.closed_at,
                    amount=c.amount,
                    currency=c.currency,
                    channel=c.channel,
                    reference_id=c.reference_id,
                    description=c.description
                )
                session.add(claim)
                created += 1

        session.commit()
        return {"inserted": created}

# Health
@app.get("/health", summary="Estado del servicio")
def health():
    try:
        with Session(engine) as session:
            session.execute(select(1))
        return {"status": "ok", "db": "reachable"}
    except Exception:
        return {"status": "ok", "db": "unreachable", "note": "sirviendo dataset embebido si tabla vacía"}
