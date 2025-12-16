@echo off
:: Zorg dat het script altijd werkt vanuit zijn eigen map
pushd "%~dp0"
title Begrippenkader Menu

:menu
cls
echo ========================================================
echo                 BEGRIPPENKADER MENU
echo ========================================================
echo.
echo   [1] SETUP   (Dependencies installeren)
echo   [2] CLEAN   (Oude bestanden opruimen)
echo   [3] BUILD   (Site genereren)
echo   [4] SERVE   (Lokaal bekijken)
echo.
echo   [Q] STOPPEN
echo.
echo ========================================================
set /p choice=Maak een keuze: 

if /i "%choice%"=="1" goto do_setup
if /i "%choice%"=="2" goto do_clean
if /i "%choice%"=="3" goto do_build
if /i "%choice%"=="4" goto do_serve
if /i "%choice%"=="q" goto end

echo.
echo Ongeldige keuze, probeer opnieuw...
timeout /t 1 >nul
goto menu

:: --- ACTIES ---

:do_setup
echo.
call setup.cmd
echo.
echo Druk op een toets om terug te gaan naar het menu...
pause >nul
goto menu

:do_clean
echo.
call clean.cmd
echo.
echo Klaar met opruimen.
timeout /t 2 >nul
goto menu

:do_build
echo.
call build.cmd
echo.
echo Druk op een toets om terug te gaan naar het menu...
pause >nul
goto menu

:do_serve
echo.
echo De server start nu...
echo (Druk in het venster op Ctrl+C om te stoppen en terug te keren)
echo.
call serve.cmd
goto menu

:end
popd
