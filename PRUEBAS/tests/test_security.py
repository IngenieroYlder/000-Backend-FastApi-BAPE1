def _register_payload(seed: str) -> dict:
    return {
        "email": f"sec_{seed}@example.com",
        "password": "Pass1234!",
        "first_name": "Sec",
        "last_name": "Tester",
        "phone": "3110000000",
        "company_name": f"Compania SEC {seed}",
    }


def _register_and_login(client, seed: str) -> str:
    payload = _register_payload(seed)
    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def test_users_requires_token(client, evidence_capture):
    """
    CP-RB-01 - Proteger /users cuando no hay token
    QUE: Verificar que el acceso a la lista de usuarios esta protegido.
    COMO: Realizando una peticion GET a /users sin enviar cabeceras de autorizacion.
    RESULTADO ESPERADO: Codigo 401 (UNAUTHORIZED) y rechazo de la peticion.
    """
    response = client.get("/users/")
    evidence_capture("GET /users sin token", response=response)

    assert response.status_code == 401


def test_users_superadmin_can_list(client, evidence_capture, unique_seed):
    """
    CP-RB-02 - Permitir listado de usuarios con rol superadmin
    QUE: Asegurar que un usuario con privilegios de superadmin puede ver a otros usuarios.
    COMO: Generando un token JWT para un superadmin y usandolo para consultar /users.
    RESULTADO ESPERADO: Codigo 200 (EXITO) y una lista JSON de usuarios registrados.
    """
    token = _register_and_login(client, unique_seed)
    response = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    evidence_capture("GET /users con superadmin", response=response)

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1
