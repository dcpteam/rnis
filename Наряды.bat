@echo off
chcp 1251
call %HOMEPATH%\anaconda3\envs\rnis\Lib\venv\scripts\nt\activate.bat
echo ��� �������?
echo 1. ������� ������
echo 2. ����� ������
echo 3. ��������� ������������
set /P INPUT=%=%
If "%INPUT%"=="1" python download_reports.py
If "%INPUT%"=="2" python add_uuid_exits.py
If "%INPUT%"=="3" python click_orders_multithreading.py
pause