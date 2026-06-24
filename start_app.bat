@echo off
title 株トレードアシスタント
echo 起動中...
start "" "http://localhost:8501"
G:\trading_venv\Scripts\python -m streamlit run "g:\ビジネス\claudecode\trading_app\app.py" --server.headless true
pause
