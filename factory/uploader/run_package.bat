@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
rem 사용법: outbox\<꾸러미>\upload_plan.json 을 이 파일 위에 끌어다 놓기. (확인 모드: 예약 단추 직전에서 멈춤)
if "%~1"=="" ( echo upload_plan.json 파일을 이 파일 위에 끌어다 놓아 주세요. & pause & exit /b 1 )
echo 열려 있는 '업로드 전용' 크롬 창이 있으면 먼저 닫아 주세요.
py "%~dp0run.py" --plan "%~1"
pause
