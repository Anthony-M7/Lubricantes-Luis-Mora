@echo off
:: Archivo para manejo de dependencias del proyecto

:: 1. Activar el entorno virtual
cd /d C:\Users\crist\OneDrive\Escritorio\Lubricantes-Luis-Mora
@REM cd /d C:\Users\USUARIO\Desktop\Programación\Django - Sitio Lubricantes Luis Mora

call virtualenv\Scripts\activate

:: Menú de opciones
echo Seleccione una opción:
echo 1. Generar requirements.txt (freeze)
echo 2. Instalar dependencias desde requirements.txt
echo 3. Ambas operaciones (freeze + install)
echo 4. Salir
set /p opcion="Opción [1-4]: "

if "%opcion%"=="1" goto freeze
if "%opcion%"=="2" goto install
if "%opcion%"=="3" goto both
if "%opcion%"=="4" goto end

:freeze
echo Generando archivo requirements.txt...
pip freeze > requirements.txt
echo requirements.txt generado correctamente.
goto end

:install
echo Instalando dependencias...
pip install -r requirements.txt
echo Dependencias instaladas correctamente.
goto end

:both
echo Generando e instalando dependencias...
pip freeze > requirements.txt
pip install -r requirements.txt
echo Operación completada.
goto end

:end
pause