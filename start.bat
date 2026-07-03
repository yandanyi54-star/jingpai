@echo off
echo 正在启动 PodcastPublish 排版工具...
cd /d "%~dp0backend"
call venv\Scripts\activate
start python app.py
timeout /t 2 /nobreak > nul
start http://localhost:5000
echo 启动完成！浏览器将自动打开。
pause