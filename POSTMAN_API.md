# Guía de Pruebas con Postman - BAPE API

Esta guía te ayudará a configurar y probar todos los endpoints de tu Backend usando [Postman](https://www.postman.com/downloads/), la herramienta estándar para probar APIs.

## 1. Configuración Inicial

### Crear un Entorno (Environment)
Para no repetir la URL base todo el tiempo, configura esto:
1.  Abre Postman.
2.  Ve a **Environments** -> **Create Environment**.
3.  Nombre: `BAPE Production` (o `Local` si es local).
4.  Agrega la variable:
    *   **Variable**: `base_url`
    *   **Initial Value**: `https://tudominio.com` (o `http://localhost:8000` si es local).
    *   **Variable**: `token`
    *   **Initial Value**: (Déjalo vacío por ahora).

---

## 2. Autenticación (Login)

Antes de nada, necesitas obtener tu "laven de acceso" (Token JWT). Sin esto, la API te prohibirá el paso (Error 401).

**Request: Login**
*   **Método**: `POST`
*   **URL**: `{{base_url}}/token`
*   **Body** (Selecciona `x-www-form-urlencoded`):
    *   `username`: `admin@bape.com`
    *   `password`: `admin`
*   **Tests** (Pestaña "Tests" en Postman):
    Agrega este código para guardar el token automáticamente:
    ```javascript
    var jsonData = pm.response.json();
    pm.environment.set("token", jsonData.access_token);
    ```

> Dale a **Send**. Si sale status **200 OK**, ¡ya estás dentro! El token se guardó solo.

---

## 3. Configurar Autorización Automática
Para no pegar el token en cada petición:
1.  Ve a la carpeta de tu colección (o a cada petición individual).
2.  Pestaña **Authorization**.
3.  Type: **Bearer Token**.
4.  Token: `{{token}}`.

---

## 4. Pruebas de Usuarios

### A. Listar Usuarios
*   **Método**: `GET`
*   **URL**: `{{base_url}}/users/`
*   **Resultado esperado**: Una lista JSON con todos los usuarios.

### B. Crear Usuario
*   **Método**: `POST`
*   **URL**: `{{base_url}}/users/`
*   **Body** (`raw` -> `JSON`):
    ```json
    {
      "email": "nuevo@test.com",
      "password": "clave_segura",
      "first_name": "Juan",
      "last_name": "Pérez",
      "phone": "3001234567"
    }
    ```

### C. Editar Usuario (Tu nueva función)
*   **Método**: `PUT`
*   **URL**: `{{base_url}}/users/{ID_DEL_USUARIO}`
*   **Body** (`raw` -> `JSON`):
    ```json
    {
      "first_name": "Juan Actualizado",
      "phone": "3119999999"
    }
    ```
*   **Nota**: No necesitas enviar todos los campos, solo los que cambias.

---

## 5. Pruebas de Productos

### A. Crear Producto Completo
*   **Método**: `POST`
*   **URL**: `{{base_url}}/products/`
*   **Body** (`raw` -> `JSON`):
    ```json
    {
      "name": "Camiseta Premium",
      "price": 50.00,
      "stock": 100,
      "category_id": 1,
      "image": "https://via.placeholder.com/150",
      "short_description": "La mejor calidad",
      "long_description": "<h1>Detalles</h1><p>Algodón 100%...</p>",
      "gallery_images": [
          "https://foto1.com/a.jpg", 
          "https://foto2.com/b.jpg"
      ]
    }
    ```

### B. Listar Productos
*   **Método**: `GET`
*   **URL**: `{{base_url}}/products/`

### C. Borrar Producto
*   **Método**: `DELETE`
*   **URL**: `{{base_url}}/products/{ID}`

---

## 6. Pruebas de Categorías

### A. Crear Categoría Producto
*   **Método**: `POST`
*   **URL**: `{{base_url}}/product-categories`
*   **Body**:
    ```json
    {
      "name": "Ropa de Verano"
    }
    ```

---

## Resumen de Errores Comunes

| Código | Significado | Solución |
| :--- | :--- | :--- |
| **401 Unauthorized** | No enviaste el token o expiró. | Ejecuta el Login de nuevo. |
| **403 Forbidden** | No tienes permisos | Revisa si tu usuario está activo. |
| **422 Validation Error** | Enviaste mal el JSON (tipo de dato incorrecto). | Revisa el Body de tu petición. |
| **500 Internal Server Error** | El servidor explotó. | Revisa los logs en Easypanel (Console). |
