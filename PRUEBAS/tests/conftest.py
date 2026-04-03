from __future__ import annotations

import json
import os
import re
import textwrap
import uuid
import inspect
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont
from sqlmodel import SQLModel, Session, create_engine

from app import models
from app.database import get_db, get_session
from app.main import app


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)[:120]


def _nombre_prueba_desde_item(item: pytest.Item) -> str:
    doc = getattr(getattr(item, "function", None), "__doc__", None)
    if isinstance(doc, str) and doc.strip():
        # Retornar solo la primera linea para el nombre corto si es necesario, 
        # pero aqui lo usaremos para todo el docstring en el reporte PDF.
        return doc.strip().splitlines()[0]
    return item.name


def _entrada_prueba_default(id_prueba: str, nombre_prueba: str = "") -> Dict[str, Any]:
    return {
        "id_prueba": id_prueba,
        "nombre_prueba": nombre_prueba or id_prueba,
        "resultado": "no_ejecutada",
        "duracion_segundos": 0.0,
        "pantallazos": [],
        "error": "",
    }


def _render_text_screenshot(image_path: Path, title: str, lines: list[str]) -> None:
    width = 1400
    margin = 36
    line_height = 20
    wrapped_lines: list[str] = []
    for line in lines:
        wrapped = textwrap.wrap(line, width=120) or [""]
        wrapped_lines.extend(wrapped)

    height = max(800, margin * 2 + (len(wrapped_lines) + 6) * line_height)
    img = Image.new("RGB", (width, height), color=(20, 20, 20))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    draw.text((margin, margin), title, fill=(255, 255, 255), font=font)
    y = margin + 2 * line_height
    for line in wrapped_lines:
        draw.text((margin, y), line, fill=(230, 230, 230), font=font)
        y += line_height

    image_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(image_path)


def _response_lines(response: Any) -> list[str]:
    lines = [
        f"ESTADO_HTTP: {response.status_code}",
        "ENCABEZADOS:",
    ]
    for key, value in sorted(response.headers.items()):
        lines.append(f"  {key}: {value}")
    body = response.text if hasattr(response, "text") else str(response)
    lines.append("CUERPO:")
    lines.extend([f"  {line}" for line in body.splitlines()])
    return lines


def pytest_configure(config: pytest.Config) -> None:
    run_dir_env = os.getenv("BAPE_TEST_RUN_DIR")
    if run_dir_env:
        run_dir = Path(run_dir_env)
    else:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_dir = Path("PRUEBAS") / "evidencias" / run_id

    screenshots_dir = run_dir / "pantallazos"
    reportes_dir = run_dir / "reportes"
    run_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    reportes_dir.mkdir(parents=True, exist_ok=True)

    config._bape_reporte = {
        "id_ejecucion": run_dir.name,
        "generado_en_utc": datetime.now(timezone.utc).isoformat(),
        "directorios": {
            "directorio_ejecucion": str(run_dir),
            "pantallazos": str(screenshots_dir),
            "reportes": str(reportes_dir),
        },
        "resumen": {"total": 0, "aprobadas": 0, "fallidas": 0, "omitidas": 0},
        "pruebas": {},
    }
    config._bape_capture_count = {}
    config._bape_test_counter = 0
    config._bape_tests_seen = set()


@pytest.fixture
def evidence_capture(request: pytest.FixtureRequest, pytestconfig: pytest.Config):
    id_prueba = request.node.nodeid
    nombre_prueba = _nombre_prueba_desde_item(request.node)
    
    if id_prueba not in pytestconfig._bape_tests_seen:
        pytestconfig._bape_test_counter += 1
        pytestconfig._bape_tests_seen.add(id_prueba)
    
    num_prueba = pytestconfig._bape_test_counter
    
    pruebas_map = pytestconfig._bape_reporte["pruebas"]
    if id_prueba not in pruebas_map:
        pruebas_map[id_prueba] = _entrada_prueba_default(id_prueba, nombre_prueba)

    def _capture(paso: str, response: Any | None = None, extra: str | None = None) -> Path:
        counts = pytestconfig._bape_capture_count
        counts[id_prueba] = counts.get(id_prueba, 0) + 1
        shot_index = counts[id_prueba]

        # Extraer docstring y codigo para el modo interactivo
        doc = request.node.obj.__doc__ or "Sin descripcion"
        doc = textwrap.dedent(doc).strip()
        
        try:
            source = inspect.getsource(request.node.obj)
            source = textwrap.dedent(source).strip()
        except Exception:
            source = "# No se pudo obtener el codigo fuente"

        if os.getenv("BAPE_INTERACTIVE") == "True":
            if shot_index == 1:
                print("\n" + "╔" + "═"*78 + "╗")
                print(f"║ PRUEBA #{num_prueba}: {nombre_prueba}".ljust(79) + "║")
                print("╠" + "═"*78 + "╣")
                for line in doc.splitlines():
                    print(f"║ {line}".ljust(79) + "║")
                print("╠" + "═"*78 + "╣")
                print("║ CODIGO A EJECUTAR:".ljust(79) + "║")
                print("╟" + "─"*78 + "╢")
                for line in source.splitlines():
                    clean_line = line.replace("\t", "    ")
                    if len(clean_line) > 74: clean_line = clean_line[:71] + "..."
                    print(f"║   {clean_line}".ljust(79) + "║")
                print("╚" + "═"*78 + "╝")
                input("\n>>> Presiona [ENTER] para iniciar...")

            print(f"\n" + "-"*60)
            print(f" EJECUTANDO PASO: {paso}")
            if response is not None:
                print(f" RESPUESTA HTTP: {response.status_code}")
            print("-"*60)
            input(">>> Presiona [ENTER] para continuar...")

        shot_name = f"{_safe_name(id_prueba)}_{shot_index:02d}_{_safe_name(paso)}.png"
        shot_path = Path(pytestconfig._bape_reporte["directorios"]["pantallazos"]) / shot_name

        lines: list[str] = [f"PRUEBA: {nombre_prueba}", f"ID: {id_prueba}", f"PASO: {paso}", ""]
        if response is not None:
            lines.extend(_response_lines(response))
        if extra:
            lines.extend(["", "NOTAS:"])
            lines.extend([f"  {line}" for line in extra.splitlines()])

        _render_text_screenshot(shot_path, f"Evidencia de Prueba - {paso}", lines)
        
        captura_info = {
            "path": str(shot_path),
            "paso": paso,
            "lineas": lines
        }
        pruebas_map[id_prueba].setdefault("capturas", []).append(captura_info)
        pruebas_map[id_prueba]["pantallazos"].append(str(shot_path))
        return shot_path
        # ... rest of capture logic

    return _capture


@pytest.fixture
def unique_seed() -> str:
    return uuid.uuid4().hex[:8]


@pytest.fixture
def client():
    run_dir = Path(os.getenv("BAPE_TEST_RUN_DIR", "PRUEBAS/evidencias/manual"))
    db_dir = run_dir / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_file = db_dir / f"test_{uuid.uuid4().hex}.db"

    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(models.Plan(name="Free", price=0.0, limits={}))
        session.commit()

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_session] = override_get_db

    startup_handlers = list(app.router.on_startup)
    shutdown_handlers = list(app.router.on_shutdown)
    app.router.on_startup.clear()
    app.router.on_shutdown.clear()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    app.router.on_startup[:] = startup_handlers
    app.router.on_shutdown[:] = shutdown_handlers


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return

    id_prueba = item.nodeid
    nombre_prueba = _nombre_prueba_desde_item(item)
    pruebas_map = item.config._bape_reporte["pruebas"]
    entrada = pruebas_map.setdefault(id_prueba, _entrada_prueba_default(id_prueba, nombre_prueba))

    mapa_resultado = {"passed": "aprobada", "failed": "fallida", "skipped": "omitida"}
    entrada["resultado"] = mapa_resultado.get(report.outcome, report.outcome)
    entrada["duracion_segundos"] = round(float(report.duration), 4)
    if report.failed and call.excinfo is not None:
        entrada["error"] = str(call.excinfo.value)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    data = session.config._bape_reporte
    pruebas = list(data["pruebas"].values())
    total = len(pruebas)
    aprobadas = sum(1 for item in pruebas if item["resultado"] == "aprobada")
    fallidas = sum(1 for item in pruebas if item["resultado"] == "fallida")
    omitidas = sum(1 for item in pruebas if item["resultado"] == "omitida")
    data["resumen"] = {"total": total, "aprobadas": aprobadas, "fallidas": fallidas, "omitidas": omitidas}
    data["codigo_salida_pytest"] = exitstatus

    results_path = Path(data["directorios"]["directorio_ejecucion"]) / "results.json"
    results_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
