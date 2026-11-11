@echo off
chcp 65001 >nul
echo [1/2] 업로드 프로그램 준비(Playwright 설치) - 처음 한 번만
py -m pip install --upgrade playwright tzdata pillow
echo.
echo [2/2] 크롬은 이미 설치된 것을 그대로 씁니다(브라우저 추가 다운로드 없음).
echo 끝났습니다. 다음은 login_once.bat 을 두 번 클릭하세요.
pause
