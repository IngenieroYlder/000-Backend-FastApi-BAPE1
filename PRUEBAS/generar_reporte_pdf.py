from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from xml.sax.saxutils import escape
import textwrap

import numpy as np
import cv2
from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)[:120]


def _build_image_flowable(path: Path, max_width: float = 500, max_height: float = 280):
    if not path.exists():
        return Paragraph(f"Pantallazo no encontrado: <b>{escape(str(path))}</b>", getSampleStyleSheet()["Normal"])

    with PILImage.open(path) as img:
        width, height = img.size

    scale = min(max_width / float(width), max_height / float(height), 1.0)
    return Image(str(path), width=width * scale, height=height * scale)


def _normalizar_data(data: Dict) -> Dict:
    # Compatibilidad con corridas antiguas en ingles
    if "pruebas" not in data and "tests" in data:
        pruebas = {}
        for key, test in data.get("tests", {}).items():
            resultado_en = test.get("outcome", "unknown")
            mapa = {"passed": "aprobada", "failed": "fallida", "skipped": "omitida"}
            pruebas[key] = {
                "id_prueba": test.get("nodeid", key),
                "nombre_prueba": test.get("nodeid", key),
                "resultado": mapa.get(resultado_en, resultado_en),
                "duracion_segundos": test.get("duration_seconds", 0),
                "pantallazos": test.get("screenshots", []),
                "capturas": test.get("capturas", []),
                "error": test.get("error", ""),
            }
        data["pruebas"] = pruebas

    if "resumen" not in data and "summary" in data:
        summary = data.get("summary", {})
        data["resumen"] = {
            "total": summary.get("total", 0),
            "aprobadas": summary.get("passed", 0),
            "fallidas": summary.get("failed", 0),
            "omitidas": summary.get("skipped", 0),
        }

    if "id_ejecucion" not in data:
        data["id_ejecucion"] = data.get("run_id", "sin_id")

    if "generado_en_utc" not in data:
        data["generado_en_utc"] = data.get("generated_at_utc", "desconocido")

    if "directorios" not in data and "directories" in data:
        dirs = data.get("directories", {})
        data["directorios"] = {
            "directorio_ejecucion": dirs.get("run_dir", ""),
            "pantallazos": dirs.get("screenshots", ""),
            "reportes": dirs.get("reportes", dirs.get("reportes", "")),
        }

    return data


def _status_color(resultado: str):
    if resultado == "aprobada":
        return colors.green
    if resultado == "fallida":
        return colors.red
    if resultado == "omitida":
        return colors.orange
    return colors.black


def _build_story(data: Dict, pruebas: List[Dict], titulo: str):
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(titulo, styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"ID de ejecucion: <b>{escape(str(data.get('id_ejecucion', 'desconocido')))}</b>", styles["Normal"]))
    story.append(Paragraph(f"Generado UTC: <b>{escape(str(data.get('generado_en_utc', 'desconocido')))}</b>", styles["Normal"]))

    resumen = data.get("resumen", {})
    resumen_texto = (
        f"Total: <b>{resumen.get('total', 0)}</b> | "
        f"Aprobadas: <b>{resumen.get('aprobadas', 0)}</b> | "
        f"Fallidas: <b>{resumen.get('fallidas', 0)}</b> | "
        f"Omitidas: <b>{resumen.get('omitidas', 0)}</b>"
    )
    story.append(Paragraph(resumen_texto, styles["Normal"]))
    story.append(Spacer(1, 16))

    for idx, prueba in enumerate(pruebas):
        id_prueba = str(prueba.get("id_prueba", "sin_id"))
        nombre_prueba = str(prueba.get("nombre_prueba", id_prueba))
        resultado = str(prueba.get("resultado", "desconocido"))
        duracion = prueba.get("duracion_segundos", 0)
        pantallazos = prueba.get("pantallazos", [])

        story.append(Paragraph(f"Prueba: <b>{escape(nombre_prueba)}</b>", styles["Heading2"]))
        story.append(Paragraph(f"ID tecnico: <b>{escape(id_prueba)}</b>", styles["Normal"]))
        story.append(
            Paragraph(
                f"Resultado: <font color='{_status_color(resultado)}'><b>{escape(resultado.upper())}</b></font>",
                styles["Normal"],
            )
        )
        story.append(Paragraph(f"Duracion: <b>{duracion} s</b>", styles["Normal"]))

        error = str(prueba.get("error", "") or "")
        if error:
            story.append(Paragraph(f"Error: <b>{escape(error)}</b>", styles["Normal"]))

        if not pantallazos:
            story.append(Paragraph("Sin pantallazos registrados.", styles["Normal"]))
        else:
            story.append(Spacer(1, 8))
            for shot in pantallazos:
                shot_path = Path(shot)
                story.append(Paragraph(f"Pantallazo: {escape(shot_path.name)}", styles["Normal"]))
                story.append(_build_image_flowable(shot_path))
                story.append(Spacer(1, 10))

        if idx < len(pruebas) - 1:
            story.append(PageBreak())

    return story


def _render_text_frame(title: str, lines: list[str], current_line_idx: int, current_char_idx: int, width=1400, height=800) -> np.ndarray:
    margin = 36
    line_height = 20
    img = PILImage.new("RGB", (width, height), color=(20, 20, 20))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    draw.text((margin, margin), title, fill=(0, 255, 0), font=font) # Verde para el titulo "Terminal"
    
    y = margin + 2 * line_height
    for i, line in enumerate(lines):
        if i < current_line_idx:
            draw.text((margin, y), line, fill=(230, 230, 230), font=font)
            y += line_height
        elif i == current_line_idx:
            # Dibujar solo parte del texto
            snippet = line[:current_char_idx]
            draw.text((margin, y), snippet + "_", fill=(230, 230, 230), font=font)
            y += line_height
            break # No dibujar lineas futuras
        else:
            break
            
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def _generate_video_from_capturas(capturas: List[Dict[str, Any]], output_path: Path, fps: int = 30):
    if not capturas:
        return

    width, height = 1400, 800
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    for cap in capturas:
        lines = cap.get("lineas", [])
        paso = cap.get("paso", "Ejecutando...")
        title = f"BAPE TEST TERMINAL - {paso}"
        
        # Envolver lineas para que no se salgan del video
        wrapped_total_lines = []
        for line in lines:
            wrapped = textwrap.wrap(line, width=120) or [""]
            wrapped_total_lines.extend(wrapped)

        # Animacion de escritura
        frame = None
        for l_idx, line in enumerate(wrapped_total_lines):
            # Velocidad variable: mas rapido para bloques grandes de cuerpo
            step = 1 if len(line) < 50 else 2
            for c_idx in range(0, len(line) + 1, step):
                frame = _render_text_frame(title, wrapped_total_lines, l_idx, c_idx, width, height)
                video.write(frame)
            
            # Pequeña pausa al final de cada linea importante
            if any(x in line for x in ["PRUEBA:", "PASO:", "ESTADO_HTTP:"]):
                for _ in range(5): video.write(frame)

        # Pausa al final de la captura (2 segundos)
        if frame is not None:
            for _ in range(fps * 2):
                video.write(frame)

    video.release()


def generate_reports(results_json_path: Path) -> Dict[str, str]:
    data_raw = json.loads(results_json_path.read_text(encoding="utf-8"))
    data = _normalizar_data(data_raw)

    pruebas_map = data.get("pruebas", {})
    pruebas = sorted(pruebas_map.values(), key=lambda item: item.get("id_prueba", ""))

    directorios = data.get("directorios", {})
    run_dir = Path(directorios.get("directorio_ejecucion", results_json_path.parent))
    reportes_dir = run_dir / "reportes"
    por_prueba_dir = reportes_dir / "por_prueba"
    reportes_dir.mkdir(parents=True, exist_ok=True)
    por_prueba_dir.mkdir(parents=True, exist_ok=True)

    id_ejecucion = str(data.get("id_ejecucion", run_dir.name))
    pdf_consolidado = reportes_dir / f"reporte_pruebas_{id_ejecucion}.pdf"

    doc = SimpleDocTemplate(str(pdf_consolidado), pagesize=A4)
    doc.build(_build_story(data, pruebas, "Reporte automatizado de pruebas - BAPE"))

    videos_dir = run_dir / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)

    for prueba in pruebas:
        id_prueba = str(prueba.get("id_prueba", "sin_id"))
        nombre_prueba = str(prueba.get("nombre_prueba", id_prueba))
        
        # Generar PDF individual
        pdf_prueba = por_prueba_dir / f"{_safe_name(nombre_prueba)}.pdf"
        single_doc = SimpleDocTemplate(str(pdf_prueba), pagesize=A4)
        single_doc.build(_build_story(data, [prueba], f"Reporte individual - {nombre_prueba}"))

        # Generar Video Animado
        capturas = prueba.get("capturas", [])
        if capturas:
            video_path = videos_dir / f"{_safe_name(nombre_prueba)}.mp4"
            _generate_video_from_capturas(capturas, video_path, fps=30)

    return {
        "pdf_consolidado": str(pdf_consolidado),
        "carpeta_por_prueba": str(por_prueba_dir),
        "carpeta_videos": str(videos_dir),
    }


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Uso: python PRUEBAS/generar_reporte_pdf.py <ruta_results.json>")
        return 1

    results_path = Path(argv[1]).resolve()
    if not results_path.exists():
        print(f"No existe results.json en: {results_path}")
        return 1

    outputs = generate_reports(results_path)
    print("Reporte PDF consolidado:", outputs["pdf_consolidado"])
    print("Reportes PDF por prueba:", outputs["carpeta_por_prueba"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
