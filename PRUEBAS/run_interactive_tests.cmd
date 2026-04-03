@echo off
set BAPE_INTERACTIVE=True
set BAPE_TEST_RUN_DIR=PRUEBAS/evidencias/manual_interactivo

:: Navegar a la carpeta raiz del proyecto (padre de donde esta este script)
pushd %~dp0..

echo ============================================================
echo   MODO INTERACTIVO DE PRUEBAS - BAPE
echo ============================================================
echo   Ubicacion: %CD%
echo.

if exist venv\Scripts\python.exe (
    :: Ejecutar todas las pruebas de la carpeta tests en modo interactivo y sin captura de salida (-s)
    venv\Scripts\python.exe -m pytest -s PRUEBAS/tests/
) else (
    echo [ERROR] No se encontro la carpeta 'venv' en: %CD%
    echo Por favor, asegurate de que el entorno virtual este instalado.
)

echo.
echo ============================================================
echo   Pruebas finalizadas.
echo ============================================================
popd
pause
