@echo off
chcp 1251
call %HOMEPATH%\anaconda3\envs\rnis\Lib\venv\scripts\nt\activate.bat
echo Что сделать?
echo 1. Скачать отчеты
echo 2. Найти ссылки
echo 3. Запустить проставление
set /P INPUT=%=%
If "%INPUT%"=="1" python download_reports.py
If "%INPUT%"=="2" python add_uuid_exits.py
If "%INPUT%"=="3" python click_orders_multithreading.py
pause