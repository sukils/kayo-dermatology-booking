#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
予約管理アプリ - デプロイ用メインアプリケーション
かよ皮膚科の予約を簡単に行い、Googleカレンダーに自動登録するWebアプリ
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from flask_mail import Mail
import json
import logging
import os
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

# 既存の予約プログラムをインポート
import sys
sys.path.append('..')
from hospital_booking_automation_v3 import HospitalBookingAutomationV3

app = Flask(__name__)

# メール送信機能の初期化
from config.email_config import get_email_manager
email_manager = get_email_manager(app)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 設定ファイル読み込み（環境変数対応）
def load_config():
    """設定ファイルを読み込む（環境変数対応）"""
    try:
        # 環境変数から設定を読み込み
        config = {
            "hospital_info": {
                "name": os.getenv('HOSPITAL_NAME', 'かよ皮膚科'),
                "address": os.getenv('HOSPITAL_ADDRESS', '〒811-2101 福岡県糟屋郡宇美町宇美１丁目9-19'),
                "phone": os.getenv('HOSPITAL_PHONE', '092-692-7339'),
                "web_url": os.getenv('HOSPITAL_WEB_URL', 'https://www5.tandt.co.jp/cti/hs713/index_p.html')
            },
            "booking_settings": {
                "default_time": os.getenv('DEFAULT_TIME', '09:15'),
                "max_retries": int(os.getenv('MAX_RETRIES', '3')),
                "timeout": int(os.getenv('TIMEOUT', '30'))
            },
            "google_calendar": {
                "enabled": os.getenv('GOOGLE_CALENDAR_ENABLED', 'false').lower() == 'true',
                "calendar_id": os.getenv('GOOGLE_CALENDAR_ID', 'primary'),
                "timezone": os.getenv('GOOGLE_CALENDAR_TIMEZONE', 'Asia/Tokyo')
            },
            "email": {
                "enabled": os.getenv('EMAIL_ENABLED', 'false').lower() == 'true',
                "smtp_server": os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
                "smtp_port": int(os.getenv('EMAIL_SMTP_PORT', '587')),
                "use_tls": os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true',
                "username": os.getenv('EMAIL_USERNAME', ''),
                "password": os.getenv('EMAIL_PASSWORD', ''),
                "from_email": os.getenv('EMAIL_FROM_EMAIL', ''),
                "from_name": os.getenv('EMAIL_FROM_NAME', 'かよ皮膚科予約管理システム'),
                "default_recipient": os.getenv('EMAIL_DEFAULT_RECIPIENT', '')
            }
        }
        
        # 設定ファイルが存在する場合は上書き
        if os.path.exists('config/config.json'):
            with open('config/config.json', 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                # ファイルの設定で環境変数を上書き
                for section, values in file_config.items():
                    if section in config:
                        config[section].update(values)
        
        return config
        
    except Exception as e:
        logger.error(f"設定読み込みエラー: {e}")
        # デフォルト設定を返す
        return {
            "hospital_info": {
                "name": "かよ皮膚科",
                "address": "〒811-2101 福岡県糟屋郡宇美町宇美１丁目9-19",
                "phone": "092-692-7339",
                "web_url": "https://www5.tandt.co.jp/cti/hs713/index_p.html"
            },
            "booking_settings": {
                "default_time": "09:15",
                "max_retries": 3,
                "timeout": 30
            },
            "google_calendar": {
                "enabled": False,
                "calendar_id": "primary",
                "timezone": "Asia/Tokyo"
            },
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "use_tls": True,
                "username": "",
                "password": "",
                "from_email": "",
                "from_name": "かよ皮膚科予約管理システム",
                "default_recipient": ""
            }
        }

# データベース初期化
def init_database():
    """データベースを初期化する"""
    try:
        os.makedirs('database', exist_ok=True)
        conn = sqlite3.connect('database/bookings.db')
        cursor = conn.cursor()
        
        # 予約テーブルの作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_number TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                booking_date TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                google_calendar_event_id TEXT,
                google_calendar_link TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 予約履歴テーブルの作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS booking_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (booking_id) REFERENCES bookings (id)
            )
        ''')
        
        # スケジュール予約テーブルの作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_number TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                target_booking_date TEXT NOT NULL,
                booking_time TEXT NOT NULL,
                execution_time TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 事前予約テーブルの作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS advance_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_number TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                target_booking_date TEXT NOT NULL,
                booking_time TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                execution_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("データベースの初期化が完了しました")
        
    except Exception as e:
        logger.error(f"データベース初期化エラー: {e}")

@app.route('/')
def index():
    """メインページ"""
    try:
        config = load_config()
        return render_template('index.html', config=config)
    except Exception as e:
        logger.error(f"メインページエラー: {e}")
        return "エラーが発生しました", 500

@app.route('/booking')
def booking_form():
    """予約フォームページ"""
    try:
        return render_template('booking.html')
    except Exception as e:
        logger.error(f"予約フォームエラー: {e}")
        return "エラーが発生しました", 500

@app.route('/api/booking', methods=['POST'])
def create_booking():
    """予約を作成するAPI"""
    try:
        data = request.get_json()
        logger.info(f"予約リクエストを受信: {data}")
        
        # 必須フィールドの確認
        required_fields = ['patient_number', 'birth_date', 'booking_date']
        for field in required_fields:
            if not data.get(field):
                logger.warning(f"必須フィールドが不足: {field}")
                return jsonify({
                    'success': False, 
                    'message': f'{field}は必須項目です'
                }), 400
        
        patient_number = data['patient_number']
        birth_date = data['birth_date']
        booking_date = data['booking_date']
        booking_time = data.get('booking_time', '09:15')
        
        logger.info(f"受信したデータ: patient_number={patient_number}, birth_date={birth_date}, booking_date={booking_date}, booking_time={booking_time}")
        
        # 入力値の検証
        if not patient_number.isdigit():
            logger.warning(f"患者番号が数字でない: {patient_number}")
            return jsonify({'success': False, 'message': '患者番号は数字のみ入力してください'}), 400
        
        try:
            datetime.strptime(birth_date, '%Y-%m-%d')
            datetime.strptime(booking_date, '%Y-%m-%d')
            logger.info("日付形式の検証が完了")
        except ValueError as e:
            logger.warning(f"日付形式エラー: birth_date={birth_date}, booking_date={booking_date}, error={e}")
            return jsonify({'success': False, 'message': '日付の形式が正しくありません'}), 400
        
        # 予約日が今日以降かチェック
        today = datetime.now().date()
        booking_date_obj = datetime.strptime(booking_date, '%Y-%m-%d').date()
        if booking_date_obj < today:
            logger.warning(f"予約日が過去: booking_date={booking_date}, today={today}")
            return jsonify({'success': False, 'message': '予約日は今日以降の日付を選択してください'}), 400
        
        logger.info("入力値の検証が完了、予約処理を開始")
        
        # 既存の予約プログラムを実行
        try:
            automation = HospitalBookingAutomationV3()
            
            # 設定ファイルを更新
            automation.config['patient_info']['patient_number'] = patient_number
            automation.config['patient_info']['birth_date'] = birth_date
            
            # 軽量版の予約を実行
            result = automation.execute_lightweight_booking()
            
        except ImportError as e:
            logger.error(f"予約プログラムのインポートエラー: {e}")
            return jsonify({
                'success': False, 
                'message': '予約システムの初期化に失敗しました。システム管理者に連絡してください。'
            }), 500
            
        except Exception as e:
            logger.error(f"予約プログラム実行エラー: {e}")
            # 失敗時の処理
            booking_data = {
                'patient_number': patient_number,
                'birth_date': birth_date,
                'booking_date': booking_date,
                'status': 'failed',
                'message': f'予約システムエラー: {str(e)}'
            }
            
            # データベースに保存
            save_booking_to_db(booking_data)
            
            return jsonify({
                'success': False,
                'message': '予約システムでエラーが発生しました。しばらく時間をおいて再度お試しください。',
                'error_details': str(e),
                'booking_data': booking_data
            }), 500
        
        if result:
            # 成功時の処理
            booking_data = {
                'patient_number': patient_number,
                'birth_date': birth_date,
                'booking_date': booking_date,
                'status': 'success',
                'message': '予約が完了しました'
            }
            
            # データベースに保存
            booking_id = save_booking_to_db(booking_data)
            
            # Googleカレンダーに登録（設定が有効な場合）
            config = load_config()
            if config['google_calendar']['enabled']:
                try:
                    calendar_result = add_to_google_calendar(booking_data)
                    if calendar_result[0]:  # 成功
                        logger.info(f"Googleカレンダーへの登録が完了しました: {booking_id}")
                    else:
                        logger.warning(f"Googleカレンダーへの登録に失敗: {calendar_result[1]}")
                except Exception as e:
                    logger.error(f"Googleカレンダー登録エラー: {e}")
            
            # メール送信（設定が有効な場合）
            email_message = ""
            if config.get('email', {}).get('enabled', False):
                try:
                    # メール送信先の設定（設定ファイルから取得またはデフォルト）
                    recipient_email = config.get('email', {}).get('default_recipient', None)
                    
                    # 予約完了確認メールを送信
                    email_success, email_result = email_manager.send_booking_confirmation(
                        {'id': booking_id, **booking_data}, 
                        recipient_email
                    )
                    
                    if email_success:
                        email_message = "確認メールも送信されました"
                        logger.info(f"予約完了確認メールを送信しました: {recipient_email}")
                    else:
                        email_message = f"メール送信に失敗: {email_result}"
                        logger.warning(f"予約完了確認メール送信失敗: {email_result}")
                        
                except Exception as e:
                    email_message = f"メール送信エラー: {str(e)}"
                    logger.error(f"予約完了確認メール送信エラー: {e}")
            else:
                email_message = "メール送信機能は無効です"
            
            return jsonify({
                'success': True,
                'message': '予約が完了しました！',
                'booking_data': booking_data,
                'booking_id': booking_id,
                'details': f'予約番号: {booking_id}\n患者番号: {patient_number}\n誕生日: {birth_date}\n予約日: {booking_date}\n予約時間: {booking_time}',
                'email_sent': email_message
            })
        else:
            # 失敗時の処理
            booking_data = {
                'patient_number': patient_number,
                'birth_date': birth_date,
                'booking_date': booking_date,
                'status': 'failed',
                'message': '予約に失敗しました。受付時間外または満員の可能性があります。'
            }
            
            # データベースに保存
            save_booking_to_db(booking_data)
            
            return jsonify({
                'success': False,
                'message': '予約に失敗しました。受付時間外または満員の可能性があります。再度お試しください。',
                'booking_data': booking_data
            }), 500
            
    except Exception as e:
        logger.error(f"予約実行エラー: {e}")
        return jsonify({'success': False, 'message': f'システムエラーが発生しました: {str(e)}'}), 500

def save_booking_to_db(booking_data):
    """予約データをデータベースに保存"""
    try:
        conn = sqlite3.connect('database/bookings.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bookings (patient_number, birth_date, booking_date, status, message)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            booking_data['patient_number'],
            booking_data['birth_date'],
            booking_data['booking_date'],
            booking_data['status'],
            booking_data['message']
        ))
        
        # 挿入された予約のIDを取得
        booking_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        logger.info(f"予約データをデータベースに保存しました: ID={booking_id}, {booking_data}")
        
        return booking_id
        
    except Exception as e:
        logger.error(f"データベース保存エラー: {e}")
        return None

def add_to_google_calendar(booking_data):
    """Googleカレンダーに予約を追加"""
    try:
        # Google Calendar Managerを取得
        from config.google_calendar_config import get_calendar_manager
        calendar_manager = get_calendar_manager()
        
        # 認証情報ファイルの確認
        if not calendar_manager.check_credentials_file():
            logger.warning("Google Calendar API認証情報ファイルが見つかりません")
            return False, "認証情報ファイルが設定されていません"
        
        # イベントを作成
        success, result = calendar_manager.create_booking_event(booking_data)
        
        if success:
            logger.info(f"Googleカレンダーに予約を追加しました: {result}")
            
            # データベースにイベントIDを保存
            update_booking_with_event_id(booking_data.get('id'), result['event_id'], result.get('html_link'))
            
            return True, result
        else:
            logger.error(f"Googleカレンダーへの予約追加に失敗: {result}")
            return False, result
            
    except Exception as e:
        logger.error(f"Googleカレンダー追加エラー: {e}")
        return False, f"カレンダー追加エラー: {e}"

def update_booking_with_event_id(booking_id, event_id, calendar_link=None):
    """予約データにGoogle CalendarのイベントIDを更新"""
    try:
        conn = sqlite3.connect('database/bookings.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE bookings 
            SET google_calendar_event_id = ?, 
                google_calendar_link = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (event_id, calendar_link, booking_id))
        
        conn.commit()
        conn.close()
        logger.info(f"予約データを更新しました: booking_id={booking_id}, event_id={event_id}")
        
    except Exception as e:
        logger.error(f"データベース更新エラー: {e}")

@app.route('/history')
def booking_history():
    """予約履歴ページ"""
    try:
        conn = sqlite3.connect('database/bookings.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM bookings ORDER BY created_at DESC LIMIT 50
        ''')
        
        bookings = cursor.fetchall()
        conn.close()
        
        return render_template('history.html', bookings=bookings)
        
    except Exception as e:
        logger.error(f"予約履歴取得エラー: {e}")
        return "エラーが発生しました", 500

@app.route('/api/bookings')
def get_bookings():
    """予約一覧を取得するAPI"""
    try:
        # クエリパラメータの取得
        status_filter = request.args.get('status')
        date_filter = request.args.get('date')
        
        conn = sqlite3.connect('database/bookings.db')
        cursor = conn.cursor()
        
        # 基本クエリ
        query = '''
            SELECT * FROM bookings 
            WHERE 1=1
        '''
        params = []
        
        # ステータスフィルター
        if status_filter:
            query += ' AND status = ?'
            params.append(status_filter)
        
        # 日付フィルター
        if date_filter:
            query += ' AND DATE(booking_date) = ?'
            params.append(date_filter)
        
        query += ' ORDER BY created_at DESC LIMIT 100'
        
        cursor.execute(query, params)
        bookings = cursor.fetchall()
        conn.close()
        
        # カラム名を取得
        columns = ['id', 'patient_number', 'birth_date', 'booking_date', 'status', 
                  'message', 'google_calendar_event_id', 'google_calendar_link', 
                  'created_at', 'updated_at']
        
        # 辞書形式に変換
        booking_list = []
        for booking in bookings:
            booking_dict = dict(zip(columns, booking))
            booking_list.append(booking_dict)
        
        return jsonify({
            'success': True,
            'bookings': booking_list,
            'total': len(booking_list)
        })
        
    except Exception as e:
        logger.error(f"予約一覧取得エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

if __name__ == '__main__':
    # 必要なフォルダを作成
    os.makedirs('logs', exist_ok=True)
    os.makedirs('database', exist_ok=True)
    os.makedirs('config', exist_ok=True)
    
    # データベース初期化
    init_database()
    
    # アプリケーション起動
    logger.info("予約管理アプリを起動します")
    
    # ポート設定（環境変数から取得、デフォルトは5000）
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
