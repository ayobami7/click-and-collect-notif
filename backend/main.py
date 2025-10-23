from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import socketio
import uvicorn

from database import get_db, init_db
from models import Collection, CollectionStatus

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
            "POST /api/collect": "Customer creates collection request",
            "GET /api/collections": "Get all collections",
            "PATCH /api/collections/{id}/complete": "Mark collection as complete",
            "GET /api/health": "Health check"
        }
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/collect", response_model=CollectionResponse)
async def create_collection(
    request: CollectionRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Create new collection in database
        collection = Collection(
            customer_name=request.customer_name,
            barcode=request.barcode,
            status=CollectionStatus.PENDING.value
        )
        
        db.add(collection)
        await db.commit()
        await db.refresh(collection)
        
        # Emit real-time notification to all connected staff devices
        await sio.emit('new_collection', {
            "id": collection.id,
            "customer_name": collection.customer_name,
            "barcode": collection.barcode,
            "timestamp": collection.created_at.isoformat(),
            "message": f"{collection.customer_name} is waiting for collection"
        })
        
        print(f"New collection: {collection.customer_name} - {collection.barcode}")
        
        return {
            "id": collection.id,
            "customer_name": collection.customer_name,
            "barcode": collection.barcode,
            "timestamp": collection.created_at.isoformat(),
            "status": collection.status
        }
        
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
    await db.commit()
    await db.refresh(collection)
    
    # Notify staff that collection is complete
    await sio.emit('collection_completed', {
        "id": collection.id,
        "customer_name": collection.customer_name
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
        host="0.0.0.0",
        port=8000,
        reload=True
    )