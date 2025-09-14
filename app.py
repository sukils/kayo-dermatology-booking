
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
予約管理アプリ - メインアプリケーション
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

# データベース接続関数
def get_db_connection():
    """データベース接続を取得（環境変数対応）"""
    import os
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Heroku PostgreSQL用
        import psycopg2
        from urllib.parse import urlparse
        result = urlparse(database_url)
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        return conn
    else:
        # ローカル開発用（SQLite）
        import sqlite3
        return sqlite3.connect('database/bookings.db')

# 設定ファイル読み込み
def load_config():
    """設定ファイルを読み込む"""
    try:
        with open('config/config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # デフォルト設定を作成
        default_config = {
            "hospital_info": {
                "name": "かよ皮膚科",
                "address": "東京都...",
                "phone": "03-...",
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
            }
        }
        # 設定ファイルを保存
        os.makedirs('config', exist_ok=True)
        with open('config/config.json', 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        return default_config

# データベース初期化
def init_database():
    """データベースを初期化する"""
    try:
        os.makedirs('database', exist_ok=True)
        conn = get_db_connection()
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

@app.route('/manifest.json')
def manifest():
    """PWAマニフェストファイル"""
    return send_from_directory('static', 'manifest.json')

@app.route('/service-worker.js')
def service_worker():
    """サービスワーカーファイル"""
    return send_from_directory('static/js', 'service-worker.js')

@app.route('/test_notification.html')
def test_notification():
    """通知機能テストページ"""
    try:
        return send_from_directory('.', 'test_notification.html')
    except Exception as e:
        logger.error(f"通知機能テストページ表示エラー: {e}")
        return "エラーが発生しました", 500

@app.route('/test_email.html')
def test_email_page():
    """メール送信機能テストページ"""
    try:
        return send_from_directory('.', 'test_email.html')
    except Exception as e:
        logger.error(f"メール送信機能テストページ表示エラー: {e}")
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
        conn = get_db_connection()
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
        conn = get_db_connection()
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

@app.route('/api/advance-booking', methods=['POST'])
def create_advance_booking():
    """事前予約を作成するAPI"""
    try:
        data = request.get_json()
        logger.info(f"事前予約リクエストを受信: {data}")
        
        # 必須フィールドの確認
        required_fields = ['patient_number', 'birth_date', 'target_booking_date', 'execution_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False, 
                    'message': f'{field}は必須項目です'
                }), 400
        
        patient_number = data['patient_number']
        birth_date = data['birth_date']
        target_booking_date = data['target_booking_date']
        execution_date = data['execution_date']
        booking_time = data.get('booking_time', '09:15')
        
        # 入力値の検証
        if not patient_number.isdigit():
            return jsonify({'success': False, 'message': '患者番号は数字のみ入力してください'}), 400
        
        try:
            datetime.strptime(birth_date, '%Y-%m-%d')
            datetime.strptime(target_booking_date, '%Y-%m-%d')
            datetime.strptime(execution_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'message': '日付の形式が正しくありません'}), 400
        
        # 予約日が今日以降かチェック
        today = datetime.now().date()
        target_date_obj = datetime.strptime(target_booking_date, '%Y-%m-%d').date()
        if target_date_obj < today:
            return jsonify({'success': False, 'message': '予約日は今日以降の日付を選択してください'}), 400
        
        # 実行日が予約日より前かチェック
        execution_date_obj = datetime.strptime(execution_date, '%Y-%m-%d').date()
        if execution_date_obj >= target_date_obj:
            return jsonify({'success': False, 'message': '実行日は予約日より前の日付を設定してください'}), 400
        
        # 事前予約をデータベースに保存
        advance_booking_id = save_advance_booking_to_db({
            'patient_number': patient_number,
            'birth_date': birth_date,
            'target_booking_date': target_booking_date,
            'booking_time': booking_time,
            'execution_date': execution_date,
            'status': 'pending'
        })
        
        if advance_booking_id:
            # Google Calendarに事前予約イベントを作成
            calendar_event_created = False
            calendar_event_id = None
            calendar_message = ""
            
            try:
                # 設定でカレンダー連携が有効になっているかチェック
                with open('config/config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if config.get('google_calendar', {}).get('enabled', False):
                    # Google Calendar連携の初期化
                    from config.google_calendar_config import get_calendar_manager
                    calendar_manager = get_calendar_manager()
                    
                    if not calendar_manager.check_credentials_file():
                        calendar_message = "Google Calendar認証ファイルが見つかりません"
                        logger.warning(f"事前予約のGoogle Calendar認証ファイルエラー: {advance_booking_id}")
                    else:
                        # 事前予約用のカレンダーイベントデータを作成
                        calendar_data = {
                            'patient_number': patient_number,
                            'birth_date': birth_date,
                            'booking_date': target_booking_date,
                            'booking_time': booking_time,
                            'advance_booking_id': advance_booking_id
                        }
                        
                        # Google Calendarにイベントを作成
                        success, result = calendar_manager.create_advance_booking_event(calendar_data)
                        if success:
                            calendar_event_created = True
                            calendar_event_id = result.get('event_id')
                            calendar_message = "Google Calendarにも登録されました"
                            logger.info(f"事前予約のGoogle Calendar登録成功: {advance_booking_id}, event_id: {calendar_event_id}")
                        else:
                            calendar_message = f"Google Calendar登録失敗: {result}"
                            logger.warning(f"事前予約のGoogle Calendar登録失敗: {advance_booking_id}, エラー: {result}")
                else:
                    calendar_message = "Google Calendar連携は無効です"
                    
            except Exception as e:
                calendar_message = f"Google Calendar連携エラー: {str(e)}"
                logger.error(f"事前予約のGoogle Calendar連携エラー: {advance_booking_id}, エラー: {e}")
            
            # メール送信（設定が有効な場合）
            email_message = ""
            if config.get('email', {}).get('enabled', False):
                try:
                    # メール送信先の設定（設定ファイルから取得またはデフォルト）
                    recipient_email = config.get('email', {}).get('default_recipient', None)
                    
                    # 事前予約作成確認メールを送信
                    advance_booking_data = {
                        'patient_number': patient_number,
                        'birth_date': birth_date,
                        'target_booking_date': target_booking_date,
                        'booking_time': booking_time,
                        'execution_date': execution_date
                    }
                    
                    email_success, email_result = email_manager.send_advance_booking_confirmation(
                        advance_booking_data, 
                        recipient_email
                    )
                    
                    if email_success:
                        email_message = "確認メールも送信されました"
                        logger.info(f"事前予約作成確認メールを送信しました: {recipient_email}")
                    else:
                        email_message = f"メール送信に失敗: {email_result}"
                        logger.warning(f"事前予約作成確認メール送信失敗: {email_result}")
                        
                except Exception as e:
                    email_message = f"メール送信エラー: {str(e)}"
                    logger.error(f"事前予約作成確認メール送信エラー: {e}")
            else:
                email_message = "メール送信機能は無効です"
            
            # 事前予約タスクをスケジュールに追加
            schedule_advance_booking_task(advance_booking_id, execution_date)
            
            return jsonify({
                'success': True,
                'message': f'事前予約が作成されました。{calendar_message} {email_message}',
                'advance_booking_id': advance_booking_id,
                'execution_date': execution_date,
                'target_booking_date': target_booking_date,
                'calendar_event_created': calendar_event_created,
                'calendar_event_id': calendar_event_id,
                'email_sent': email_message
            })
        else:
            return jsonify({
                'success': False,
                'message': '事前予約の保存に失敗しました'
            }), 500
            
    except Exception as e:
        logger.error(f"事前予約作成エラー: {e}")
        return jsonify({'success': False, 'message': f'システムエラーが発生しました: {str(e)}'}), 500

@app.route('/api/scheduled-booking', methods=['POST'])
def create_scheduled_booking():
    """スケジュール予約を作成するAPI"""
    try:
        data = request.get_json()
        
        # 必須フィールドの確認
        required_fields = ['patient_number', 'birth_date', 'target_booking_date', 'execution_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False, 
                    'message': f'{field}は必須項目です'
                }), 400
        
        patient_number = data['patient_number']
        birth_date = data['birth_date']
        target_booking_date = data['target_booking_date']
        execution_time = data['execution_time']
        booking_time = data.get('booking_time', '09:15')
        
        # 入力値の検証
        if not patient_number.isdigit():
            return jsonify({'success': False, 'message': '患者番号は数字のみ入力してください'}), 400
        
        try:
            datetime.strptime(birth_date, '%Y-%m-%d')
            datetime.strptime(target_booking_date, '%Y-%m-%d')
            datetime.strptime(execution_time, '%Y-%m-%d %H:%M')
        except ValueError:
            return jsonify({'success': False, 'message': '日付・時刻の形式が正しくありません'}), 400
        
        # 予約日が今日以降かチェック
        today = datetime.now().date()
        target_date_obj = datetime.strptime(target_booking_date, '%Y-%m-%d').date()
        if target_date_obj < today:
            return jsonify({'success': False, 'message': '予約日は今日以降の日付を選択してください'}), 400
        
        # 実行時刻が未来かチェック
        execution_datetime = datetime.strptime(execution_time, '%Y-%m-%d %H:%M')
        if execution_datetime <= datetime.now():
            return jsonify({'success': False, 'message': '実行時刻は現在時刻より後の時刻を設定してください'}), 400
        
        # スケジュール予約をデータベースに保存
        scheduled_booking_id = save_scheduled_booking_to_db({
            'patient_number': patient_number,
            'birth_date': birth_date,
            'target_booking_date': target_booking_date,
            'booking_time': booking_time,
            'execution_time': execution_time,
            'status': 'pending'
        })
        
        if scheduled_booking_id:
            # スケジュールタスクを設定
            schedule_booking_task(scheduled_booking_id, execution_datetime)
            
            return jsonify({
                'success': True,
                'message': 'スケジュール予約が作成されました',
                'scheduled_booking_id': scheduled_booking_id,
                'execution_time': execution_time
            })
        else:
            return jsonify({
                'success': False,
                'message': 'スケジュール予約の保存に失敗しました'
            }), 500
            
    except Exception as e:
        logger.error(f"スケジュール予約作成エラー: {e}")
        return jsonify({'success': False, 'message': f'システムエラーが発生しました: {str(e)}'}), 500

def save_advance_booking_to_db(advance_booking_data):
    """事前予約データをデータベースに保存"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO advance_bookings (patient_number, birth_date, target_booking_date, 
                                        booking_time, execution_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            advance_booking_data['patient_number'],
            advance_booking_data['birth_date'],
            advance_booking_data['target_booking_date'],
            advance_booking_data['booking_time'],
            advance_booking_data['execution_date'],
            advance_booking_data['status']
        ))
        
        # 挿入された事前予約のIDを取得
        advance_booking_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        logger.info(f"事前予約データをデータベースに保存しました: ID={advance_booking_id}")
        
        return advance_booking_id
        
    except Exception as e:
        logger.error(f"事前予約データベース保存エラー: {e}")
        return None

def save_scheduled_booking_to_db(scheduled_booking_data):
    """スケジュール予約データをデータベースに保存"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO scheduled_bookings (patient_number, birth_date, target_booking_date, 
                                          booking_time, execution_time, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            scheduled_booking_data['patient_number'],
            scheduled_booking_data['birth_date'],
            scheduled_booking_data['target_booking_date'],
            scheduled_booking_data['booking_time'],
            scheduled_booking_data['execution_time'],
            scheduled_booking_data['status']
        ))
        
        # 挿入されたスケジュール予約のIDを取得
        scheduled_booking_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        logger.info(f"スケジュール予約データをデータベースに保存しました: ID={scheduled_booking_id}")
        
        return scheduled_booking_id
        
    except Exception as e:
        logger.error(f"スケジュール予約データベース保存エラー: {e}")
        return None

def schedule_advance_booking_task(advance_booking_id, execution_date):
    """事前予約タスクをスケジュールに追加"""
    try:
        # 既存のスケジュールライブラリを使用
        import schedule
        import threading
        import time
        
        def execute_advance_booking():
            """事前予約を実行"""
            try:
                # 事前予約データを取得
                conn = get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM advance_bookings WHERE id = ?
                ''', (advance_booking_id,))
                
                advance_booking = cursor.fetchone()
                conn.close()
                
                if not advance_booking:
                    logger.error(f"事前予約が見つかりません: {advance_booking_id}")
                    return
                
                # カラム名を取得
                columns = ['id', 'patient_number', 'birth_date', 'target_booking_date', 
                          'booking_time', 'status', 'message', 'execution_date', 
                          'created_at', 'updated_at']
                advance_booking_dict = dict(zip(columns, advance_booking))
                
                # 予約を実行
                automation = HospitalBookingAutomationV3()
                automation.config['patient_info']['patient_number'] = advance_booking_dict['patient_number']
                automation.config['patient_info']['birth_date'] = advance_booking_dict['birth_date']
                
                result = automation.execute_lightweight_booking()
                
                # 結果を更新
                update_advance_booking_status(advance_booking_id, 'completed' if result else 'failed')
                
                if result:
                    logger.info(f"事前予約が完了しました: {advance_booking_id}")
                else:
                    logger.warning(f"事前予約が失敗しました: {advance_booking_id}")
                    
            except Exception as e:
                logger.error(f"事前予約実行エラー: {e}")
                update_advance_booking_status(advance_booking_id, 'failed', str(e))
        
        # 実行日時を設定（指定日の09:00に実行）
        execution_datetime = datetime.strptime(execution_date, '%Y-%m-%d').replace(hour=9, minute=0)
        
        # スケジュールを設定
        schedule.every().day.at(execution_datetime.strftime('%H:%M')).do(execute_advance_booking)
        
        # バックグラウンドでスケジューラーを実行
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1分ごとにチェック
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info(f"事前予約タスクを設定しました: ID={advance_booking_id}, 実行日={execution_date}")
        
    except Exception as e:
        logger.error(f"事前予約タスク設定エラー: {e}")

def schedule_booking_task(scheduled_booking_id, execution_datetime):
    """予約タスクをスケジュールに追加"""
    try:
        # 既存のスケジュールライブラリを使用
        import schedule
        import threading
        import time
        
        def execute_scheduled_booking():
            """スケジュールされた予約を実行"""
            try:
                # スケジュール予約データを取得
                conn = get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM scheduled_bookings WHERE id = ?
                ''', (scheduled_booking_id,))
                
                scheduled_booking = cursor.fetchone()
                conn.close()
                
                if not scheduled_booking:
                    logger.error(f"スケジュール予約が見つかりません: {scheduled_booking_id}")
                    return
                
                # カラム名を取得
                columns = ['id', 'patient_number', 'birth_date', 'target_booking_date', 
                          'booking_time', 'execution_time', 'status', 'message', 
                          'created_at', 'updated_at']
                scheduled_booking_dict = dict(zip(columns, scheduled_booking))
                
                # 予約を実行
                automation = HospitalBookingAutomationV3()
                automation.config['patient_info']['patient_number'] = scheduled_booking_dict['patient_number']
                automation.config['patient_info']['birth_date'] = scheduled_booking_dict['birth_date']
                
                result = automation.execute_lightweight_booking()
                
                # 結果を更新
                update_scheduled_booking_status(scheduled_booking_id, 'completed' if result else 'failed')
                
                if result:
                    logger.info(f"スケジュール予約が完了しました: {scheduled_booking_id}")
                else:
                    logger.warning(f"スケジュール予約が失敗しました: {scheduled_booking_id}")
                    
            except Exception as e:
                logger.error(f"スケジュール予約実行エラー: {e}")
                update_scheduled_booking_status(scheduled_booking_id, 'failed', str(e))
        
        # スケジュールを設定
        schedule.every().day.at(execution_datetime.strftime('%H:%M')).do(execute_scheduled_booking)
        
        # バックグラウンドでスケジューラーを実行
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1分ごとにチェック
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info(f"スケジュール予約タスクを設定しました: ID={scheduled_booking_id}, 実行時刻={execution_datetime}")
        
    except Exception as e:
        logger.error(f"スケジュールタスク設定エラー: {e}")

def update_advance_booking_status(advance_booking_id, status, message=None):
    """事前予約のステータスを更新"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if message:
            cursor.execute('''
                UPDATE advance_bookings 
                SET status = ?, message = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, message, advance_booking_id))
        else:
            cursor.execute('''
                UPDATE advance_bookings 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, advance_booking_id))
        
        conn.commit()
        conn.close()
        logger.info(f"事前予約ステータスを更新しました: ID={advance_booking_id}, status={status}")
        
    except Exception as e:
        logger.error(f"事前予約ステータス更新エラー: {e}")

def update_scheduled_booking_status(scheduled_booking_id, status, message=None):
    """スケジュール予約のステータスを更新"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if message:
            cursor.execute('''
                UPDATE scheduled_bookings 
                SET status = ?, message = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, message, scheduled_booking_id))
        else:
            cursor.execute('''
                UPDATE scheduled_bookings 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, scheduled_booking_id))
        
        conn.commit()
        conn.close()
        logger.info(f"スケジュール予約ステータスを更新しました: ID={scheduled_booking_id}, status={status}")
        
    except Exception as e:
        logger.error(f"スケジュール予約ステータス更新エラー: {e}")

@app.route('/advance')
def advance_booking():
    """事前予約ページ"""
    try:
        return render_template('advance.html')
    except Exception as e:
        logger.error(f"事前予約ページエラー: {e}")
        return "エラーが発生しました", 500

@app.route('/scheduled')
def scheduled_booking():
    """スケジュール予約ページ"""
    try:
        return render_template('scheduled.html')
    except Exception as e:
        logger.error(f"スケジュール予約ページエラー: {e}")
        return "エラーが発生しました", 500

@app.route('/api/advance-bookings')
def get_advance_bookings():
    """事前予約一覧を取得するAPI"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM advance_bookings ORDER BY execution_date ASC
        ''')
        
        advance_bookings = cursor.fetchall()
        conn.close()
        
        # カラム名を取得
        columns = ['id', 'patient_number', 'birth_date', 'target_booking_date', 
                  'booking_time', 'status', 'message', 'execution_date', 
                  'created_at', 'updated_at']
        
        # 辞書形式に変換
        advance_booking_list = []
        for booking in advance_bookings:
            booking_dict = dict(zip(columns, booking))
            advance_booking_list.append(booking_dict)
        
        return jsonify({
            'success': True,
            'advance_bookings': advance_booking_list,
            'total': len(advance_booking_list)
        })
        
    except Exception as e:
        logger.error(f"事前予約一覧取得エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

@app.route('/api/scheduled-bookings')
def get_scheduled_bookings():
    """スケジュール予約一覧を取得するAPI"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM scheduled_bookings ORDER BY execution_time ASC
        ''')
        
        scheduled_bookings = cursor.fetchall()
        conn.close()
        
        # カラム名を取得
        columns = ['id', 'patient_number', 'birth_date', 'target_booking_date', 
                  'booking_time', 'execution_time', 'status', 'message', 
                  'created_at', 'updated_at']
        
        # 辞書形式に変換
        scheduled_booking_list = []
        for booking in scheduled_bookings:
            booking_dict = dict(zip(columns, booking))
            scheduled_booking_list.append(booking_dict)
        
        return jsonify({
            'success': True,
            'scheduled_bookings': scheduled_booking_list,
            'total': len(scheduled_booking_list)
        })
        
    except Exception as e:
        logger.error(f"スケジュール予約一覧取得エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

@app.route('/api/calendar-status')
def get_calendar_status():
    """Google Calendar連携の状況を取得するAPI"""
    try:
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        calendar_enabled = config.get('google_calendar', {}).get('enabled', False)
        
        return jsonify({
            'success': True,
            'enabled': calendar_enabled,
            'message': 'Google Calendar連携が有効です' if calendar_enabled else 'Google Calendar連携は無効です'
        })
        
    except Exception as e:
        logger.error(f"カレンダー状況取得エラー: {e}")
        return jsonify({
            'success': False,
            'enabled': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

@app.route('/api/email-status')
def get_email_status():
    """メール送信機能の状況を取得するAPI"""
    try:
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        email_enabled = config.get('email', {}).get('enabled', False)
        email_config = config.get('email', {})
        
        return jsonify({
            'success': True,
            'enabled': email_enabled,
            'smtp_server': email_config.get('smtp_server', ''),
            'smtp_port': email_config.get('smtp_port', ''),
            'from_email': email_config.get('from_email', ''),
            'default_recipient': email_config.get('default_recipient', ''),
            'message': 'メール送信機能が有効です' if email_enabled else 'メール送信機能は無効です'
        })
        
    except Exception as e:
        logger.error(f"メール状況取得エラー: {e}")
        return jsonify({
            'success': False,
            'enabled': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

@app.route('/api/test-email', methods=['POST'])
def test_email():
    """テストメールを送信するAPI"""
    try:
        data = request.get_json()
        recipient_email = data.get('recipient_email')
        
        if not recipient_email:
            return jsonify({
                'success': False,
                'message': '送信先メールアドレスが必要です'
            }), 400
        
        # テスト用の予約データ
        test_booking_data = {
            'id': 99999,
            'patient_number': '123456',
            'birth_date': '1990-01-01',
            'booking_date': '2025-08-30',
            'status': 'success',
            'message': 'テスト用の予約です'
        }
        
        # テストメールを送信
        email_success, email_result = email_manager.send_booking_confirmation(
            test_booking_data, 
            recipient_email
        )
        
        if email_success:
            return jsonify({
                'success': True,
                'message': 'テストメールが送信されました',
                'recipient': recipient_email
            })
        else:
            return jsonify({
                'success': False,
                'message': f'テストメール送信に失敗: {email_result}'
            }), 500
            
    except Exception as e:
        logger.error(f"テストメール送信エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

@app.route('/api/push-subscription', methods=['POST'])
def save_push_subscription():
    """プッシュ通知の購読情報を保存するAPI"""
    try:
        data = request.get_json()
        logger.info(f"プッシュ通知購読情報を受信: {data}")
        
        # 購読情報をデータベースに保存（簡易版）
        # 実際の実装では、より詳細な管理が必要
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # プッシュ通知テーブルの作成（存在しない場合）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                p256dh TEXT,
                auth TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 購読情報を保存
        cursor.execute('''
            INSERT INTO push_subscriptions (endpoint, p256dh, auth)
            VALUES (?, ?, ?)
        ''', (
            data.get('endpoint', ''),
            data.get('keys', {}).get('p256dh', ''),
            data.get('keys', {}).get('auth', '')
        ))
        
        conn.commit()
        conn.close()
        
        logger.info("プッシュ通知購読情報を保存しました")
        
        return jsonify({
            'success': True,
            'message': 'プッシュ通知の設定が完了しました'
        })
        
    except Exception as e:
        logger.error(f"プッシュ通知購読情報保存エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

@app.route('/api/send-notification', methods=['POST'])
def send_notification():
    """プッシュ通知を送信するAPI"""
    try:
        data = request.get_json()
        title = data.get('title', 'かよ皮膚科予約管理')
        body = data.get('body', '新しい通知があります')
        
        # プッシュ通知の送信処理
        # 実際の実装では、web-pushライブラリを使用してプッシュ通知を送信
        logger.info(f"プッシュ通知送信: {title} - {body}")
        
        return jsonify({
            'success': True,
            'message': '通知を送信しました'
        })
        
    except Exception as e:
        logger.error(f"プッシュ通知送信エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

@app.route('/api/advance-bookings/<int:booking_id>', methods=['DELETE'])
def delete_advance_booking(booking_id):
    """事前予約を削除するAPI"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 予約の存在確認
        cursor.execute('SELECT * FROM advance_bookings WHERE id = ?', (booking_id,))
        advance_booking = cursor.fetchone()
        
        if not advance_booking:
            return jsonify({
                'success': False,
                'message': '事前予約が見つかりません'
            }), 404
        
        # 事前予約を削除
        cursor.execute('DELETE FROM advance_bookings WHERE id = ?', (booking_id,))
        
        conn.commit()
        conn.close()
        
        # Google Calendarのイベントも削除を試行
        calendar_message = ""
        try:
            # 設定でカレンダー連携が有効になっているかチェック
            with open('config/config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if config.get('google_calendar', {}).get('enabled', False):
                # 事前予約に関連するカレンダーイベントを検索して削除
                # 注: 事前予約の場合は、advance_booking_idでイベントを特定する必要があります
                # ここでは、患者番号と予約日でイベントを検索して削除を試行
                patient_number = advance_booking[1]  # 患者番号
                target_booking_date = advance_booking[3]  # 予約希望日
                
                # カレンダーから該当するイベントを検索して削除
                success, events = calendar_manager.get_calendar_events()
                if success:
                    for event in events:
                        # イベントの説明から患者番号と予約日を確認
                        description = event.get('description', '')
                        if (f'患者番号: {patient_number}' in description and 
                            target_booking_date in event.get('start', {}).get('dateTime', '')):
                            # イベントを削除
                            delete_success, delete_result = calendar_manager.delete_booking_event(event['id'])
                            if delete_success:
                                calendar_message = "Google Calendarのイベントも削除されました"
                                logger.info(f"事前予約削除時にGoogle Calendarイベントも削除: {event['id']}")
                            else:
                                calendar_message = f"Google Calendarイベント削除失敗: {delete_result}"
                                logger.warning(f"事前予約削除時のGoogle Calendarイベント削除失敗: {delete_result}")
                            break
                else:
                    calendar_message = "Google Calendarイベント検索失敗"
            else:
                calendar_message = "Google Calendar連携は無効です"
                
        except Exception as e:
            calendar_message = f"Google Calendar連携エラー: {str(e)}"
            logger.error(f"事前予約削除時のGoogle Calendar連携エラー: {e}")
        
        return jsonify({
            'success': True,
            'message': f'事前予約を削除しました。{calendar_message}'
        })
        
    except Exception as e:
        logger.error(f"事前予約削除エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

@app.route('/api/scheduled-bookings/<int:booking_id>', methods=['DELETE'])
def delete_scheduled_booking(booking_id):
    """スケジュール予約を削除するAPI"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 予約の存在確認
        cursor.execute('SELECT * FROM scheduled_bookings WHERE id = ?', (booking_id,))
        scheduled_booking = cursor.fetchone()
        
        if not scheduled_booking:
            return jsonify({
                'success': False,
                'message': 'スケジュール予約が見つかりません'
            }), 404
        
        # スケジュール予約を削除
        cursor.execute('DELETE FROM scheduled_bookings WHERE id = ?', (booking_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'スケジュール予約を削除しました'
        })
        
    except Exception as e:
        logger.error(f"スケジュール予約削除エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

@app.route('/history')
def booking_history():
    """予約履歴ページ"""
    try:
        conn = get_db_connection()
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
        
        conn = get_db_connection()
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

@app.route('/api/bookings/<int:booking_id>')
def get_booking_detail(booking_id):
    """特定の予約詳細を取得するAPI"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM bookings WHERE id = ?
        ''', (booking_id,))
        
        booking = cursor.fetchone()
        conn.close()
        
        if not booking:
            return jsonify({
                'success': False,
                'message': '予約が見つかりません'
            }), 404
        
        # カラム名を取得
        columns = ['id', 'patient_number', 'birth_date', 'booking_date', 'status', 
                  'message', 'google_calendar_event_id', 'google_calendar_link', 
                  'created_at', 'updated_at']
        
        # 辞書形式に変換
        booking_dict = dict(zip(columns, booking))
        
        return jsonify({
            'success': True,
            'booking': booking_dict
        })
        
    except Exception as e:
        logger.error(f"予約詳細取得エラー: {e}")
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    """予約を削除するAPI"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 予約の存在確認
        cursor.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,))
        booking = cursor.fetchone()
        
        if not booking:
            return jsonify({
                'success': False,
                'message': '予約が見つかりません'
            }), 404
        
        # Google CalendarイベントIDを取得
        cursor.execute('''
            SELECT google_calendar_event_id FROM bookings WHERE id = ?
        ''', (booking_id,))
        result = cursor.fetchone()
        event_id = result[0] if result else None
        
        # 予約を削除
        cursor.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
        
        # 履歴テーブルに削除記録を追加
        cursor.execute('''
            INSERT INTO booking_history (booking_id, action, details)
            VALUES (?, ?, ?)
        ''', (booking_id, 'delete', '予約が削除されました'))
        
        conn.commit()
        conn.close()
        
        # Google Calendarからも削除（イベントIDがある場合）
        if event_id:
            try:
                from config.google_calendar_config import get_calendar_manager
                calendar_manager = get_calendar_manager()
                calendar_manager.delete_booking_event(event_id)
                logger.info(f"Google Calendarからイベントを削除しました: {event_id}")
            except Exception as e:
                logger.warning(f"Google Calendarからの削除に失敗: {e}")
        
        return jsonify({
            'success': True,
            'message': '予約を削除しました'
        })
        
    except Exception as e:
        logger.error(f"予約削除エラー: {e}")
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
    # 本番環境では環境変数からポートを取得
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
