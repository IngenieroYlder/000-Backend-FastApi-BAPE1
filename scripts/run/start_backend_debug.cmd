@echo off
title BAPE Backend Debug
echo "Starting Backend in Debug Mode..."
cd /d "d:\Colombia Picture\n8n agente ia burbuja\000 Backend FastApi BAPE"
call .\venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload --port 8003
pause
