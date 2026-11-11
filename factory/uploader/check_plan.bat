@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
rem 사용법: 기획 JSON 파일을 이 파일 위에 끌어다 놓기. 업로드는 하지 않고 점검표만 보여 줍니다.
if "%~1"=="" ( echo 기획 JSON 파일을 이 파일 위에 끌어다 놓아 주세요. & pause & exit /b 1 )
py "%~dp0upload_plan.py" "%~1"
pause
