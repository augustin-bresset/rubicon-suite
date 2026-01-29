# PDP API Documentation

REST API for Product Definition and Pricing system.

## Base URL

```
http://localhost:8069/api/v1
```

## Authentication

All API endpoints (except `/auth/login`) require JWT authentication.

Include the token in the `Authorization` header:
```
Authorization: Bearer <token>
```

---

## Authentication Endpoints

### POST /auth/login

Authenticate a user and receive a JWT token.

**Request Body:**
```json
{
  "login": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "token": "eyJ...",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "login": "admin",
    "name": "Administrator"
  }
}
```

**Response (401):**
```json
{
  "error": "Invalid credentials"
}
```

---

### POST /auth/refresh

Refresh the current JWT token.

**Headers:**
```
Authorization: Bearer <current_token>
```

**Response (200):**
```json
{
  "token": "eyJ...",
  "expires_in": 86400
}
```

---

### GET /auth/me

Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": 1,
  "login": "admin",
  "name": "Administrator",
  "email": "admin@example.com"
}
```

---

## Product Endpoints

### GET /pdp/products

List all products with optional filtering.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| model_id | integer | Filter by model ID |
| limit | integer | Max results (default: 100) |
| offset | integer | Pagination offset (default: 0) |

**Response (200):**
```json
{
  "products": [
    {
      "id": 1,
      "code": "RING-001",
      "name": "Gold Ring",
      "model_id": 5,
      "model_code": "MDL-005"
    }
  ],
  "total": 42
}
```

---

### GET /pdp/products/{id}

Get full product details including weights and pricing.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Product ID |

**Response (200):**
```json
{
  "product": {
    "id": 1,
    "code": "RING-001",
    "name": "Gold Ring",
    "model_id": 5,
    "model_code": "MDL-005",
    "create_date": "2024-01-15 10:30:00"
  },
  "weights": {
    "stone_original": [
      {
        "type": "Diamond",
        "shade": "White",
        "shape": "Round",
        "pieces": 12,
        "weight": "0.50"
      }
    ],
    "stone_recut": [...],
    "metal": [
      {
        "metal": "Gold",
        "purity": "18K",
        "weight": 5.25
      }
    ]
  },
  "costing": {
    "currency": {
      "id": 1,
      "symbol": "$",
      "rate": 1.0
    },
    "lines": [
      {
        "type": "stone",
        "label": "Stones",
        "cost": 1500.00,
        "margin": 450.00,
        "price": 1950.00
      },
      {
        "type": "metal",
        "label": "Metals",
        "cost": 800.00,
        "margin": 240.00,
        "price": 1040.00
      }
    ],
    "totals": {
      "cost": 2300.00,
      "margin": 690.00,
      "price": 2990.00
    }
  },
  "metadata": {
    "all_currencies": [...],
    "all_margins": [...]
  }
}
```

---

### POST /pdp/products/{id}/price

Compute price with specific margin and currency.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Product ID |

**Request Body:**
```json
{
  "margin_id": 1,
  "currency_id": 2
}
```

**Response (200):**
```json
{
  "lines": [
    {
      "type": "stone",
      "cost": 1500.00,
      "margin": 450.00,
      "price": 1950.00
    }
  ],
  "totals": {
    "cost": 2300.00,
    "margin": 690.00,
    "price": 2990.00
  },
  "currency": {
    "id": 2,
    "symbol": "EUR",
    "position": "after",
    "rate": 0.92
  }
}
```

---

## Metadata Endpoints

### GET /pdp/metadata

Get all reference data for dropdowns and filters.

**Response (200):**
```json
{
  "currencies": [
    {"id": 1, "name": "USD", "symbol": "$", "rate": 1.0}
  ],
  "margins": [
    {"id": 1, "name": "Standard"}
  ],
  "models": [
    {"id": 1, "code": "MDL-001", "name": "Ring Model A"}
  ],
  "metals": [
    {"id": 1, "name": "Gold"}
  ]
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "error": "Error message description"
}
```

**Common HTTP Status Codes:**
| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized (missing or invalid token) |
| 403 | Forbidden (permission denied) |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Permission System

API endpoints check user permissions via the `pdp_permission` module.

**Required Permissions:**
| Endpoint | Permission |
|----------|------------|
| GET /pdp/products | product.read |
| GET /pdp/products/{id} | product.read |
| POST /pdp/products/{id}/price | price.compute |

If the user lacks the required permission, the API returns:
```json
{
  "error": "Permission denied: product.read"
}
```

---

## Usage Examples

### cURL

**Login:**
```bash
curl -X POST http://localhost:8069/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "admin", "password": "admin"}'
```

**Get Products:**
```bash
curl http://localhost:8069/api/v1/pdp/products \
  -H "Authorization: Bearer <token>"
```

**Get Product Details:**
```bash
curl http://localhost:8069/api/v1/pdp/products/1 \
  -H "Authorization: Bearer <token>"
```

**Compute Price:**
```bash
curl -X POST http://localhost:8069/api/v1/pdp/products/1/price \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"margin_id": 1, "currency_id": 2}'
```

### Python

```python
import requests

API_URL = "http://localhost:8069/api/v1"

# Login
response = requests.post(f"{API_URL}/auth/login", json={
    "login": "admin",
    "password": "admin"
})
token = response.json()["token"]

# Get products
headers = {"Authorization": f"Bearer {token}"}
products = requests.get(f"{API_URL}/pdp/products", headers=headers)
print(products.json())
```
