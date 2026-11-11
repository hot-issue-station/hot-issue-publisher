@echo off
chcp 65001 >nul
rem 업로드 전용 크롬 프로필로 네 사이트 로그인 화면을 엽니다. 대표님이 직접 로그인하고 창을 닫으면 끝.
set "PROFILE=%LOCALAPPDATA%\DuksimUploader\chrome_profile"
if not "%DUKSIM_PROFILE%"=="" set "PROFILE=%DUKSIM_PROFILE%"
set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" ( echo 크롬을 찾지 못했습니다. & pause & exit /b 1 )
echo 업로드 전용 크롬 창이 열립니다. 탭 4개에서 각각 로그인해 주세요.
echo (유튜브 Studio / 틱톡 Studio / 비즈니스 스위트 / X) 로그인을 마치면 크롬 창을 모두 닫으세요.
start "" "%CHROME%" --user-data-dir="%PROFILE%" "https://studio.youtube.com" "https://www.tiktok.com/tiktokstudio/upload" "https://business.facebook.com/latest/home" "https://x.com/home"
pause
