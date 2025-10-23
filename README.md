# Click & Collect Notification System

A real-time notification system for retail click & collect services. Customers scan barcodes at collection points, and staff receive instant notifications on their devices.

## Project Overview

**Use Case**: Customer comes to Click & Collect counter → Scans barcode → Staff device receives real-time notification → Staff retrieves parcel

**Tech Stack**:
- **Backend**: Python, FastAPI, Socket.IO
- **Database**: SQLite (development) / PostgreSQL (production)
- **Real-time**: WebSocket notifications
- **API**: RESTful endpoints

## Project Structure

```
click-and-collect/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Database models
│   ├── database.py          # Database configuration
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment template
│   └── .env                 
├── frontend/                
└── README.md               
```

## Quick Start

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone or create the project**
```bash
mkdir click-and-collect
cd click-and-collect
```

2. **Set up the backend**
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

3. **Run the server**
```bash
python main.py
```

The server will start at `http://localhost:8000`

The database (`collections.db`) will be created automatically on first run.

## API Endpoints

### Customer Endpoints

**Create Collection Request**
```bash
POST /api/collect
Content-Type: application/json

{
  "customer_name": "John Doe",
  "barcode": "ABC123456"
}
```

### Staff Endpoints

**Get All Collections**
```bash
GET /api/collections

GET /api/collections?status=pending
```

**Get Single Collection**
```bash
GET /api/collections/{id}
```

**Mark Collection as Complete**
```bash
PATCH /api/collections/{id}/complete
```

**Delete Collection**
```bash
DELETE /api/collections/{id}
```

### System Endpoints

**Health Check**
```bash
GET /api/health
```

**API Documentation**
```bash
GET /docs  # Swagger UI
GET /redoc # ReDoc
```

## Real-time Notifications

Staff devices connect via Socket.IO to receive real-time updates:

**Events Emitted to Staff:**
- `new_collection` - When customer requests collection
- `collection_completed` - When collection is marked complete
- `connection_status` - Connection confirmation

## Testing the API

### Using cURL

```bash
# Create a collection
curl -X POST http://localhost:8000/api/collect \
  -H "Content-Type: application/json" \
  -d '{"customer_name": "Alice Smith", "barcode": "XYZ789"}'

# Get all pending collections
curl http://localhost:8000/api/collections?status=pending

# Complete a collection
curl -X PATCH http://localhost:8000/api/collections/1/complete
```

### Using Python

```python
import requests

# Create collection
response = requests.post(
    "http://localhost:8000/api/collect",
    json={"customer_name": "Bob Jones", "barcode": "ABC123"}
)
print(response.json())

# Get collections
response = requests.get("http://localhost:8000/api/collections")
print(response.json())
```

## Database

### SQLite
- File: `collections.db` (created automatically)

### PostgreSQL

1. Install PostgreSQL driver:
```bash
pip install asyncpg
```

2. Update `.env`:
```bash
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/collections_db
```

3. Restart the server

### Database Schema

**collections** table:
- `id` - Primary key (auto-increment)
- `customer_name` - Customer's name
- `barcode` - Scanned barcode
- `status` - pending/completed/cancelled
- `created_at` - Timestamp when created
- `updated_at` - Timestamp when last updated

## 🔧 Configuration

Edit `.env` file:

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./collections.db

# Server
HOST=0.0.0.0
PORT=8000
```

## Dependencies

- **fastapi** - Modern web framework
- **uvicorn** - ASGI server
- **python-socketio** - Real-time WebSocket
- **sqlalchemy** - Database ORM
- **aiosqlite** - Async SQLite driver
- **pydantic** - Data validation
- **python-dotenv** - Environment variables

## Development

### Adding New Features

1. **Add Database Field**:
   - Update `models.py`
   - Restart server (tables auto-update in dev)

2. **Add API Endpoint**:
   - Add route in `main.py`
   - Use `Depends(get_db)` for database access

3. **Add Real-time Event**:
   - Emit event with `await sio.emit('event_name', data)`

### Resetting Database

```bash
# Stop server, then:
rm collections.db
# Restart server - fresh database created
```

##  Security Notes

For production:
1. Use PostgreSQL instead of SQLite
2. Set proper CORS origins (not `*`)
3. Add authentication for staff endpoints
4. Use HTTPS
5. Add rate limiting
6. Validate and sanitize inputs

## License

This is a side project / learning project. Feel free to use and modify.



