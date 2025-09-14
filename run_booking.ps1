# 病院予約自動化プログラム実行スクリプト
Write-Host "病院予約自動化プログラムを開始します..." -ForegroundColor Green
Write-Host ""

# Pythonがインストールされているかチェック
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Pythonバージョン: $pythonVersion" -ForegroundColor Cyan
} catch {
    Write-Host "エラー: Pythonがインストールされていません。" -ForegroundColor Red
    Write-Host "Python 3.8以上をインストールしてください。" -ForegroundColor Yellow
    Read-Host "Enterキーを押して終了"
    exit 1
}

# 仮想環境を作成（初回のみ）
if (-not (Test-Path "venv")) {
    Write-Host "仮想環境を作成中..." -ForegroundColor Yellow
    python -m venv venv
}

# 仮想環境をアクティベート
Write-Host "仮想環境をアクティベート中..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# 依存関係をインストール
Write-Host "依存関係をインストール中..." -ForegroundColor Yellow
pip install -r requirements.txt

# プログラム実行
Write-Host ""
Write-Host "予約自動化プログラムを実行中..." -ForegroundColor Green
Write-Host "一度だけ実行する場合は: python hospital_booking_automation.py --once" -ForegroundColor Cyan
Write-Host "スケジューラー実行する場合は: python hospital_booking_automation.py" -ForegroundColor Cyan
Write-Host ""

python hospital_booking_automation.py

Read-Host "Enterキーを押して終了"
