# BAPE Backend API Documentation

## Base URL
`http://localhost:8000` (Local)
`http://<your-vps-ip>:8000` (Production)

## Authentication
All protected endpoints require a Bearer Token.
Header: `Authorization: Bearer <your_token>`

## 1. Auth & Users
### Register
**Endpoint:** `POST /auth/register`
**Body (JSON):** `{"email": "admin@bape.com", "password": "admin"}`

### Login
**Endpoint:** `POST /auth/login`
**Body (form-data):** `username` and `password`
**Response:** `{"access_token": "...", "token_type": "bearer"}`

### Users Management (Admin)
- `GET /users/` : List all users
- `POST /users/` : Create new user
- `GET /users/{id}` : Get user details
- `PUT /users/{id}` : Update user details
- `PUT /users/{id}/status?is_active=true` : Toggle status
- `DELETE /users/{id}` : Delete user

## 2. Products
- `GET /products/` : List all products
- `POST /products/` : Create a product
- `GET /products/{id}` : Get product details
- `PUT /products/{id}` : Update a product
- `DELETE /products/{id}` : Delete a product

## 3. Services
- `GET /services/` : List all services
- `POST /services/` : Create a service
- `GET /services/{id}` : Get service details
- `PUT /services/{id}` : Update a service
- `DELETE /services/{id}` : Delete a service

## 4. Categories
- `GET /product-categories/` : List product categories
- `POST /product-categories/` : Create product category
- `DELETE /product-categories/{id}` : Delete product category
- `GET /service-categories/` : List service categories
- `POST /service-categories/` : Create service category
- `DELETE /service-categories/{id}` : Delete service category

## 5. Settings (Company Settings)
- `GET /settings/` : Get current company settings
- `POST /settings/update` : Update settings (bot rules, prompts, AI keys)
- `POST /settings/upload/branding` : Upload logo/branding images
- `POST /settings/test-email` : Send test email

## 6. Contacts
- `GET /contacts/` : List all contacts
- `POST /contacts/` : Create a contact manually
- `GET /contacts/{id}` : Get contact details
- `PUT /contacts/{id}` : Update contact info/status (e.g. pause AI)
- `DELETE /contacts/{id}` : Delete a contact

## 7. Chat (Messaging)
- `GET /chat/` : List active chats/contacts
- `GET /chat/{contact_id}/messages` : Get message history for a contact
- `POST /chat/{contact_id}/send` : Send manual message to contact
- `POST /chat/{contact_id}/pause` : Pause/Resume AI for a specific contact

## 8. WhatsApp Sessions & Webhooks
- `GET /whatsapp/sessions` : List all WhatsApp sessions
- `POST /whatsapp/sessions` : Create new session configuration
- `POST /whatsapp/sessions/{id}/init` : Start/Init session to get QR
- `DELETE /whatsapp/sessions/{id}` : Delete session
- `POST /whatsapp/sessions/{id}/reset` : Reset session (fix Bad MAC)
- `POST /whatsapp/sessions/{id}/repair` : Repair session
- `POST /whatsapp/sessions/{id}/status` : Publish text status
- `PUT /whatsapp/sessions/{id}/config` : Update session bot behavior
- `POST /webhook` : Incoming webhook from Baileys Engine (QR, Messages, Ready)

## 9. Calendar & Appointments
- `GET /calendar/auth-url` : Get Google Calendar OAuth URL
- `GET /calendar/callback` : Google Calendar OAuth callback
- `GET /calendar/settings` : Get calendar availability settings
- `POST /calendar/settings` : Update calendar availability settings
- `GET /calendar/availability` : Check available slots for a date
- `POST /calendar/book` : Book an appointment (Public/Bot)
- `GET /calendar/appointments` : List upcoming appointments
- `PUT /calendar/appointments/{id}` : Update an appointment
- `DELETE /calendar/appointments/{id}` : Cancel an appointment
- `POST /calendar/manual-book` : Book manually from dashboard

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
