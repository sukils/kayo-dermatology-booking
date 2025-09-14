# かよ皮膚科予約管理アプリ デプロイガイド

## 無料デプロイプラットフォーム

### 1. Railway (推奨)
- **無料プラン**: 月500時間まで
- **特徴**: 自動デプロイ、環境変数設定が簡単
- **URL**: https://railway.app

### 2. Render
- **無料プラン**: 月750時間まで
- **特徴**: 自動デプロイ、独自ドメイン対応
- **URL**: https://render.com

### 3. Heroku
- **無料プラン**: 月550時間まで（クレジットカード登録必要）
- **特徴**: スリープ機能あり
- **URL**: https://heroku.com

## Railway でのデプロイ手順

### 1. 準備
1. GitHubアカウントを作成
2. このプロジェクトをGitHubリポジトリにプッシュ
3. Railwayアカウントを作成（GitHubでログイン）

### 2. デプロイ
1. Railwayにログイン
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

## Render でのデプロイ手順

### 1. 準備
1. GitHubアカウントを作成
2. このプロジェクトをGitHubリポジトリにプッシュ
3. Renderアカウントを作成（GitHubでログイン）

### 2. デプロイ
1. Renderにログイン
2. "New +" をクリック
3. "Web Service" を選択
4. リポジトリを選択
5. 以下の設定を入力：
   - **Name**: kayo-booking-app
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app_deploy.py`
6. "Create Web Service" をクリック

### 3. 環境変数設定
Renderのダッシュボードで：
1. "Environment" タブを開く
2. 上記の環境変数を追加

## セキュリティ設定

### 1. メール設定
- Gmailを使用する場合、アプリパスワードを生成
- 2段階認証を有効にする
- アプリパスワードを環境変数に設定

### 2. Google Calendar設定
- Google Cloud Consoleでプロジェクトを作成
- Calendar APIを有効化
- 認証情報を作成
- 認証情報ファイルをアップロード

### 3. データベース
- 本番環境ではPostgreSQLの使用を推奨
- 無料プランではSQLiteを使用

## トラブルシューティング

### 1. ビルドエラー
- `requirements.txt` の依存関係を確認
- Pythonバージョンを確認

### 2. 起動エラー
- 環境変数の設定を確認
- ログを確認

### 3. 機能エラー
- 設定ファイルの内容を確認
- 外部APIの認証情報を確認

## 注意事項

1. **無料プランの制限**
   - 月間実行時間制限
   - スリープ機能（一定時間アクセスがないと停止）
   - ストレージ制限

2. **セキュリティ**
   - 機密情報は環境変数で管理
   - 設定ファイルをGitにコミットしない

3. **バックアップ**
   - 定期的にデータベースをバックアップ
   - 設定ファイルのバックアップ

## サポート

問題が発生した場合は、以下を確認してください：
1. ログファイルの内容
2. 環境変数の設定
3. 外部サービスの認証情報
4. ネットワーク接続
