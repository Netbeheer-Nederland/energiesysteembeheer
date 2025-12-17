@echo off
setlocal enabledelayedexpansion
title Begrippenkader Launcher

:: ========================================================
:: CONFIGURATIE
:: ========================================================
:: Map waarin portable versies gezocht worden (relatief aan dit script)
set TOOLS_DIR=tools

echo ========================================================
echo   Systeemcontrole ^& start
echo ========================================================

:: --------------------------------------------------------
:: STAP 1: PYTHON ZOEKEN (Portable > Systeem)
:: --------------------------------------------------------
set PYTHON_FOUND=0

:: Check 1: Portable Python (bijv. WinPython uitgepakt in tools/python)
if exist "%~dp0%TOOLS_DIR%\python\python.exe" (
    echo [INFO] Portable Python gevonden in %TOOLS_DIR%\python...
    :: Voeg python en de scripts map toe aan de PATH van deze sessie
    set PATH=%~dp0%TOOLS_DIR%\python;%~dp0%TOOLS_DIR%\python\Scripts;%PATH%
    set PYTHON_FOUND=1
) else (
    :: Check 2: Systeem Python
    python --version >nul 2>&1
    if !errorlevel! equ 0 set PYTHON_FOUND=1
)

if !PYTHON_FOUND!==0 (
    cls
    echo [FOUT] Geen Python gevonden!
    echo.
    echo Optie A ^(je hebt admin-rechten^):
    echo    Installeer Python via https://www.python.org/downloads/
    echo    ^(Vink aan: "Add Python to PATH"^)
    echo.
    echo Optie B ^(je hebt GEEN admin-rechten^):
    echo    1. Download WinPython.
    echo    2. Pak het uit.
    echo    3. Hernoem de map met 'python.exe' erin naar 'python'.
    echo    4. Plaats die map in: %~dp0%TOOLS_DIR%\
    echo       ^(Je krijgt dus: %~dp0%TOOLS_DIR%\python\python.exe^)
    echo.
    pause
    exit /b 1
) else (
    echo [OK] Python is actief.
)

:: --------------------------------------------------------
:: STAP 2: RUBY ZOEKEN (Portable > Systeem)
:: --------------------------------------------------------
set RUBY_FOUND=0

:: Check 1: Portable Ruby (bijv. Ruby+Devkit uitgepakt in tools/ruby)
if exist "%~dp0%TOOLS_DIR%\ruby\bin\ruby.exe" (
    echo [INFO] Portable Ruby gevonden in %TOOLS_DIR%\ruby...
    set PATH=%~dp0%TOOLS_DIR%\ruby\bin;%PATH%
    set RUBY_FOUND=1
) else (
    :: Check 2: Systeem Ruby
    ruby --version >nul 2>&1
    if !errorlevel! equ 0 set RUBY_FOUND=1
)

if !RUBY_FOUND!==0 (
    cls
    echo [FOUT] Geen Ruby gevonden!
    echo.
    echo Optie A ^(Je hebt admin rechten^):
    echo    Installeer Ruby+Devkit via https://rubyinstaller.org/
    echo.
    echo Optie B ^(Je hebt GEEN admin rechten^):
    echo    1. Download de 'Archives' versie ^(7z of zip^) van Ruby+Devkit.
    echo    2. Pak uit en hernoem de map naar 'ruby'.
    echo    3. Plaats die map in: %~dp0%TOOLS_DIR%\
    echo       ^(Je krijgt dus: %~dp0%TOOLS_DIR%\ruby\bin\ruby.exe^)
    echo.
    pause
    exit /b 1
) else (
    echo [OK] Ruby is actief.
)

:: --------------------------------------------------------
:: STAP 3: BOOTSTRAP INVOKE
:: --------------------------------------------------------
:: We gebruiken nu de python die we gevonden hebben (portable of systeem)
python -c "import invoke" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Eerste keer opstarten: dependencies installeren...
    python -m pip install invoke >nul
)

:: --------------------------------------------------------
:: STAP 4: START MENU
:: --------------------------------------------------------
cls
:: Start invoke. Omdat we Scripts aan PATH hebben toegevoegd, werkt 'inv' ook met portable python.
inv menu

if %errorlevel% neq 0 (
    echo.
    echo Er is iets misgegaan of het script is afgesloten.
    pause >nul
)

endlocal
