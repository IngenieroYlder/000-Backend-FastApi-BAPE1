@echo off
setlocal
echo ============================================================
echo   CONFIGURADOR DE ENTORNO VIRTUAL - BAPE
echo ============================================================
echo.

:: Verificar si python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se encontro 'python' en el sistema. 
    echo Por favor instala Python 3.10+ y agregalo al PATH.
    pause
    exit /b 1
)

:: Crear el venv si no existe
if not exist venv (
    echo [+] Creando entorno virtual (venv)...
    python -m venv venv
) else (
    echo [!] El entorno virtual ya existe. Actualizando dependencias...
)

:: Actualizar pip e instalar dependencias
echo.
echo [+] Instalando dependencias base (requirements.txt)...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt

echo.
echo [+] Instalando dependencias de pruebas (PRUEBAS/requirements-test.txt)...
venv\Scripts\python.exe -m pip install -r PRUEBAS/requirements-test.txt

echo.
echo ============================================================
echo   INSTALACION COMPLETADA CON EXITO
echo ============================================================
echo   Ahora puedes ejecutar las pruebas interactivas con:
echo   .\PRUEBAS\run_interactive_tests.cmd
echo ============================================================
pause
