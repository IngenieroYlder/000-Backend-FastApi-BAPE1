@echo off
echo "STOPPING OLD PROCESSES..."
taskkill /F /IM uvicorn.exe /T 2>NUL
taskkill /F /IM python.exe /T 2>NUL
taskkill /F /IM node.exe /T 2>NUL

echo "Launching all services in debug windows..."
start "BAPE Backend" "d:\Colombia Picture\n8n agente ia burbuja\000 Backend FastApi BAPE\start_backend_debug.cmd"
start "BAPE Baileys" "d:\Colombia Picture\n8n agente ia burbuja\000 Backend FastApi BAPE\start_baileys_debug.cmd"
echo "Services launched. Check the new windows for logs."
pause
