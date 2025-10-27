from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import socketio
import json
import uvicorn
import os
from dotenv import load_dotenv


from database import get_db, init_db
from models import Collection, CollectionStatus
from utils import generate_barcode, generate_order_number, validate_barcode

load_dotenv()

# Socket.IO setup
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)

# FastAPI app
app = FastAPI(title="Click & Collect Notification System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Combine Socket.IO with FastAPI
socket_app = socketio.ASGIApp(sio, app)

# Pydantic models
class OrderItem(BaseModel):
    name: str
    quantity: int
    
class OrderRequest(BaseModel):
    customer_name: str
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None
    items: Optional[List[OrderItem]] = None
    order_number: Optional[str] = None

class CollectionRequest(BaseModel):
    customer_name: str
    barcode: str

class CollectionResponse(BaseModel):
    id: int
    customer_name: str
    barcode: str
    timestamp: str
    status: str

# Startup event
@app.on_event("startup")
async def startup_event():
    await init_db()
    print("Server started successfully!")

# Socket.IO events
@sio.event
async def connect(sid, environ):
    print(f"Staff device connected: {sid}")
    await sio.emit('connection_status', {'message': 'Connected to notification system'}, room=sid)

@sio.event
async def disconnect(sid):
    print(f"Staff device disconnected: {sid}")

# REST API endpoints
@app.get("/")
async def root():
    return {
        "message": "Click & Collect Notification API",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/orders": "Create new order (generates barcode)",
            "PATCH /api/orders/{id}/ready": "Mark order as ready for collection",
            "POST /api/collect": "Customer creates collection request",
            "GET /api/collections": "Get all collections",
            "PATCH /api/collections/{id}/complete": "Mark collection as complete",
            "GET /api/health": "Health check"
        }
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/orders")
async def create_order(
    request: OrderRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    CREATE ORDER - When customer places an order
    This generates a barcode and creates the order in the system
    """
    try:
        # Generate unique barcode
        barcode = generate_barcode()
        
        # Generate order number if not provided
        order_number = request.order_number or generate_order_number()
        
        # Convert items to JSON string if provided
        items_json = None
        if request.items:
            items_json = json.dumps([item.dict() for item in request.items])
        
        # Create order in database
        order = Collection(
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            customer_phone=request.customer_phone,
            barcode=barcode,
            order_number=order_number,
            items=items_json,
            status=CollectionStatus.PENDING.value  # Order is being prepared
        )
        
        db.add(order)
        await db.commit()
        await db.refresh(order)
        
        print(f"✅ New order created: {order_number} for {request.customer_name}")
        print(f"   Barcode: {barcode}")
        
        return {
            "id": order.id,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "barcode": barcode,
            "order_number": order_number,
            "items": request.items,
            "status": order.status,
            "timestamp": order.created_at.isoformat(),
            "message": "Order created successfully. Customer will receive barcode for collection."
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/orders/{order_id}/ready")
async def mark_order_ready(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    MARK ORDER READY - When staff prepares the order
    Changes status from PENDING to READY
    """
    result = await db.execute(
        select(Collection).where(Collection.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = CollectionStatus.READY.value
    await db.commit()
    await db.refresh(order)
    
    # Optionally notify customer via email/SMS that order is ready
    print(f"✅ Order {order.order_number} is ready for collection")
    
    return {
        **order.to_dict(),
        "message": "Order marked as ready for collection"
    }

@app.post("/api/collect", response_model=CollectionResponse)
# this is where the customer creates a collection request
async def create_collection(
    request: CollectionRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Validate barcode format
        if not validate_barcode(request.barcode):
            raise HTTPException(
                status_code=400, 
                detail="Invalid barcode format"
            )
        
        # Find order by barcode
        result = await db.execute(
            select(Collection).where(Collection.barcode == request.barcode)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=404, 
                detail="Order not found. Please check your barcode."
            )
        
        # Check if order is ready
        if order.status == CollectionStatus.PENDING.value:
            raise HTTPException(
                status_code=400,
                detail="Order is still being prepared. Please wait."
            )
        
        if order.status == CollectionStatus.COLLECTED.value:
            raise HTTPException(
                status_code=400,
                detail="This order has already been collected."
            )
        
        # Verify customer name matches
        if order.customer_name.lower() != request.customer_name.lower():
            print(f"Name mismatch: Expected '{order.customer_name}', got '{request.customer_name}'")
        
        # Emit real-time notification to staff devices
        await sio.emit('new_collection', {
            "id": order.id,
            "customer_name": order.customer_name,
            "barcode": order.barcode,
            "order_number": order.order_number,
            "items": order.items,
            "timestamp": datetime.now().isoformat(),
            "message": f"{order.customer_name} is waiting at collection point"
        })
        
        print(f"Collection notification: {order.customer_name} - Order {order.order_number}")
        
        return {
            "id": order.id,
            "customer_name": order.customer_name,
            "barcode": order.barcode,
            "timestamp": order.created_at.isoformat(),
            "status": order.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/collections")
async def get_collections(
    status: str = None,
    db: AsyncSession = Depends(get_db)
):

    try:
        query = select(Collection)
        
        if status:
            query = query.where(Collection.status == status)
        
        query = query.order_by(Collection.created_at.desc())
        
        result = await db.execute(query)
        collections = result.scalars().all()
        
        return {
            "collections": [c.to_dict() for c in collections],
            "count": len(collections)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/collections/{collection_id}")
async def get_collection(
    collection_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Collection).where(Collection.id == collection_id)
    )
    collection = result.scalar_one_or_none()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    return collection.to_dict()

@app.patch("/api/collections/{collection_id}/complete")
async def complete_collection(
    collection_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Collection).where(Collection.id == collection_id)
    )
    collection = result.scalar_one_or_none()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    collection.status = CollectionStatus.COMPLETED.value
    collection.collected_at = datetime.now()
    await db.commit()
    await db.refresh(collection)
    
    # Notify staff that collection is complete
    await sio.emit('collection_completed', {
        "id": collection.id,
        "customer_name": collection.customer_name,
        "order_number": collection.order_number
    })
    
    return collection.to_dict()

@app.delete("/api/collections/{collection_id}")
async def delete_collection(
    collection_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Collection).where(Collection.id == collection_id)
    )
    collection = result.scalar_one_or_none()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    await db.delete(collection)
    await db.commit()
    
    return {"message": "Collection deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(
        "main:socket_app",
        host=os.getenv("HOST", "localhost"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )