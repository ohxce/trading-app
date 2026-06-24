Start-Process -FilePath "G:\trading_venv\Scripts\python.exe" `
    -ArgumentList "-m streamlit run `"g:\ビジネス\claudecode\trading_app\app.py`" --server.headless true" `
    -WindowStyle Hidden

Start-Sleep -Seconds 4
Start-Process "http://localhost:8501"
