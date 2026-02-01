Write-Host "🚀 Inizio procedura di RESET TOTALE..." -ForegroundColor Cyan

# 1. Spegnimento Container
Write-Host "[1/5] Spegnimento container Docker..." -ForegroundColor Yellow
docker compose down

# 2. Eliminazione cartelle dati (Gestione errori se file in uso)
Write-Host "[2/5] Eliminazione dati fisici (SQL, Vector, Uploads)..." -ForegroundColor Yellow
$folders = @("postgres_data", "qdrant_data", "uploads")

foreach ($folder in $folders) {
    if (Test-Path $folder) {
        try {
            Remove-Item -Recurse -Force $folder -ErrorAction Stop
            Write-Host "   ✅ $folder eliminata." -ForegroundColor Green
        } catch {
            Write-Warning "   ❌ Impossibile eliminare $folder. Assicurati che non ci siano file aperti o Docker bloccati."
        }
    }
}

# 3. Ricreazione cartella uploads (necessaria per l'app)
if (!(Test-Path "uploads")) {
    New-Item -ItemType Directory -Path "uploads" | Out-Null
    Write-Host "[3/5] Cartella 'uploads' ricreata." -ForegroundColor Green
}

# 4. Riavvio Database
Write-Host "[4/5] Riavvio database puliti..." -ForegroundColor Yellow
docker compose up -d

# Attendiamo qualche secondo per l'avvio di Postgres
Write-Host "   ⏳ Attesa avvio PostgreSQL (10s)..."
Start-Sleep -Seconds 10

# 5. Re-inizializzazione SQL
Write-Host "[5/5] Inizializzazione tabelle SQL e utenti..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\activate.ps1") {
    # Se esiste l'ambiente virtuale, lo usiamo per lanciare lo script
    powershell -Command "& {.\venv\Scripts\activate; python init_db.py}"
} else {
    python init_db.py
}

Write-Host "`n✨ SISTEMA RESETTATO E PRONTO! ✨" -ForegroundColor Cyan
Write-Host "Ora puoi lanciare: streamlit run app.py" -ForegroundColor White
