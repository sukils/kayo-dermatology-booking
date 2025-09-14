# 病院予約自動化プログラム

かよ皮膚科のWeb予約システムを自動で操作するPythonプログラムです。

## 機能

- 指定した日時に自動で予約ページにアクセス
- 予約フォームの自動入力・送信
- スクリーンショットによる実行状況の記録
- ログ機能で実行状況を詳細に記録
- エラーハンドリングとリトライ機能

## 必要な環境

- Python 3.8以上
- Google Chrome ブラウザ
- ChromeDriver（自動でダウンロードされます）

## セットアップ

### 1. 依存関係のインストール

```bash
# 仮想環境を作成
python -m venv venv

# 仮想環境をアクティベート
# Windows
venv\Scripts\activate.bat
# macOS/Linux
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt
```

### 2. 設定ファイルの編集

`config.json`を編集して、以下の情報を設定してください：

- **patient_info**: 患者の基本情報（名前、電話番号、メールアドレス）
- **booking_times**: 予約を実行する曜日と時間
- **chrome_options**: ブラウザの設定

## 使用方法

### 一度だけ実行

```bash
python hospital_booking_automation.py --once
```

### スケジューラー実行（推奨）

```bash
python hospital_booking_automation.py
```

### Windows用バッチファイル

`run_booking.bat`をダブルクリックして実行

### PowerShell用スクリプト

```powershell
.\run_booking.ps1
```

## 設定項目

### 予約時間設定

```json
"booking_times": [
    {
        "day": "monday",
        "time": "12:00",
        "enabled": true
    }
]
```

- `day`: 曜日（monday, tuesday, wednesday, thursday, friday）
- `time`: 時間（24時間形式）
- `enabled`: 有効/無効の切り替え

### 患者情報

```json
"patient_info": {
    "name": "患者様",
    "phone": "090-0000-0000",
    "email": "patient@example.com"
}
```

### ブラウザ設定

```json
"chrome_options": {
    "headless": false,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

- `headless`: ヘッドレスモード（true: 画面表示なし、false: 画面表示あり）
- `user_agent`: ブラウザのユーザーエージェント

## ログとスクリーンショット

- **ログファイル**: `hospital_booking.log`
- **スクリーンショット**: 実行時の各段階で自動保存
  - `before_booking.png`: 予約開始前
  - `before_submit.png`: 送信前
  - `after_submit.png`: 送信後
  - `error_screenshot.png`: エラー発生時

## 注意事項

1. **利用規約の確認**: 病院のWeb予約システムの利用規約を必ず確認してください
2. **個人情報の管理**: 設定ファイルに含まれる個人情報は適切に管理してください
3. **ネットワーク環境**: 安定したインターネット接続が必要です
4. **ブラウザ更新**: Chromeブラウザは最新版に更新してください

## トラブルシューティング

### よくある問題

1. **ChromeDriverエラー**
   - Chromeブラウザを最新版に更新
   - プログラムを再実行（自動でダウンロードされます）

2. **要素が見つからない**
   - 病院のWebサイトの構造が変更された可能性
   - 設定ファイルのXPathを確認・調整

3. **タイムアウトエラー**
   - ネットワーク接続を確認
   - 設定ファイルで待機時間を調整

### ログの確認

エラーが発生した場合は、`hospital_booking.log`ファイルを確認してください。詳細なエラー情報が記録されています。

## ライセンス

このプログラムは個人利用を目的としています。商用利用は禁止されています。

## サポート

問題が発生した場合は、ログファイルとスクリーンショットを確認してから、適切な対処を行ってください。
