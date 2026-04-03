from __future__ import annotations


def _register_payload(seed: str) -> dict:
    return {
        "email": f"qa_{seed}@example.com",
        "password": "Pass1234!",
        "first_name": "QA",
        "last_name": "Tester",
        "phone": "3000000000",
        "company_name": f"Compania QA {seed}",
    }


def test_register_success(client, evidence_capture, unique_seed):
    """
    CP-AU-01 - Registrar un usuario valido
    QUE: Validar que un nuevo usuario puede registrarse correctamente con datos validos.
    COMO: Enviando un POST a /auth/register con email, password y datos de empresa nuevos.
    RESULTADO ESPERADO: Codigo 200 (EXITO) y el objeto del usuario con su ID autogenerado.
    """
    payload = _register_payload(unique_seed)
    response = client.post("/auth/register", json=payload)
    evidence_capture("POST /auth/register exito", response=response)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["is_active"] is True


def test_register_duplicate_email(client, evidence_capture, unique_seed):
    """
    CP-AU-02 - Rechazar registro con correo duplicado
    QUE: Verificar que el sistema no permite registrar dos usuarios con el mismo email.
    COMO: Intentando registrar un usuario con un correo que ya fue registrado en el paso anterior.
    RESULTADO ESPERADO: Codigo 400 (BAD REQUEST) y mensaje de error indicando que el correo ya existe.
    """
    payload = _register_payload(unique_seed)
    first = client.post("/auth/register", json=payload)
    second = client.post("/auth/register", json=payload)

    evidence_capture("POST /auth/register duplicado", response=second)
    assert first.status_code == 200
    assert second.status_code == 400


def test_login_success_returns_token(client, evidence_capture, unique_seed):
    """
    CP-AU-03 - Iniciar sesion con credenciales validas
    QUE: Comprobar que un usuario registrado puede obtener un token de acceso (JWT).
    COMO: Enviando las credenciales correctas al endpoint /auth/login.
    RESULTADO ESPERADO: Codigo 200 (EXITO) y un JSON con el 'access_token' y 'token_type'.
    """
    payload = _register_payload(unique_seed)
    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    )
    evidence_capture("POST /auth/login exito", response=login_response)

    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_login_invalid_password(client, evidence_capture, unique_seed):
    """
    CP-AU-04 - Rechazar inicio de sesion con clave invalida
    QUE: Validar que el sistema deniega el acceso si la contraseña es incorrecta.
    COMO: Intentando hacer login con un email existente pero con una contraseña erronea.
    RESULTADO ESPERADO: Codigo 401 (UNAUTHORIZED) y mensaje de error de credenciales incorrectas.
    """
    payload = _register_payload(unique_seed)
    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        data={"username": payload["email"], "password": "wrong-password"},
    )
    evidence_capture("POST /auth/login clave invalida", response=login_response)

    assert login_response.status_code == 401
