# BAPE Backend API Documentation

## Base URL
`http://localhost:8000` (Local)
`http://<your-vps-ip>:8000` (Production)

## Authentication
All protected endpoints require a Bearer Token.
Header: `Authorization: Bearer <your_token>`

### 1. Login
**Endpoint:** `POST /auth/login`
**Body (form-data):**
- `username`: (string) Email of the user (e.g., `admin@bape.com`)
- `password`: (string) Password
**Response:**
```json
{
    "access_token": "eyJhbG...",
    "token_type": "bearer"
}
```

## Products
### 2. List Products
**Endpoint:** `GET /products/`
**Auth:** Required

### 3. Create Product
**Endpoint:** `POST /products/`
**Auth:** Required
**Body (JSON):**
```json
{
    "name": "Pantalón Blue Jean",
    "price": 50000.0,
    "stock": 100,
    "category_id": 1,
    "image": "http://image.url",
    "short_description": "Jeans clásicos",
    "long_description": "<p>Detalles...</p>",
    "gallery_images": ["http://img1.jpg", "http://img2.jpg"]
}
```

### 4. Delete Product
**Endpoint:** `DELETE /products/{id}`
**Auth:** Required

## Services
### 5. List Services
**Endpoint:** `GET /services/`
**Auth:** Required

### 6. Create Service
**Endpoint:** `POST /services/`
**Auth:** Required
**Body (JSON):**
```json
{
    "name": "Lavandería Express",
    "price": 15000.0,
    "category_id": 1,
    "image": "http://image.url",
    "short_description": "Lavado rápido",
    "long_description": "<p>Detalles...</p>",
    "gallery_images": []
}
```

### 7. Delete Service
**Endpoint:** `DELETE /services/{id}`
**Auth:** Required

## Categories
### 8. List Product Categories
**Endpoint:** `GET /product-categories/`
**Auth:** Required

### 9. Create Product Category
**Endpoint:** `POST /product-categories/`
**Auth:** Required
**Body (JSON):** `{"name": "Nueva Categoría"}`

### 10. List Service Categories
**Endpoint:** `GET /service-categories/`
**Auth:** Required

## Users (Admin)
### 11. List Users
**Endpoint:** `GET /users/`
**Auth:** Required

### 12. Create User
**Endpoint:** `POST /users/`
**Auth:** Required
**Body (JSON):**
```json
{
    "email": "nuevo@bape.com",
    "password": "password123"
}
```

### 13. Toggle User Status
**Endpoint:** `PUT /users/{id}/status?is_active=true`
**Auth:** Required

### 14. Delete User
**Endpoint:** `DELETE /users/{id}`
**Auth:** Required

---

# Postman Testing Guide

1.  **Create Environment:**
    *   Variable: `base_url` = `http://localhost:8000`
    *   Variable: `token` = (Leave empty initially)

2.  **Login Request:**
    *   Create a POST request to `{{base_url}}/auth/login`.
    *   Body > x-www-form-urlencoded: `username`=admin@bape.com, `password`=admin.
    *   **Tests Tab:** Add script to save token:
        ```javascript
        var jsonData = pm.response.json();
        pm.environment.set("token", jsonData.access_token);
        ```

3.  **Other Requests:**
    *   Set Authorization type to **Bearer Token**.
    *   Token value: `{{token}}`.
    *   Now you can run any request (GET Products, Create User, etc.) efficiently.
