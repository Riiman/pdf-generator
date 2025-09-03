@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Create venv
if not exist .venv (
    py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Ensure wkhtmltopdf is present
if not exist third_party\wkhtmltopdf\wkhtmltopdf.exe (
    echo [INFO] Place wkhtmltopdf.exe at third_party\wkhtmltopdf\wkhtmltopdf.exe
)

pyinstaller lettergen.spec --noconfirm

echo Build complete. See dist\LetterGen\LetterGen.exe
