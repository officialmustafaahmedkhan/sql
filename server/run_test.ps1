$env:PYTHONPATH = "D:\Downloads\sql-lab-platform\backend_python"
Start-Process python -ArgumentList "D:\Downloads\sql-lab-platform\backend_python\app.py" -WindowStyle Hidden -PassThru | Out-Null
Start-Sleep -Seconds 3

Write-Host "Testing Backend..."
python "D:\Downloads\sql-lab-platform\backend_python\test_api.py"