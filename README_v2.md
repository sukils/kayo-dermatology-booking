# 病院予約自動化プログラム v2

かよ皮膚科のWeb予約システムを自動で操作するPythonプログラムです。
**患者番号のみの入力**に対応した改良版です。

## 主な変更点（v2）

### 🔄 **予約フローの簡素化**
- 患者番号のみの入力で予約可能
- 名前、電話番号、メールアドレスの入力が不要
- より高速で確実な予約処理

### 🎯 **正確な要素検索**
- ページ要素のXPathを設定ファイルで管理
- 複数の候補パターンで要素を検索
- より柔軟で安定した動作

## 機能

- 指定した日時に自動で予約ページにアクセス
- 予約ボタンの自動クリック
- **患者番号の自動入力**
- 予約フォームの自動送信
- スクリーンショットによる実行状況の記録
- ログ機能で実行状況を詳細に記録
- エラーハンドリングとリトライ機能

## 予約フロー

1. **メインページアクセス** → かよ皮膚科のWebサイト
2. **予約ボタンクリック** → 予約システムへ移動
3. **患者番号入力** → 設定された患者番号を自動入力
4. **予約送信** → フォームを自動送信

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

`config_v2.json`を編集して、以下の情報を設定してください：

- **patient_info.patient_number**: 患者番号（必須）
- **booking_times**: 予約を実行する曜日と時間
- **chrome_options**: ブラウザの設定

## 使用方法

### 一度だけ実行

```bash
python hospital_booking_automation_v2.py --once
```

### スケジューラー実行（推奨）

```bash
python hospital_booking_automation_v2.py
```

## 設定項目

### 患者番号設定

```json
"patient_info": {
    "patient_number": "12345"
}
```

**重要**: 実際の患者番号に変更してください。

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

### ページ要素設定

```json
"page_elements": {
    "booking_button": [
        "//a[contains(text(), '予約')]",
        "//button[contains(text(), '予約')]"
    ],
    "patient_number_input": [
        "//input[@name='patient_number']",
        "//input[@placeholder='患者番号']"
    ]
}
```

必要に応じて、実際のページ構造に合わせてXPathを調整してください。

## ログとスクリーンショット

- **ログファイル**: `hospital_booking_v2.log`
- **スクリーンショット**: 実行時の各段階で自動保存
  - `before_booking.png`: 予約開始前
  - `patient_number_form.png`: 患者番号入力画面
  - `after_patient_number_input.png`: 患者番号入力後
  - `after_submit.png`: 送信後
  - `error_screenshot_attempt_X.png`: エラー発生時（試行回数付き）

## ページ分析ツール

実際のページ構造を確認するために、`page_analyzer.py`を使用できます：

```bash
python page_analyzer.py
```

このツールは以下を実行します：
- ページ内のすべてのリンクとボタンの一覧表示
- 予約関連要素の検索
- フォーム要素の詳細分析
- スクリーンショットの取得

## 注意事項

1. **利用規約の確認**: 病院のWeb予約システムの利用規約を必ず確認してください
2. **患者番号の管理**: 設定ファイルに含まれる患者番号は適切に管理してください
3. **ネットワーク環境**: 安定したインターネット接続が必要です
4. **ブラウザ更新**: Chromeブラウザは最新版に更新してください

## トラブルシューティング

### よくある問題

1. **予約ボタンが見つからない**
   - `page_analyzer.py`でページ構造を確認
   - 設定ファイルのXPathを調整

2. **患者番号入力フィールドが見つからない**
   - 実際のページで要素を確認
   - 開発者ツールで要素の属性を確認

3. **ChromeDriverエラー**
   - Chromeブラウザを最新版に更新
   - プログラムを再実行（自動でダウンロードされます）

### ログの確認

エラーが発生した場合は、`hospital_booking_v2.log`ファイルを確認してください。詳細なエラー情報が記録されています。

## カスタマイズ

### 新しい要素パターンの追加

設定ファイルの`page_elements`セクションに新しいXPathパターンを追加できます：

```json
"patient_number_input": [
    "//input[@name='patient_number']",
    "//input[@name='custom_field']",  // 新しいパターン
    "//input[@id='new_id']"           // 新しいパターン
]
```

### 待機時間の調整

```json
"wait_timeout": 30,        // ページ読み込み待機時間
"retry_count": 5           // リトライ回数
```

## ライセンス

このプログラムは個人利用を目的としています。商用利用は禁止されています。

## サポート

問題が発生した場合は、以下の順序で対処してください：

1. ログファイルの確認
2. スクリーンショットの確認
3. `page_analyzer.py`でのページ構造確認
4. 設定ファイルの調整
5. 必要に応じてXPathパターンの追加・修正
