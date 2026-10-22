@echo off
setlocal
cd /d "%~dp0"
echo ===== TORRE LOCA: pruebas, ejecutable e instalador =====

where python >nul 2>nul
if errorlevel 1 (
  echo No se encontro Python 3.10 o superior en el PATH.
  exit /b 1
)

if not exist .venv\Scripts\python.exe python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller
if errorlevel 1 exit /b 1

echo.
echo ----- Ejecutando pruebas -----
python -m unittest discover -s tests -v
if errorlevel 1 (
  echo Las pruebas fallaron. No se genera el ejecutable.
  exit /b 1
)

echo.
echo ----- Generando TorreLoca.exe -----
set ICONO=
if exist assets\icono.ico set ICONO=--icon assets\icono.ico
pyinstaller --noconfirm --clean --onefile --windowed --name TorreLoca %ICONO% --add-data "assets;assets" main.py
if errorlevel 1 exit /b 1
if not exist dist\TorreLoca.exe (
  echo No se genero dist\TorreLoca.exe
  exit /b 1
)
echo OK: dist\TorreLoca.exe

echo.
echo ----- Generando InstalarTorreLoca.exe (requiere Inno Setup 6) -----
set ISCC=
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" (
  echo Inno Setup 6 no esta instalado. Descargalo de https://jrsoftware.org/isinfo.php
  echo y vuelve a ejecutar build.bat. El ejecutable ya esta listo en dist\TorreLoca.exe
  exit /b 0
)
"%ISCC%" installer\TorreLoca.iss
if errorlevel 1 exit /b 1
if not exist dist\InstalarTorreLoca.exe (
  echo No se genero dist\InstalarTorreLoca.exe
  exit /b 1
)
echo OK: dist\InstalarTorreLoca.exe
endlocal
