@echo off
:: Test01 Mandatory
python .\main.py public/instances/public1.txt public/my_solutions/public1.txt
fc public\solutions\public1.txt public\my_solutions\public1.txt

:: Test02 Mandatory
python .\main.py public/instances/public2.txt public/my_solutions/public2.txt
fc public\solutions\public2.txt public\my_solutions\public2.txt

:: Test03 Mandatory
python .\main.py public/instances/public3.txt public/my_solutions/public3.txt
fc public\solutions\public3.txt public\my_solutions\public3.txt

:: Test04 Mandatory
python .\main.py public/instances/public4.txt public/my_solutions/public4.txt
fc public\solutions\public4.txt public\my_solutions\public4.txt

:: Test05 Mandatory
python .\main.py public/instances/public5.txt public/my_solutions/public5.txt
fc public\solutions\public5.txt public\my_solutions\public5.txt

:: Test06 Mandatory
python .\main.py public/instances/public6.txt public/my_solutions/public6.txt
fc public\solutions\public6.txt public\my_solutions\public6.txt