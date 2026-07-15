@echo off
:: Test01 Mandatory
python .\main.py public/instances/1.txt public/my_solutions/1.txt
fc public\solutions\1.txt public\my_solutions\1.txt

:: Test02 Mandatory
python .\main.py public/instances/2.txt public/my_solutions/2.txt
fc public\solutions\2.txt public\my_solutions\2.txt

:: Test03 Mandatory
python .\main.py public/instances/3.txt public/my_solutions/3.txt
fc public\solutions\3.txt public\my_solutions\3.txt

:: Test04 Mandatory
python .\main.py public/instances/4.txt public/my_solutions/4.txt
fc public\solutions\4.txt public\my_solutions\4.txt

:: Test05 Mandatory
python .\main.py public/instances/5.txt public/my_solutions/5.txt
fc public\solutions\5.txt public\my_solutions\5.txt