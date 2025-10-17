@echo off
REM Git Sync Fix Script for Solar Dashboard
REM This resolves merge conflicts and syncs with remote repository

echo ========================================
echo Git Sync Fix Script
echo ========================================
echo.

cd C:\Users\Brandon\Documents\solar-dashboard

echo [1/6] Adding all changes...
git add .

echo [2/6] Committing local changes...
git commit -m "Sync local changes - %date% %time%"

echo [3/6] Pulling from remote (attempting merge)...
git pull origin main --no-rebase

REM Check if there are merge conflicts
git diff --name-only --diff-filter=U > conflicts.txt
set /p conflicts=<conflicts.txt
del conflicts.txt

if not "%conflicts%"=="" (
    echo.
    echo [!] Merge conflicts detected, resolving...
    
    REM Accept our version for all conflicts
    for /f "delims=" %%f in ('git diff --name-only --diff-filter=U') do (
        echo     Resolving: %%f
        git checkout --ours "%%f"
        git add "%%f"
    )
    
    echo [4/6] Committing resolved conflicts...
    git commit -m "Resolve merge conflicts - keep local versions"
) else (
    echo [4/6] No conflicts to resolve
)

echo [5/6] Pushing to remote...
git push origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo [SUCCESS] Git sync completed!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo [ERROR] Push failed - manual intervention needed
    echo ========================================
)

echo.
pause