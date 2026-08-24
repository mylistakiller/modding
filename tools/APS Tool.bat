@echo off
cd /d "%~dp0"
py hs2_aps_tool.py || python hs2_aps_tool.py
pause
