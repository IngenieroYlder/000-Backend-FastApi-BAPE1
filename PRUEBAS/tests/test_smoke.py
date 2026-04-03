def test_health_endpoint(client, evidence_capture):
    """
    CP-SM-01 - Validar endpoint de salud del backend
    QUE: Verificar que la API esta arriba y responde correctamente.
    COMO: Realizando una peticion GET al endpoint /health.
    RESULTADO ESPERADO: Codigo 200 (EXITO) y JSON {"status": "ok"}.
    """
    response = client.get("/health")
    evidence_capture("GET /health", response=response, extra="Validacion de disponibilidad del servicio.")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_page(client, evidence_capture):
    """
    CP-SM-02 - Verificar acceso a la pagina de inicio de sesion
    QUE: Comprobar que la vista web de login carga correctamente.
    COMO: Realizando una peticion GET a /login y validando el contenido HTML.
    RESULTADO ESPERADO: Codigo 200 (EXITO) y recepcion de un documento HTML5.
    """
    response = client.get("/login")
    evidence_capture("GET /login", response=response, extra="Verificacion de carga de vista HTML de login.")
    assert response.status_code == 200
    assert "<html" in response.text.lower()


def test_root_page(client, evidence_capture):
    """
    CP-SM-03 - Verificar ruta raiz como pantalla inicial
    QUE: Validar que la ruta raiz (/) redirige o muestra la pantalla inicial.
    COMO: Accediendo a / y comprobando que devuelve una pagina HTML valida.
    RESULTADO ESPERADO: Codigo 200 (EXITO) y recepcion de la pagina principal (Login).
    """
    response = client.get("/")
    evidence_capture("GET /", response=response, extra="La ruta raiz debe devolver una vista HTML.")
    assert response.status_code == 200
    assert "<html" in response.text.lower()
