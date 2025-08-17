from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
from uuid import uuid4
from typing import Dict, Optional
import asyncio

app = FastAPI()

# In-memory DBs
payments_db: Dict[str, dict] = {}
transactions_db: Dict[str, dict] = {}


# Enums
class PaymentStatus(str, Enum):
    created = "created"
    authorized = "authorized"
    settled = "settled"
    failed = "failed"


class TransactionStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    declined = "declined"
    settled = "settled"
    chargeback = "chargeback"


# Models
class CreatePaymentRequest(BaseModel):
    amount: float
    currency: str
    description: Optional[str]


class PaymentResponse(BaseModel):
    payment_id: str
    status: PaymentStatus


class CreateTransactionRequest(BaseModel):
    payment_id: str
    card_number: str
    exp_date: str
    cvv: str


class TransactionResponse(BaseModel):
    transaction_id: str
    payment_id: str
    status: TransactionStatus


class PaymentStatusResponse(BaseModel):
    payment_id: str
    status: PaymentStatus
    last_transaction_status: Optional[TransactionStatus]


# Create Payment
@app.post("/payments", response_model=PaymentResponse)
def create_payment(req: CreatePaymentRequest):
    payment_id = str(uuid4())
    payments_db[payment_id] = {
        "status": PaymentStatus.created,
        "amount": req.amount,
        "currency": req.currency,
        "description": req.description,
        "transactions": [],
    }
    return PaymentResponse(payment_id=payment_id, status=PaymentStatus.created)


# Create Transaction (Async Simulation Trigger)
@app.post("/transactions", response_model=TransactionResponse)
async def create_transaction(req: CreateTransactionRequest):
    if req.payment_id not in payments_db:
        raise HTTPException(status_code=404, detail="Payment not found")

    tx_id = str(uuid4())
    transaction = {
        "transaction_id": tx_id,
        "payment_id": req.payment_id,
        "status": TransactionStatus.pending,
    }
    transactions_db[tx_id] = transaction
    payments_db[req.payment_id]["transactions"].append(tx_id)

    # Simulate async callback in background
    asyncio.create_task(simulate_gateway_callback(tx_id))

    return TransactionResponse(**transaction)


# Simulated Asynchronous Callback from Payment Gateway
async def simulate_gateway_callback(transaction_id: str):
    await asyncio.sleep(2)  # simulate network delay

    tx = transactions_db[transaction_id]
    card_first_digit = payments_db[tx["payment_id"]]["amount"] % 10  # fake logic

    # Simulate logic
    if card_first_digit < 5:
        tx["status"] = TransactionStatus.approved
        update_payment_status(tx["payment_id"], PaymentStatus.authorized)
    else:
        tx["status"] = TransactionStatus.declined
        update_payment_status(tx["payment_id"], PaymentStatus.failed)

    # Later callback: simulate settlement
    await asyncio.sleep(2)
    if tx["status"] == TransactionStatus.approved:
        tx["status"] = TransactionStatus.settled
        update_payment_status(tx["payment_id"], PaymentStatus.settled)


# Update payment status based on transactions
def update_payment_status(payment_id: str, new_status: PaymentStatus):
    current = payments_db[payment_id]["status"]
    status_order = [
        PaymentStatus.created,
        PaymentStatus.authorized,
        PaymentStatus.settled,
        PaymentStatus.failed,
    ]
    if status_order.index(new_status) > status_order.index(current):
        payments_db[payment_id]["status"] = new_status


# Get Payment Status
@app.get("/payments/{payment_id}", response_model=PaymentStatusResponse)
def get_payment(payment_id: str):
    payment = payments_db.get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    last_tx_id = payment["transactions"][-1] if payment["transactions"] else None
    last_tx_status = transactions_db[last_tx_id]["status"] if last_tx_id else None

    return PaymentStatusResponse(
        payment_id=payment_id,
        status=payment["status"],
        last_transaction_status=last_tx_status,
    )
