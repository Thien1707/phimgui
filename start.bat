@echo off
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo Creating venv...
  python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt -q
if not exist .env copy .env.example .env
echo Run init.sql in MySQL Workbench, then: python -m backend.seed
python run_desktop.py
