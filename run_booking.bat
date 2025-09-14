@echo off
chcp 65001 > nul
echo 病院予約自動化プログラムを開始します...
echo.

REM Pythonがインストールされているかチェック
python --version > nul 2>&1
if errorlevel 1 (
    echo エラー: Pythonがインストールされていません。
    echo Python 3.8以上をインストールしてください。
    pause
    exit /b 1
)

REM 仮想環境を作成（初回のみ）
if not exist "venv" (
    echo 仮想環境を作成中...
    python -m venv venv
)

REM 仮想環境をアクティベート
echo 仮想環境をアクティベート中...
call venv\Scripts\activate.bat

REM 依存関係をインストール
echo 依存関係をインストール中...
pip install -r requirements.txt

REM プログラム実行
echo.
echo 予約自動化プログラムを実行中...
echo 一度だけ実行する場合は: python hospital_booking_automation.py --once
echo スケジューラー実行する場合は: python hospital_booking_automation.py
echo.

python hospital_booking_automation.py

pause
