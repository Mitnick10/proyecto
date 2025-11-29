@echo off
cd /d "%~dp0"
set FLASK_APP=project/app.py
set FLASK_ENV=development
set FLASK_PORT=5000
set FLASK_HOST=127.0.0.1
echo Iniciando aplicacion Flask en localhost:5000...
echo Accede a: http://localhost:5000
python project/app.py
pause
