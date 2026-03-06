Write-Host "MATANDO TODOS LOS PROCESOS DE BAPE..." -ForegroundColor Red
taskkill /F /IM python.exe /T
taskkill /F /IM node.exe /T
taskkill /F /IM uvicorn.exe /T
taskkill /F /IM ngrok.exe /T
Write-Host "✅ Limpieza completada. Ahora puedes iniciar de nuevo." -ForegroundColor Green
