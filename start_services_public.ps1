Write-Host "STOPPING OLD PROCESSES (CLEANUP)..." -ForegroundColor Yellow
taskkill /F /IM node.exe /T 2>$null
taskkill /F /IM python.exe /T 2>$null
taskkill /F /IM uvicorn.exe /T 2>$null

Start-Sleep -Seconds 2

Write-Host "STARTING BAPE SERVICES (PUBLIC MODE)..." -ForegroundColor Green

# Start Backend (FastAPI + Ngrok)
Write-Host "Launching Backend (FastAPI + Ngrok)..." -ForegroundColor Cyan
# Usage of python start_public.py
$backendCmd = "cd 'd:\Colombia Picture\n8n agente ia burbuja\000 Backend FastApi BAPE'; $host.ui.RawUI.WindowTitle = 'OFFICIAL BAPE BACKEND (PUBLIC + NGROK)'; & '.\venv\Scripts\python.exe' start_public.py"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $backendCmd

# Start-Sleep to let backend init
Start-Sleep -Seconds 5

# Start Baileys Engine
Write-Host "Launching Baileys Engine..." -ForegroundColor Cyan
$baileysCmd = "cd 'd:\Colombia Picture\n8n agente ia burbuja\000 Backend FastApi BAPE\baileys_engine'; $host.ui.RawUI.WindowTitle = 'OFFICIAL BAILEYS ENGINE (Port 3001)'; npm start"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $baileysCmd

Write-Host "Services started in Public Mode!" -ForegroundColor Green
