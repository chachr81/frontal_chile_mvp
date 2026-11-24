# Crea el entorno de desarrollo en esta carpeta (Windows PowerShell).
# Uso:  .\setup.ps1
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# 1) Entorno virtual local (.venv) con el Python disponible en el sistema.
python -m venv .venv

# 2) Actualiza pip e instala las dependencias y el paquete en modo editable.
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m pip install -e .

# 3) Verifica que las pruebas pasan antes de comenzar a trabajar.
& .\.venv\Scripts\python.exe -m pytest -q

Write-Host "Entorno listo. Active con: .\.venv\Scripts\Activate.ps1"
Write-Host "Ejecute el visor con:      streamlit run src/frontal/app/streamlit_app.py"
