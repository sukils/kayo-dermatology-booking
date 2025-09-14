#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
メール送信設定 - かよ皮膚科予約管理システム
予約完了時のメール通知機能
"""

import logging
import json
from flask_mail import Mail, Message
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailManager:
    """メール送信を管理するクラス"""
    
    def __init__(self, app=None):
        self.app = app
        self.mail = None
        self.config = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Flaskアプリケーションにメール機能を初期化"""
        try:
            # 設定ファイルを読み込み
            with open('config/config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # メール設定が有効かチェック
            if not self.config.get('email', {}).get('enabled', False):
                logger.info("メール送信機能は無効です")
                return
            
            # Flask-Mail設定
            app.config['MAIL_SERVER'] = self.config['email']['smtp_server']
            app.config['MAIL_PORT'] = self.config['email']['smtp_port']
            app.config['MAIL_USE_TLS'] = self.config['email']['use_tls']
            app.config['MAIL_USERNAME'] = self.config['email']['username']
            app.config['MAIL_PASSWORD'] = self.config['email']['password']
            app.config['MAIL_DEFAULT_SENDER'] = (
                self.config['email']['from_name'],
                self.config['email']['from_email']
            )
            
            # Flask-Mailを初期化
            self.mail = Mail(app)
            logger.info("メール送信機能が初期化されました")
            
        except Exception as e:
            logger.error(f"メール送信機能の初期化エラー: {e}")
            self.mail = None
    
    def is_enabled(self):
        """メール送信機能が有効かチェック"""
        return self.mail is not None and self.config is not None
    
    def send_booking_confirmation(self, booking_data, recipient_email=None):
        """予約完了確認メールを送信"""
        if not self.is_enabled():
            logger.warning("メール送信機能が無効です")
            return False, "メール送信機能が無効です"
        
        try:
            # メール本文を作成
            subject = f"🎉 かよ皮膚科 予約完了確認 - {booking_data['booking_date']}"
            
            # HTML形式のメール本文
            html_body = self._create_booking_confirmation_html(booking_data)
            
            # プレーンテキスト形式のメール本文
            text_body = self._create_booking_confirmation_text(booking_data)
            
            # メールを作成
            msg = Message(
                subject=subject,
                recipients=[recipient_email] if recipient_email else [],
                html=html_body,
                body=text_body
            )
            
            # メールを送信
            self.mail.send(msg)
            
            logger.info(f"予約完了確認メールを送信しました: {recipient_email}")
            return True, "メール送信が完了しました"
            
        except Exception as e:
            logger.error(f"メール送信エラー: {e}")
            return False, f"メール送信エラー: {str(e)}"
    
    def send_advance_booking_confirmation(self, advance_booking_data, recipient_email=None):
        """事前予約作成確認メールを送信"""
        if not self.is_enabled():
            logger.warning("メール送信機能が無効です")
            return False, "メール送信機能が無効です"
        
        try:
            # メール本文を作成
            subject = f"⏰ かよ皮膚科 事前予約作成確認 - {advance_booking_data['target_booking_date']}"
            
            # HTML形式のメール本文
            html_body = self._create_advance_booking_confirmation_html(advance_booking_data)
            
            # プレーンテキスト形式のメール本文
            text_body = self._create_advance_booking_confirmation_text(advance_booking_data)
            
            # メールを作成
            msg = Message(
                subject=subject,
                recipients=[recipient_email] if recipient_email else [],
                html=html_body,
                body=text_body
            )
            
            # メールを送信
            self.mail.send(msg)
            
            logger.info(f"事前予約作成確認メールを送信しました: {recipient_email}")
            return True, "メール送信が完了しました"
            
        except Exception as e:
            logger.error(f"メール送信エラー: {e}")
            return False, f"メール送信エラー: {str(e)}"
    
    def _create_booking_confirmation_html(self, booking_data):
        """予約完了確認メールのHTML本文を作成"""
        return f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>予約完了確認</title>
            <style>
                body {{
                    font-family: 'Noto Sans JP', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 15px 15px 0 0;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 15px 15px;
                }}
                .booking-details {{
                    background: white;
                    padding: 25px;
                    border-radius: 10px;
                    margin: 20px 0;
                    border-left: 4px solid #27ae60;
                }}
                .booking-number {{
                    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #dee2e6;
                    color: #6c757d;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 24px;
                    background: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px 5px;
                }}
                .btn:hover {{
                    background: #0056b3;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎉 予約完了確認</h1>
                <p>かよ皮膚科の予約が完了しました</p>
            </div>
            
            <div class="content">
                <p>この度は、かよ皮膚科のご予約ありがとうございます。</p>
                <p>以下の内容で予約が完了いたしました。</p>
                
                <div class="booking-details">
                    <h3>📋 予約詳細</h3>
                    <p><strong>患者番号:</strong> {booking_data['patient_number']}</p>
                    <p><strong>誕生日:</strong> {booking_data['birth_date']}</p>
                    <p><strong>予約日:</strong> {booking_data['booking_date']}</p>
                    <p><strong>予約時間:</strong> 09:15</p>
                    <p><strong>予約日時:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>
                </div>
                
                <div class="booking-number">
                    <h3>🔢 予約番号</h3>
                    <h2 style="margin: 0; font-size: 2rem;">{booking_data.get('id', 'N/A')}</h2>
                    <p style="margin: 5px 0 0 0;">この番号は受付時にお伝えください</p>
                </div>
                
                <div style="margin: 30px 0;">
                    <h3>📝 ご来院時の注意事項</h3>
                    <ul>
                        <li>予約時間の15分前にお越しください</li>
                        <li>健康保険証をご持参ください</li>
                        <li>初診の方は問診票の記入が必要です</li>
                        <li>キャンセルの場合は事前にご連絡ください</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://www5.tandt.co.jp/cti/hs713/index_p.html" class="btn" target="_blank">
                        🌐 病院ホームページ
                    </a>
                </div>
            </div>
            
            <div class="footer">
                <p>このメールは自動送信されています。</p>
                <p>ご不明な点がございましたら、お気軽にお電話ください。</p>
                <p><strong>かよ皮膚科</strong><br>
                〒811-2101 福岡県糟屋郡宇美町宇美１丁目9-19<br>
                TEL: 092-692-7339</p>
            </div>
        </body>
        </html>
        """
    
    def _create_booking_confirmation_text(self, booking_data):
        """予約完了確認メールのプレーンテキスト本文を作成"""
        return f"""
🎉 かよ皮膚科 予約完了確認

この度は、かよ皮膚科のご予約ありがとうございます。
以下の内容で予約が完了いたしました。

【予約詳細】
患者番号: {booking_data['patient_number']}
誕生日: {booking_data['birth_date']}
予約日: {booking_data['booking_date']}
予約時間: 09:15
予約日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

【予約番号】
{booking_data.get('id', 'N/A')}
※この番号は受付時にお伝えください

【ご来院時の注意事項】
・予約時間の15分前にお越しください
・健康保険証をご持参ください
・初診の方は問診票の記入が必要です
・キャンセルの場合は事前にご連絡ください

【病院情報】
かよ皮膚科
〒811-2101 福岡県糟屋郡宇美町宇美１丁目9-19
TEL: 092-692-7339
Web: https://www5.tandt.co.jp/cti/hs713/index_p.html

このメールは自動送信されています。
ご不明な点がございましたら、お気軽にお電話ください。
        """
    
    def _create_advance_booking_confirmation_html(self, advance_booking_data):
        """事前予約作成確認メールのHTML本文を作成"""
        return f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>事前予約作成確認</title>
            <style>
                body {{
                    font-family: 'Noto Sans JP', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #f39c12 0%, #f1c40f 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 15px 15px 0 0;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 15px 15px;
                }}
                .booking-details {{
                    background: white;
                    padding: 25px;
                    border-radius: 10px;
                    margin: 20px 0;
                    border-left: 4px solid #f39c12;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #dee2e6;
                    color: #6c757d;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⏰ 事前予約作成確認</h1>
                <p>かよ皮膚科の事前予約が作成されました</p>
            </div>
            
            <div class="content">
                <p>この度は、かよ皮膚科の事前予約をご利用いただき、ありがとうございます。</p>
                <p>以下の内容で事前予約が作成されました。</p>
                
                <div class="booking-details">
                    <h3>📋 事前予約詳細</h3>
                    <p><strong>患者番号:</strong> {advance_booking_data['patient_number']}</p>
                    <p><strong>誕生日:</strong> {advance_booking_data['birth_date']}</p>
                    <p><strong>予約希望日:</strong> {advance_booking_data['target_booking_date']}</p>
                    <p><strong>予約時間:</strong> {advance_booking_data['booking_time']}</p>
                    <p><strong>実行日:</strong> {advance_booking_data['execution_date']}</p>
                    <p><strong>作成日時:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>
                </div>
                
                <div style="margin: 30px 0;">
                    <h3>📝 事前予約について</h3>
                    <ul>
                        <li>実行日に自動で予約処理が実行されます</li>
                        <li>予約の成功・失敗は別途メールでお知らせします</li>
                        <li>予約が完了した場合は、予約番号をお知らせします</li>
                        <li>キャンセルや変更は事前予約管理画面から行えます</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p>このメールは自動送信されています。</p>
                <p>ご不明な点がございましたら、お気軽にお電話ください。</p>
                <p><strong>かよ皮膚科</strong><br>
                〒811-2101 福岡県糟屋郡宇美町宇美１丁目9-19<br>
                TEL: 092-692-7339</p>
            </div>
        </body>
        </html>
        """
    
    def _create_advance_booking_confirmation_text(self, advance_booking_data):
        """事前予約作成確認メールのプレーンテキスト本文を作成"""
        return f"""
⏰ かよ皮膚科 事前予約作成確認

この度は、かよ皮膚科の事前予約をご利用いただき、ありがとうございます。
以下の内容で事前予約が作成されました。

【事前予約詳細】
患者番号: {advance_booking_data['patient_number']}
誕生日: {advance_booking_data['birth_date']}
予約希望日: {advance_booking_data['target_booking_date']}
予約時間: {advance_booking_data['booking_time']}
実行日: {advance_booking_data['execution_date']}
作成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

【事前予約について】
・実行日に自動で予約処理が実行されます
・予約の成功・失敗は別途メールでお知らせします
・予約が完了した場合は、予約番号をお知らせします
・キャンセルや変更は事前予約管理画面から行えます

【病院情報】
かよ皮膚科
〒811-2101 福岡県糟屋郡宇美町宇美１丁目9-19
TEL: 092-692-7339
Web: https://www5.tandt.co.jp/cti/hs713/index_p.html

このメールは自動送信されています。
ご不明な点がございましたら、お気軽にお電話ください。
        """

def get_email_manager(app=None):
    """EmailManagerのインスタンスを取得"""
    return EmailManager(app)
