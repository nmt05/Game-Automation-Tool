@echo off
cd /d "%~dp0"
chcp 65001
title Building AutoEgg v1.0.0

echo 🚀 Bắt đầu build AutoEgg v1.0.0...

echo 📁 Dọn dẹp...
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul
rmdir /s /q obf 2>nul
del /q *.spec 2>nul

echo.
echo 🔧 Cấu hình PyArmor...
pyarmor cfg obf-code 3
pyarmor cfg obf-module 2
pyarmor cfg wrap-mode 1
pyarmor cfg restrict 1
pyarmor cfg enable_suffix 0
pyarmor cfg manifest "include eggtool.py;include hunttool.py;include license.py;include Numread.py;include *.py"

echo.
echo 🔒 Đang mã hóa toàn bộ project...
pyarmor gen -O obf -r .

if errorlevel 1 (
    echo ❌ PyArmor lỗi. Dừng build.
    pause
    exit /b
)

echo.
echo 🏗️ Đang build EXE...
pyinstaller ^
 --onefile --noconsole ^
 --hidden-import=pytesseract ^
 --hidden-import=PIL ^
 --hidden-import=PIL._tkinter_finder ^
 --hidden-import=PIL.Image ^
 --hidden-import=PIL.ImageTk ^
 --hidden-import=tkinter ^
 --hidden-import=winsound ^
 --hidden-import=random ^
 --hidden-import=tkinter.messagebox ^
 --hidden-import=tkinter.ttk ^
 --hidden-import=tkinter.filedialog ^
 --hidden-import=cv2 ^
 --hidden-import=numpy ^
 --hidden-import=requests ^
 --collect-all pytesseract ^
 --collect-all PIL ^
 --collect-all tkinter ^
 --add-data "obf;." ^
 --add-data "platform-tools;platform-tools" ^
 --add-data "Tesseract-OCR;Tesseract-OCR" ^
 --name AutoEgg_v1.0.0 ^
 "obf\eggtool_gui.py"

echo.
if exist dist\AutoEgg_v1.0.0.exe (
    echo ✅ Build thành công!
    echo 📍 File: dist\AutoEgg_v1.0.0.exe
) else (
    echo ❌ Build thất bại!
)

echo.
pause