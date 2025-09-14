#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Calendar API設定と認証処理
かよ皮膚科予約管理システム用
"""

import os
import json
import logging
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Google Calendar APIのスコープ
SCOPES = ['https://www.googleapis.com/auth/calendar']

# 認証情報ファイルのパス
CREDENTIALS_FILE = 'config/credentials.json'
TOKEN_FILE = 'config/token.json'

class GoogleCalendarManager:
    """Google Calendar APIの管理クラス"""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        
    def authenticate(self):
        """Google Calendar APIの認証を行う"""
        try:
            # 既存のトークンがあるかチェック
            if os.path.exists(TOKEN_FILE):
                self.credentials = Credentials.from_authorized_user_file(
                    TOKEN_FILE, SCOPES
                )
                
            # トークンが無効または期限切れの場合
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    # 新しい認証フローを開始
                    if not os.path.exists(CREDENTIALS_FILE):
                        logger.error(f"認証情報ファイルが見つかりません: {CREDENTIALS_FILE}")
                        return False
                        
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CREDENTIALS_FILE, SCOPES
                    )
                    self.credentials = flow.run_local_server(port=0)
                
                # トークンを保存
                with open(TOKEN_FILE, 'w') as token:
                    token.write(self.credentials.to_json())
            
            # Calendar APIサービスを構築
            self.service = build('calendar', 'v3', credentials=self.credentials)
            logger.info("Google Calendar APIの認証が完了しました")
            return True
            
        except Exception as e:
            logger.error(f"Google Calendar API認証エラー: {e}")
            return False
    
    def create_booking_event(self, booking_data):
        """予約イベントをGoogleカレンダーに作成"""
        try:
            if not self.service:
                if not self.authenticate():
                    return False, "認証に失敗しました"
            
            # イベントの開始時刻を設定
            event_date = datetime.strptime(booking_data['booking_date'], '%Y-%m-%d')
            start_time = datetime.combine(event_date, datetime.strptime('09:15', '%H:%M').time())
            end_time = start_time + timedelta(hours=1)  # 1時間の診察時間
            
            # イベントの詳細
            event = {
                'summary': f'🏥 かよ皮膚科 診察予約',
                'description': f"""
患者番号: {booking_data['patient_number']}
誕生日: {booking_data['birth_date']}
予約日時: {start_time.strftime('%Y年%m月%d日 %H:%M')}
                
※ 受付時間: 9:15開始
※ 診察時間: 約1時間
※ 予約管理システムから自動登録
                """.strip(),
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'location': 'かよ皮膚科',
                'colorId': '1',  # 青色
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 60},  # 1時間前
                        {'method': 'popup', 'minutes': 15},  # 15分前
                    ],
                },
                'extendedProperties': {
                    'private': {
                        'patient_number': booking_data['patient_number'],
                        'birth_date': booking_data['birth_date'],
                        'booking_id': str(booking_data.get('id', '')),
                        'source': 'かよ皮膚科予約管理システム'
                    }
                }
            }
            
            # イベントを作成
            event_result = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            logger.info(f"Googleカレンダーにイベントを作成しました: {event_result['id']}")
            
            # 作成されたイベントの情報を返す
            return True, {
                'event_id': event_result['id'],
                'html_link': event_result['htmlLink'],
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar API エラー: {e}")
            return False, f"カレンダー登録エラー: {e}"
        except Exception as e:
            logger.error(f"イベント作成エラー: {e}")
            return False, f"イベント作成エラー: {e}"
    
    def create_advance_booking_event(self, advance_booking_data):
        """事前予約イベントをGoogleカレンダーに作成"""
        try:
            if not self.service:
                if not self.authenticate():
                    return False, "認証に失敗しました"
            
            # イベントの開始時刻を設定
            event_date = datetime.strptime(advance_booking_data['booking_date'], '%Y-%m-%d')
            start_time = datetime.combine(event_date, datetime.strptime(advance_booking_data['booking_time'], '%H:%M').time())
            end_time = start_time + timedelta(hours=1)  # 1時間の診察時間
            
            # 事前予約であることを示すイベントの詳細
            event = {
                'summary': f'⏰ かよ皮膚科 事前予約',
                'description': f"""
患者番号: {advance_booking_data['patient_number']}
誕生日: {advance_booking_data['birth_date']}
予約日時: {start_time.strftime('%Y年%m月%d日 %H:%M')}
                
※ 受付時間: {advance_booking_data['booking_time']}開始
※ 診察時間: 約1時間
※ 事前予約管理システムから自動登録
※ 実行日: {advance_booking_data.get('execution_date', '未設定')}
                """.strip(),
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'location': 'かよ皮膚科',
                'colorId': '3',  # 黄色（事前予約用）
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 1440},  # 1日前
                        {'method': 'popup', 'minutes': 60},    # 1時間前
                        {'method': 'popup', 'minutes': 15},    # 15分前
                    ],
                },
                'extendedProperties': {
                    'private': {
                        'patient_number': advance_booking_data['patient_number'],
                        'birth_date': advance_booking_data['birth_date'],
                        'advance_booking_id': str(advance_booking_data.get('advance_booking_id', '')),
                        'source': 'かよ皮膚科事前予約管理システム'
                    }
                }
            }
            
            # イベントを作成
            event_result = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            logger.info(f"Googleカレンダーに事前予約イベントを作成しました: {event_result['id']}")
            
            # 作成されたイベントの情報を返す
            return True, {
                'event_id': event_result['id'],
                'html_link': event_result['htmlLink'],
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar API エラー: {e}")
            return False, f"カレンダー登録エラー: {e}"
        except Exception as e:
            logger.error(f"事前予約イベント作成エラー: {e}")
            return False, f"事前予約イベント作成エラー: {e}"
    
    def update_booking_event(self, event_id, booking_data):
        """既存の予約イベントを更新"""
        try:
            if not self.service:
                if not self.authenticate():
                    return False, "認証に失敗しました"
            
            # 既存のイベントを取得
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # イベントの内容を更新
            event_date = datetime.strptime(booking_data['booking_date'], '%Y-%m-%d')
            start_time = datetime.combine(event_date, datetime.strptime('09:15', '%H:%M').time())
            end_time = start_time + timedelta(hours=1)
            
            event['start']['dateTime'] = start_time.isoformat()
            event['end']['dateTime'] = end_time.isoformat()
            event['description'] = f"""
患者番号: {booking_data['patient_number']}
誕生日: {booking_data['birth_date']}
予約日時: {start_time.strftime('%Y年%m月%d日 %H:%M')}
                
※ 受付時間: 9:15開始
※ 診察時間: 約1時間
※ 予約管理システムから自動更新
            """.strip()
            
            # イベントを更新
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"Googleカレンダーのイベントを更新しました: {event_id}")
            return True, "イベントを更新しました"
            
        except Exception as e:
            logger.error(f"イベント更新エラー: {e}")
            return False, f"イベント更新エラー: {e}"
    
    def delete_booking_event(self, event_id):
        """予約イベントを削除"""
        try:
            if not self.service:
                if not self.authenticate():
                    return False, "認証に失敗しました"
            
            # イベントを削除
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            logger.info(f"Googleカレンダーのイベントを削除しました: {event_id}")
            return True, "イベントを削除しました"
            
        except Exception as e:
            logger.error(f"イベント削除エラー: {e}")
            return False, f"イベント削除エラー: {e}"
    
    def get_calendar_events(self, start_date=None, end_date=None):
        """指定期間のカレンダーイベントを取得"""
        try:
            if not self.service:
                if not self.authenticate():
                    return False, "認証に失敗しました"
            
            # 日付の設定
            if not start_date:
                start_date = datetime.now().date()
            if not end_date:
                end_date = start_date + timedelta(days=30)
            
            # イベントを取得
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=datetime.combine(start_date, datetime.min.time()).isoformat() + 'Z',
                timeMax=datetime.combine(end_date, datetime.max.time()).isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"{len(events)}件のイベントを取得しました")
            
            return True, events
            
        except Exception as e:
            logger.error(f"イベント取得エラー: {e}")
            return False, f"イベント取得エラー: {e}"
    
    def check_credentials_file(self):
        """認証情報ファイルの存在確認"""
        if not os.path.exists(CREDENTIALS_FILE):
            logger.warning(f"Google Calendar API認証情報ファイルが見つかりません: {CREDENTIALS_FILE}")
            return False
        return True
    
    def get_auth_url(self):
        """認証URLを取得（初回設定用）"""
        try:
            if not os.path.exists(CREDENTIALS_FILE):
                return False, "認証情報ファイルが見つかりません"
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            auth_url, _ = flow.authorization_url(prompt='consent')
            return True, auth_url
            
        except Exception as e:
            logger.error(f"認証URL取得エラー: {e}")
            return False, f"認証URL取得エラー: {e}"

# シングルトンインスタンス
_calendar_manager = None

def get_calendar_manager():
    """Google Calendar Managerのインスタンスを取得"""
    global _calendar_manager
    if _calendar_manager is None:
        _calendar_manager = GoogleCalendarManager()
    return _calendar_manager
