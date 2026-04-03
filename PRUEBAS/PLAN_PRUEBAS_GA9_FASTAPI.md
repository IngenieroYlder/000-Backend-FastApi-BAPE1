# Plan de Pruebas - GA9-220501096-AA1-EV01

## 1. Portada (plantilla para el PDF)
- Programa: Analisis y desarrollo de software
- Proyecto formativo: Construccion de software integrador de tecnologias orientadas a servicios
- Fase: Ejecucion
- Resultado de aprendizaje: 220501096-05
- Actividad: GA9-220501096-AA1 - Realizar plan de pruebas
- Evidencia: Taller sobre codificacion de modulos del software (EV01)
- Proyecto evaluado: Backend FastAPI BAPE
- Integrantes, ficha, instructor, fecha

## 2. Introduccion
Este documento define un plan de pruebas para el proyecto Backend FastAPI BAPE, enfocado en validar funcionalidad, estabilidad y trazabilidad.  
La estrategia esta pensada para ejecucion local, automatizada y facil de repetir, usando herramientas compatibles con FastAPI y Python.

## 3. Objetivo del plan
- Verificar que los modulos principales funcionen segun los casos de uso.
- Definir un ambiente de pruebas alineado al entorno de produccion, pero ejecutado en local.
- Documentar resultados para mantener trazabilidad.
- Dejar una base automatizable para pruebas futuras (regresion).

## 4. Tipos de pruebas de software (resumen)
1. Pruebas unitarias
   Validan funciones o metodos de forma aislada.  
   Beneficio: detectan errores rapido y con bajo costo.
2. Pruebas de integracion
   Validan la interaccion entre modulos (API + BD + servicios).  
   Beneficio: encuentran fallos de acople.
3. Pruebas funcionales (API/UI)
   Validan comportamientos frente a requisitos y casos de uso.  
   Beneficio: prueban el sistema como lo usa el usuario.
4. Pruebas de regresion
   Reejecutan casos ya validados despues de cambios.  
   Beneficio: evitan romper funcionalidades estables.
5. Pruebas de humo (smoke)
   Verifican endpoints y flujos criticos minimos.  
   Beneficio: alertan rapido si un despliegue quedo inestable.

## 5. Tipos de pruebas recomendados para este proyecto FastAPI
Para este backend, los mas compatibles y funcionales son:
1. Unitarias en servicios y utilidades internas.
2. Integracion de endpoints con FastAPI TestClient.
3. Funcionales de autenticacion y CRUD basico.
4. Humo sobre rutas criticas (`/health`, `/login`, `/auth/login`).
5. Regresion automatizada al cerrar cada cambio.

Motivo: el proyecto tiene varios routers y dependencias de base de datos, por lo que la combinacion unitarias + integracion + humo aporta buena cobertura sin complejidad excesiva.

## 6. Herramienta de pruebas elegida
- Framework principal: `pytest`
- Cliente HTTP para pruebas de API: `httpx` o `fastapi.testclient`
- Cobertura (opcional): `pytest-cov`
- Pruebas async (si aplica): `pytest-asyncio`

Instalacion sugerida en local:
```bash
pip install pytest pytest-cov pytest-asyncio
```

## 7. Ambiente de pruebas local (no nube)
1. Crear/usar entorno virtual local.
2. Usar una base de datos de pruebas (SQLite o Postgres local dedicado para test).
3. Definir variables de entorno de prueba (`.env.test`).
4. Ejecutar pruebas en maquina local antes de cada push.

Recomendacion inicial: comenzar con SQLite para pruebas rapidas de API y luego pasar a Postgres local para validar compatibilidad total.

## 8. Casos de prueba propuestos (pendiente de acuerdo)
Estos casos se proponen para aprobar contigo antes de ejecutar.

### 8.1 Smoke (prioridad alta)
1. CP-SM-01: `GET /health` responde `200` y `{"status":"ok"}`.
2. CP-SM-02: `GET /login` responde `200` y contenido HTML.
3. CP-SM-03: `GET /` responde `200` (pantalla inicial).

### 8.2 Autenticacion y acceso
1. CP-AU-01: `POST /auth/register` crea usuario valido.
2. CP-AU-02: `POST /auth/register` falla con correo duplicado.
3. CP-AU-03: `POST /auth/login` retorna token con credenciales correctas.
4. CP-AU-04: `POST /auth/login` rechaza credenciales invalidas.

### 8.3 CRUD principal (funcional)
1. CP-PR-01: Crear y listar productos (`/products`).
2. CP-SV-01: Crear y listar servicios (`/services`).
3. CP-CT-01: Crear y consultar contactos (`/api/contacts`).

### 8.4 Seguridad / autorizacion
1. CP-RB-01: Endpoint protegido sin token retorna `401`.
2. CP-RB-02: Usuario sin rol admin no puede listar usuarios (`/users` -> `403`).

## 9. Trazabilidad contra criterios de evaluacion
1. Diseno de casos de prueba
   Se cubre con la seccion 8 (casos identificados por codigo).
2. Definicion del ambiente de pruebas
   Se cubre con la seccion 7 (entorno local de prueba).
3. Ejecucion segun plan
   Se realizara por lotes: smoke -> autenticacion -> CRUD -> seguridad.
4. Documentacion de resultados
   Cada ejecucion registrara: fecha, caso, resultado, evidencia y observaciones.

## 10. Estructura sugerida para automatizacion
```text
PRUEBAS/
  PLAN_PRUEBAS_GA9_FASTAPI.md
  requirements-test.txt
  run_tests_with_report.py
  generar_reporte_pdf.py
  tests/
    conftest.py
    test_smoke.py
    test_auth.py
    test_security.py
  evidencias/
```

Comandos objetivos (cuando acordemos iniciar):
```bash
venv\Scripts\python.exe -m pip install -r PRUEBAS\requirements-test.txt
venv\Scripts\python.exe -m pytest PRUEBAS/tests -q
venv\Scripts\python.exe -m pytest PRUEBAS/tests/test_smoke.py -q
venv\Scripts\python.exe PRUEBAS\run_tests_with_report.py
```

## 11. Evidencias para el entregable SENA
Para el PDF final (minimo 3 hojas), incluir:
1. Portada
2. Introduccion
3. Tipos de pruebas y justificacion para FastAPI
4. Herramienta instalada y paso a paso
5. Capturas de ejecucion (terminal y resultados)
6. Resumen de pruebas realizadas
7. Conclusiones

## 12. Estado actual
- Plan creado: SI
- Casos definidos: PROPUESTOS
- Ejecucion automatizada: PENDIENTE de aprobacion


## 13. Requisito adicional aprobado
Se agrega un requisito obligatorio para la automatizacion:
1. Cada prueba automatizada debe generar evidencia visual (pantallazo en formato PNG).
2. Se debe generar un reporte PDF consolidado por ejecucion.
3. Se debe generar tambien un PDF individual por cada prueba automatizada.

Evidencias generadas por ejecucion:
- Carpeta de pantallazos: `PRUEBAS/evidencias/<run_id>/pantallazos/`
- PDF consolidado: `PRUEBAS/evidencias/<run_id>/reportes/reporte_pruebas_<run_id>.pdf`
- PDFs por prueba: `PRUEBAS/evidencias/<run_id>/reportes/por_prueba/`

Comando oficial de ejecucion automatizada con reporte:
```bash
venv\Scripts\python.exe PRUEBAS\run_tests_with_report.py
```

