# .venv\Scripts\activate.bat
Set-Location project
# austin -i 100 --pipe  python.exe main.py
# austin-tui python.exe main.py
# delay profiling by 4 secounds, record for 5 secounds, store file in profiling folder
austin -t 4s -x 5 -bo "..\profiling\austin_$((Get-Date).ToString('yyyyMMdd_HHmmss')).aprof" python main.py

Set-Location ..
