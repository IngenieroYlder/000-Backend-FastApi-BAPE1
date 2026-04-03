# Lista de Chequeo y Paso a Paso de Pruebas - Backend FastAPI BAPE

## 1. Lista de chequeo de pruebas automatizadas

| No. | Codigo | Tipo de prueba | Alcance | Resultado esperado |
|---|---|---|---|---|
| 1 | CP-SM-01 | Smoke | `GET /health` | Respuesta `200` y cuerpo `{"status":"ok"}`. |
| 2 | CP-SM-02 | Smoke | `GET /login` | Respuesta `200` y contenido HTML de login. |
| 3 | CP-SM-03 | Smoke | `GET /` | Respuesta `200` y contenido HTML de pantalla inicial. |
| 4 | CP-AU-01 | Funcional - Autenticacion | `POST /auth/register` | Usuario registrado correctamente (`200`) y `is_active = true`. |
| 5 | CP-AU-02 | Funcional - Autenticacion | `POST /auth/register` con email repetido | Rechazo de registro duplicado con `400`. |
| 6 | CP-AU-03 | Funcional - Autenticacion | `POST /auth/login` con credenciales validas | Retorna `200`, `access_token` y `token_type = bearer`. |
| 7 | CP-AU-04 | Funcional - Autenticacion | `POST /auth/login` con clave invalida | Rechazo con `401`. |
| 8 | CP-RB-01 | Seguridad - Acceso | `GET /users/` sin token | Rechazo por autenticacion con `401`. |
| 9 | CP-RB-02 | Seguridad - Roles | `GET /users/` con superadmin | Respuesta `200` y lista de usuarios no vacia. |

## 2. Herramientas usadas

| Herramienta | Uso |
|---|---|
| `pytest` | Ejecucion automatizada de pruebas. |
| `reportlab` | Generacion de PDF de resultados. |
| `pillow` | Generacion de evidencias visuales (pantallazos PNG). |

Archivo de dependencias de pruebas:
- `PRUEBAS/requirements-test.txt`

## 3. Paso a paso de instalacion y preparacion

1. Abrir terminal en la raiz del proyecto:
```powershell
cd "D:\Colombia Picture\n8n agente ia burbuja\000 Backend FastApi BAPE"
```

2. Crear entorno virtual (solo la primera vez):
```powershell
python -m venv venv
```

3. Instalar dependencias base del proyecto:
```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Instalar dependencias de pruebas:
```powershell
venv\Scripts\python.exe -m pip install -r PRUEBAS\requirements-test.txt
```

## 4. Ejecucion completa automatizada (recomendada)

1. Ejecutar todo el paquete de pruebas y generar evidencias + PDF:
```powershell
venv\Scripts\python.exe PRUEBAS\run_tests_with_report.py
```

2. Resultado esperado en consola:
- `9 passed`
- Ruta de `Reporte consolidado`
- Ruta de `Reportes por prueba`

3. Estructura de salida esperada:
- `PRUEBAS/evidencias/<id_ejecucion>/results.json`
- `PRUEBAS/evidencias/<id_ejecucion>/pantallazos/`
- `PRUEBAS/evidencias/<id_ejecucion>/reportes/reporte_pruebas_<id_ejecucion>.pdf`
- `PRUEBAS/evidencias/<id_ejecucion>/reportes/por_prueba/`

## 5. Paso a paso por cada prueba (ejecucion individual)

### Prueba 1: CP-SM-01
- Comando:
```powershell
venv\Scripts\python.exe -m pytest PRUEBAS/tests/test_smoke.py::test_health_endpoint -q
```
- Resultado esperado: `1 passed`.

### Prueba 2: CP-SM-02
- Comando:
```powershell
venv\Scripts\python.exe -m pytest PRUEBAS/tests/test_smoke.py::test_login_page -q
```
- Resultado esperado: `1 passed`.

### Prueba 3: CP-SM-03
- Comando:
```powershell
venv\Scripts\python.exe -m pytest PRUEBAS/tests/test_smoke.py::test_root_page -q
```
- Resultado esperado: `1 passed`.

### Prueba 4: CP-AU-01
- Comando:
```powershell
venv\Scripts\python.exe -m pytest PRUEBAS/tests/test_auth.py::test_register_success -q
```
- Resultado esperado: `1 passed`.

### Prueba 5: CP-AU-02
- Comando:
```powershell
venv\Scripts\python.exe -m pytest PRUEBAS/tests/test_auth.py::test_register_duplicate_email -q
```
- Resultado esperado: `1 passed`.

### Prueba 6: CP-AU-03
- Comando:
```powershell
venv\Scripts\python.exe -m pytest PRUEBAS/tests/test_auth.py::test_login_success_returns_token -q
```
- Resultado esperado: `1 passed`.

### Prueba 7: CP-AU-04
- Comando:
```powershell
venv\Scripts\python.exe -m pytest PRUEBAS/tests/test_auth.py::test_login_invalid_password -q
```
- Resultado esperado: `1 passed`.

### Prueba 8: CP-RB-01
- Comando:
```powershell
venv\Scripts\python.exe -m pytest PRUEBAS/tests/test_security.py::test_users_requires_token -q
```
- Resultado esperado: `1 passed`.

### Prueba 9: CP-RB-02
- Comando:
```powershell
venv\Scripts\python.exe -m pytest PRUEBAS/tests/test_security.py::test_users_superadmin_can_list -q
```
- Resultado esperado: `1 passed`.

## 6. Verificacion de resultados y trazabilidad

1. Abrir `results.json` de la ultima ejecucion en `PRUEBAS/evidencias/<id_ejecucion>/`.
2. Validar en `resumen`:
- `total = 9`
- `aprobadas = 9`
- `fallidas = 0`
- `omitidas = 0`
3. Revisar PDF consolidado y PDFs individuales para anexar al entregable.

## 7. Formato sugerido para evidencia academica

1. Portada.
2. Introduccion.
3. Lista de chequeo (seccion 1 de este documento).
4. Paso a paso de instalacion y ejecucion (secciones 3, 4 y 5).
5. Capturas/PDF de resultados.
6. Conclusiones.
