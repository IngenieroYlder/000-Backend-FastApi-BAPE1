from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from generar_reporte_pdf import generate_reports


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = project_root / "PRUEBAS" / "evidencias" / run_id
    run_tmp_dir = run_dir / "tmp"
    run_dir.mkdir(parents=True, exist_ok=True)
    run_tmp_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["BAPE_TEST_RUN_DIR"] = str(run_dir)
    env["TMP"] = str(run_tmp_dir)
    env["TEMP"] = str(run_tmp_dir)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "PRUEBAS/tests",
        "-q",
        "-p",
        "no:cacheprovider",
        "-p",
        "no:tmpdir",
    ]
    print("Ejecutando:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=project_root, env=env)

    results_json = run_dir / "results.json"
    if not results_json.exists():
        print("No se genero results.json. Revisa errores de coleccion/ejecucion de pytest.")
        return result.returncode

    outputs = generate_reports(results_json)
    print("\nReporte consolidado:")
    print(outputs["pdf_consolidado"])
    print("\nReportes por prueba:")
    print(outputs["carpeta_por_prueba"])

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
