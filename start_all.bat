@echo off
echo 📦 Starting Full Copy Trading Stack...

REM Start backend server
start cmd /k "cd backend && python app.py"

:: REM Start LTP socket listener
:: start cmd /k "cd backend && python ltp_socket.py"

REM Start frontend React app
start cmd /k "cd frontend && npm start"

echo ✅ All services started in separate terminals.
