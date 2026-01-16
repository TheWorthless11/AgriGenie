# AgriGenie API Documentation

## Overview

AgriGenie API provides endpoints for accessing the agricultural marketplace platform. The API supports creating users, managing crops, orders, and accessing AI-powered features.

## Base URL
```
http://localhost:8000/api/
```

## Authentication

Most endpoints require authentication. Use Django's session authentication or token-based authentication.

### Session Authentication
Include your session cookie from login.

### Token Authentication (for future implementation)
```
Authorization: Bearer your_token_here
```

## Response Format

All responses are in JSON format:

### Success Response
```json
{
    "status": "success",
    "data": {...},
    "message": "Operation completed successfully"
}
```

### Error Response
```json
{
    "status": "error",
    "error": "Error code",
    "message": "Human-readable error message"
}
```

## Endpoints

### User Endpoints

#### Register
```
POST /api/users/register/
```
**Request:**
```json
{
    "username": "farmer1",
    "email": "farmer@example.com",
    "password": "securepassword",
    "role": "farmer"
}
```

**Response:**
```json
{
    "status": "success",
    "data": {
        "id": 1,
        "username": "farmer1",
        "email": "farmer@example.com",
        "role": "farmer"
    }
}
```

#### Login
```
POST /api/users/login/
```
**Request:**
```json
{
    "username": "farmer1",
    "password": "securepassword"
}
```

**Response:**
```json
{
    "status": "success",
    "data": {
        "user_id": 1,
        "username": "farmer1",
        "role": "farmer"
    }
}
```

#### Get User Profile
```
GET /api/users/profile/
```
**Response:**
```json
{
    "status": "success",
    "data": {
        "id": 1,
        "username": "farmer1",
        "email": "farmer@example.com",
        "role": "farmer",
        "profile": {
            "farm_name": "Green Farm",
            "farm_location": "Punjab",
            "farm_size": 50
        }
    }
}
```

### Crop Endpoints

#### List Crops
```
GET /api/crops/
GET /api/crops/?search=tomato&crop_type=vegetable&location=Punjab
```
**Query Parameters:**
- `search`: Search by crop name or description
- `crop_type`: Filter by crop type
- `location`: Filter by location
- `min_price`: Minimum price
- `max_price`: Maximum price
- `page`: Page number (pagination)

**Response:**
```json
{
    "status": "success",
    "data": {
        "count": 150,
        "next": "/api/crops/?page=2",
        "previous": null,
        "results": [
            {
                "id": 1,
                "crop_name": "Tomato",
                "crop_type": "Vegetable",
                "quantity": 100,
                "unit": "kg",
                "price_per_unit": 50,
                "location": "Punjab",
                "farmer": "farmer1",
                "availability": true
            }
        ]
    }
}
```

#### Get Crop Details
```
GET /api/crops/{crop_id}/
```
**Response:**
```json
{
    "status": "success",
    "data": {
        "id": 1,
        "crop_name": "Tomato",
        "crop_type": "Vegetable",
        "quantity": 100,
        "unit": "kg",
        "price_per_unit": 50,
        "location": "Punjab",
        "farmer": {
            "id": 1,
            "username": "farmer1",
            "rating": 4.5
        },
        "reviews": [
            {
                "id": 1,
                "rating": 5,
                "reviewer": "buyer1",
                "text": "Great quality!"
            }
        ],
        "orders_count": 12,
        "avg_rating": 4.8
    }
}
```

#### Create Crop
```
POST /api/crops/
```
**Request:**
```json
{
    "crop_name": "Tomato",
    "crop_type": "Vegetable",
    "quantity": 100,
    "unit": "kg",
    "price_per_unit": 50,
    "description": "Fresh organic tomatoes",
    "location": "Punjab",
    "harvest_date": "2024-01-20",
    "availability_date": "2024-01-21",
    "quality_grade": "A"
}
```

#### Update Crop
```
PUT /api/crops/{crop_id}/
PATCH /api/crops/{crop_id}/
```

#### Delete Crop
```
DELETE /api/crops/{crop_id}/
```

### Disease Detection Endpoints

#### Analyze Image
```
POST /api/disease-detection/
Content-Type: multipart/form-data
```
**Request:**
```
crop_id: 1
disease_image: [file]
```

**Response:**
```json
{
    "status": "success",
    "data": {
        "disease_name": "Early Blight",
        "disease_type": "fungal",
        "confidence": 87.5,
        "treatment": "Apply copper fungicide...",
        "model": "ResNet50",
        "timestamp": "2024-01-20T10:30:00Z"
    }
}
```

#### Get Disease History
```
GET /api/crops/{crop_id}/diseases/
```
**Response:**
```json
{
    "status": "success",
    "data": {
        "count": 3,
        "diseases": [
            {
                "id": 1,
                "disease_name": "Early Blight",
                "confidence": 87.5,
                "detected_date": "2024-01-20T10:30:00Z",
                "treatment": "..."
            }
        ]
    }
}
```

### Price Prediction Endpoints

#### Get Price Predictions
```
GET /api/crops/{crop_id}/price-prediction/
GET /api/crops/{crop_id}/price-prediction/?days=30&volatility=0.05
```
**Query Parameters:**
- `days`: Number of days to forecast (default: 30)
- `volatility`: Market volatility (0.03, 0.05, 0.10)

**Response:**
```json
{
    "status": "success",
    "data": {
        "predictions": [
            {
                "date": "2024-01-21",
                "price": 52.50,
                "day": 1
            }
        ],
        "best_sell_date": {
            "date": "2024-02-10",
            "expected_price": 58.75,
            "potential_gain": 17.5
        },
        "insights": {
            "average_price": 55.00,
            "max_price": 58.75,
            "min_price": 50.00,
            "trend": "increasing",
            "volatility": 5.2,
            "recommendation": "Prices are increasing..."
        }
    }
}
```

### Weather Endpoints

#### Get Current Weather
```
GET /api/weather/?location=Punjab
```
**Response:**
```json
{
    "status": "success",
    "data": {
        "location": "Punjab",
        "temperature": 25.5,
        "feels_like": 24.0,
        "humidity": 65,
        "wind_speed": 12.5,
        "description": "Partly Cloudy",
        "alerts": [
            {
                "type": "flood",
                "severity": "high",
                "message": "Heavy rain expected",
                "recommendation": "Ensure proper drainage"
            }
        ]
    }
}
```

### Order Endpoints

#### List Orders (Farmer)
```
GET /api/farmer/orders/
GET /api/farmer/orders/?status=pending
```

#### List Orders (Buyer)
```
GET /api/buyer/orders/
GET /api/buyer/orders/?status=pending
```

#### Create Order
```
POST /api/orders/
```
**Request:**
```json
{
    "crop_id": 1,
    "quantity": 50,
    "delivery_date": "2024-01-25",
    "special_requirements": "Deliver in morning"
}
```

**Response:**
```json
{
    "status": "success",
    "data": {
        "id": 1,
        "crop_name": "Tomato",
        "quantity": 50,
        "total_price": 2500,
        "status": "pending",
        "created_date": "2024-01-20T10:30:00Z"
    }
}
```

#### Update Order Status
```
PUT /api/orders/{order_id}/
```
**Request:**
```json
{
    "status": "shipped"
}
```

### Notification Endpoints

#### List Notifications
```
GET /api/notifications/
GET /api/notifications/?unread=true
```

**Response:**
```json
{
    "status": "success",
    "data": {
        "count": 15,
        "unread": 5,
        "notifications": [
            {
                "id": 1,
                "type": "order",
                "title": "New Order",
                "message": "You have a new order for Tomato",
                "is_read": false,
                "created_at": "2024-01-20T10:30:00Z"
            }
        ]
    }
}
```

#### Mark Notification as Read
```
PATCH /api/notifications/{notification_id}/
```
**Request:**
```json
{
    "is_read": true
}
```

### Review & Rating Endpoints

#### Leave Review
```
POST /api/crops/{crop_id}/reviews/
```
**Request:**
```json
{
    "rating": 5,
    "title": "Excellent Quality",
    "review_text": "Best tomatoes I've bought"
}
```

#### Get Reviews
```
GET /api/crops/{crop_id}/reviews/
```

### Search Endpoints

#### Search Crops
```
GET /api/search/?q=tomato&location=Punjab&min_price=40&max_price=60
```

**Response:**
```json
{
    "status": "success",
    "data": {
        "query": "tomato",
        "results": [...],
        "total": 25,
        "filters_applied": {
            "location": "Punjab",
            "min_price": 40,
            "max_price": 60
        }
    }
}
```

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Permission denied |
| 404 | Not Found | Resource not found |
| 500 | Server Error | Internal error |

## Rate Limiting

- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

Headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642689000
```

## Pagination

Default page size: 20 items

**Example:**
```
GET /api/crops/?page=2&page_size=50
```

## Filtering

Apply filters to any list endpoint:

```
GET /api/crops/?crop_type=vegetable&location=Punjab&min_price=40&max_price=100
```

## Sorting

```
GET /api/crops/?ordering=-created_at  # Descending
GET /api/crops/?ordering=price_per_unit  # Ascending
```

## Bulk Operations

### Bulk Update Status
```
POST /api/orders/bulk-update/
```
**Request:**
```json
{
    "order_ids": [1, 2, 3],
    "status": "shipped"
}
```

## Webhooks (Future)

Register webhooks for real-time updates:

```
POST /api/webhooks/register/
```
**Request:**
```json
{
    "url": "https://yoursite.com/webhook",
    "events": ["order.created", "crop.listed"]
}
```

## Code Examples

### Python Example
```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/users/login/',
    json={
        'username': 'farmer1',
        'password': 'password'
    }
)
session_cookie = response.cookies

# Get crops
response = requests.get(
    'http://localhost:8000/api/crops/',
    params={'location': 'Punjab'},
    cookies=session_cookie
)
crops = response.json()
```

### JavaScript Example
```javascript
// Fetch crops with filters
const response = await fetch(
    'http://localhost:8000/api/crops/?location=Punjab&min_price=40',
    {
        method: 'GET',
        credentials: 'include'
    }
);
const data = await response.json();
```

### cURL Example
```bash
# Get crops
curl -X GET 'http://localhost:8000/api/crops/?location=Punjab'

# Create order
curl -X POST 'http://localhost:8000/api/orders/' \
  -H 'Content-Type: application/json' \
  -d '{
    "crop_id": 1,
    "quantity": 50,
    "delivery_date": "2024-01-25"
  }'
```

## Changelog

### Version 1.0.0 (Current)
- User authentication
- Crop management
- Order system
- Disease detection
- Price prediction
- Weather integration
- Notifications
- Reviews & ratings

### Planned for Version 2.0
- Payment gateway integration
- Advanced analytics
- IoT sensor integration
- Mobile app API

---

For more information, visit: https://agrigenie.readthedocs.io/api
