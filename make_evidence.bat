@echo off
set PYTHONIOENCODING=utf-8
python -m pytest -v > evidence\final_run.txt 2>&1
python check_layers.py > evidence\layers_check.txt 2>&1
python -m interface.main > evidence\demo_run.txt 2>&1
echo Evidence written to the evidence folder.
pause
