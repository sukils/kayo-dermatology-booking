# かよ皮膚科予約管理アプリ - デプロイ手順

## 🚀 クイックデプロイ（Railway推奨）

### 1. 準備
1. GitHubアカウントを作成
2. このプロジェクトをGitHubリポジトリにプッシュ
3. Railwayアカウントを作成（GitHubでログイン）

### 2. デプロイ手順
1. [Railway](https://railway.app)にログイン
2. "New Project" をクリック
3. "Deploy from GitHub repo" を選択
4. リポジトリを選択
5. "Deploy Now" をクリック

### 3. 環境変数設定
Railwayのダッシュボードで以下の環境変数を設定：

```
# 病院情報
HOSPITAL_NAME=かよ皮膚科
HOSPITAL_ADDRESS=〒811-2101 福岡県糟屋郡宇美町宇美１丁目9-19
HOSPITAL_PHONE=092-692-7339
HOSPITAL_WEB_URL=https://www5.tandt.co.jp/cti/hs713/index_p.html

# 予約設定
DEFAULT_TIME=09:15
MAX_RETRIES=3
TIMEOUT=30

# Google Calendar（使用する場合）
GOOGLE_CALENDAR_ENABLED=true
GOOGLE_CALENDAR_ID=primary
GOOGLE_CALENDAR_TIMEZONE=Asia/Tokyo

# メール設定（使用する場合）
EMAIL_ENABLED=true
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USE_TLS=true
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM_EMAIL=your-email@gmail.com
EMAIL_FROM_NAME=かよ皮膚科予約管理システム
EMAIL_DEFAULT_RECIPIENT=your-email@gmail.com
```

### 4. アプリケーション設定
Railwayのダッシュボードで：
1. "Settings" タブを開く
2. "Build Command" を設定: `pip install -r requirements.txt`
3. "Start Command" を設定: `python app_deploy.py`

## 🔧 その他のデプロイプラットフォーム

### Render
1. [Render](https://render.com)にログイン
2. "New +" → "Web Service"
3. リポジトリを選択
4. 設定：
   - **Name**: kayo-booking-app
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app_deploy.py`

### Heroku
1. [Heroku](https://heroku.com)にログイン
2. "New" → "Create new app"
3. GitHubと連携してデプロイ
4. 環境変数を設定

## 📋 必要なファイル

- `app_deploy.py` - デプロイ用メインアプリ
- `requirements.txt` - Python依存関係
- `Procfile` - Heroku用設定
- `config/config.json` - 設定ファイル
- `templates/` - HTMLテンプレート
- `static/` - CSS/JSファイル

## 🔐 セキュリティ設定

### メール設定
1. Gmailで2段階認証を有効化
2. アプリパスワードを生成
3. 環境変数に設定

### Google Calendar設定
1. Google Cloud Consoleでプロジェクト作成
2. Calendar APIを有効化
3. 認証情報を作成
4. 認証情報ファイルをアップロード

## 🚨 注意事項

1. **無料プランの制限**
   - 月間実行時間制限あり
   - スリープ機能（一定時間アクセスがないと停止）
   - ストレージ制限

2. **セキュリティ**
   - 機密情報は環境変数で管理
   - 設定ファイルをGitにコミットしない

3. **バックアップ**
   - 定期的にデータベースをバックアップ
   - 設定ファイルのバックアップ

## 📞 サポート

問題が発生した場合は、以下を確認：
1. ログファイルの内容
2. 環境変数の設定
3. 外部サービスの認証情報
4. ネットワーク接続

## 🎯 デプロイ後の確認事項

1. Webアプリが正常に起動しているか
2. 予約フォームが表示されるか
3. データベースが正常に動作するか
4. メール送信機能が動作するか（設定した場合）
5. Google Calendar連携が動作するか（設定した場合）

