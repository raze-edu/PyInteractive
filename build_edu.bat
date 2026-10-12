@echo off
rem EduMath Windows Build Shortcut
rem Usage: build_edu.bat [optional arguments, e.g. -v 1.0.1 --console]
echo ===================================================
echo   EduMath Automated Executable Builder
echo ===================================================
python build_edu.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed with error code %ERRORLEVEL%.
) else (
    echo.
    echo [DONE] Build completed successfully.
)
pause
