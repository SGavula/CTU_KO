@echo off
:: Test01 Mandatory
python .\main.py public/instances/public-1.txt public/my_solutions/public-1.txt
fc public\solutions\public-1.txt public\my_solutions\public-1.txt

:: Test02 Mandatory
python .\main.py public/instances/cat_part.txt public/my_solutions/cat_part.txt
fc public\solutions\cat_part.txt public\my_solutions\cat_part.txt

:: Test03 Mandatory
python .\main.py public/instances/sheep.txt public/my_solutions/sheep.txt
fc public\solutions\sheep.txt public\my_solutions\sheep.txt

:: Test04 Mandatory
python .\main.py public/instances/triangle.txt public/my_solutions/triangle.txt
fc public\solutions\triangle.txt public\my_solutions\triangle.txt