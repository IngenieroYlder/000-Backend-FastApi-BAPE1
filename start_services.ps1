Write-Host "STOPPING OLD PROCESSES (CLEANUP)..." -ForegroundColor Yellow
taskkill /F /IM node.exe /T 2>$null
taskkill /F /IM python.exe /T 2>$null
taskkill /F /IM uvicorn.exe /T 2>$null

Start-Sleep -Seconds 2

Write-Host "STARTING BAPE SERVICES..." -ForegroundColor Green

# Start Backend (FastAPI)
Write-Host "Launching Backend (FastAPI)..." -ForegroundColor Cyan
$backendCmd = "cd 'd:\Colombia Picture\n8n agente ia burbuja\000 Backend FastApi BAPE'; $host.ui.RawUI.WindowTitle = 'OFFICIAL BAPE BACKEND (Port 8000)'; Write-Host 'backend running...'; & '.\venv\Scripts\python.exe' -m uvicorn app.main:app --reload --port 8000"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $backendCmd

# Start-Sleep to let backend init
Start-Sleep -Seconds 3

# Start Baileys Engine
Write-Host "Launching Baileys Engine..." -ForegroundColor Cyan
$baileysCmd = "cd 'd:\Colombia Picture\n8n agente ia burbuja\000 Backend FastApi BAPE\baileys_engine'; $host.ui.RawUI.WindowTitle = 'OFFICIAL BAILEYS ENGINE (Port 3001)'; npm start"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $baileysCmd

Write-Host "Services started!" -ForegroundColor Green
Write-Host "Backend: http://localhost:8000"
Write-Host "Baileys: http://localhost:3001"
