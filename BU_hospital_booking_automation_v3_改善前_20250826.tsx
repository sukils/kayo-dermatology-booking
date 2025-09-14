#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
病院予約自動化プログラム v3
かよ皮膚科のWeb予約システムを自動で操作するプログラム
受付時間の制限に対応（患者番号のみの入力）
"""

import time
import json
import logging
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import schedule
import os

class HospitalBookingAutomationV3:
    def __init__(self, config_file="config_v3.json"):
        """初期化"""
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        self.driver = None
        self.session = requests.Session()
        
        # 受付時間設定
        self.booking_hours = {
            "monday": {"morning": "09:00-12:00", "afternoon": "14:00-17:00", "web": "12:00-16:00"},
            "tuesday": {"morning": "09:00-12:30", "afternoon": "14:00-17:00", "web": "12:00-16:00"},
            "wednesday": {"morning": "09:00-12:30", "afternoon": "14:00-17:00", "web": "12:00-16:00"},
            "thursday": {"morning": "09:00-12:30", "afternoon": "14:00-17:00", "web": "12:00-16:00"},
            "friday": {"morning": "09:00-12:30", "afternoon": "14:00-17:00", "web": "12:00-16:00"},
            "saturday": {"morning": "09:00-12:30", "afternoon": "休診", "web": "12:00まで"},
            "sunday": {"morning": "休診", "afternoon": "休診", "web": "休診"}
        }
        
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('hospital_booking_v3.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self):
        """設定ファイル読み込み"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # デフォルト設定を作成
            default_config = {
                "hospital_url": "https://www5.tandt.co.jp/cti/hs713/index_p.html",
                "booking_times": [
                    {
                        "day": "monday",
                        "time": "12:05",
                        "enabled": True
                    },
                    {
                        "day": "tuesday", 
                        "time": "12:05",
                        "enabled": True
                    },
                    {
                        "day": "wednesday",
                        "time": "12:05", 
                        "enabled": True
                    },
                    {
                        "day": "thursday",
                        "time": "12:05",
                        "enabled": True
                    },
                    {
                        "day": "friday",
                        "time": "12:05",
                        "enabled": True
                    }
                ],
                                 "patient_info": {
                     "patient_number": "12345",  # 患者番号
                     "birth_date": "1990-01-01"  # 生年月日
                 },
                "chrome_options": {
                    "headless": False,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                "wait_timeout": 20,
                "retry_count": 3,
                "page_elements": {
                    "booking_button": [
                        "//a[contains(text(), '順番受付')]",
                        "//a[contains(text(), '予約')]",
                        "//button[contains(text(), '予約')]",
                        "//a[contains(text(), 'Web予約')]",
                        "//button[contains(text(), 'Web予約')]"
                    ],
                                         "patient_number_input": [
                         "//input[@name='patient_number']",
                         "//input[@name='patient_no']",
                         "//input[@name='patient_id']",
                         "//input[@placeholder='患者番号']",
                         "//input[@placeholder='患者No']",
                         "//input[@id='patient_number']",
                         "//input[@id='patient_no']",
                         "//input[@id='patient_id']"
                     ],
                     "birth_date_input": [
                         "//input[@name='birth_date']",
                         "//input[@name='birthday']",
                         "//input[@name='birth']",
                         "//input[@type='date']",
                         "//input[@placeholder='生年月日']",
                         "//input[@placeholder='誕生日']",
                         "//input[@id='birth_date']",
                         "//input[@id='birthday']",
                         "//input[@id='birth']"
                     ],
                    "submit_button": [
                        "//button[@type='submit']",
                        "//input[@type='submit']",
                        "//button[contains(text(), '送信')]",
                        "//button[contains(text(), '確認')]",
                        "//button[contains(text(), '予約')]",
                        "//input[@value='送信']",
                        "//input[@value='確認']",
                        "//input[@value='予約']"
                    ]
                }
            }
            self.save_config(default_config)
            return default_config
            
    def save_config(self, config):
        """設定ファイル保存"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
    def check_booking_availability(self):
        """受付可能時間をチェック"""
        now = datetime.now()
        weekday = now.strftime("%A").lower()
        
        if weekday not in self.booking_hours:
            self.logger.warning(f"不明な曜日: {weekday}")
            return False
            
        hours = self.booking_hours[weekday]
        
        # Web予約受付可能かチェック
        if hours['web'] == "休診":
            self.logger.info(f"{weekday}はWeb予約受付不可（休診日）")
            return False
        elif hours['web'] == "12:00まで":
            if now.hour < 12:
                self.logger.info(f"{weekday} {now.hour}:{now.minute} - Web予約受付可能（午前中）")
                return True
            else:
                self.logger.info(f"{weekday} {now.hour}:{now.minute} - Web予約受付終了（午前のみ）")
                return False
        else:  # 12:00-16:00
            if 12 <= now.hour < 16:
                self.logger.info(f"{weekday} {now.hour}:{now.minute} - Web予約受付可能（午後）")
                return True
            elif now.hour < 12:
                self.logger.info(f"{weekday} {now.hour}:{now.minute} - Web予約受付開始まで待機中（12:00開始）")
                return False
            else:
                self.logger.info(f"{weekday} {now.hour}:{now.minute} - Web予約受付終了（16:00まで）")
                return False
                
    def setup_driver(self):
        """Chromeドライバーの設定"""
        try:
            chrome_options = Options()
            
            # 設定ファイルからオプションを読み込み
            config_options = self.config.get("chrome_options", {})
            
            # ヘッドレスモード設定
            if config_options.get("headless", False):
                chrome_options.add_argument("--headless")
            
            # ユーザーエージェント設定
            user_agent = config_options.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            chrome_options.add_argument(f"--user-agent={user_agent}")
            
            # Windows環境での互換性向上
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # ウィンドウサイズ設定
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.logger.info("Chromeドライバーの初期化を開始します")
            
            # ChromeDriverを自動でダウンロード・管理（Windows環境対応）
            try:
                # 最新版をダウンロード
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                self.logger.warning(f"最新版ChromeDriverでエラー: {e}")
                # 代替手段として、システムにインストールされているChromeDriverを使用
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                except Exception as e2:
                    self.logger.error(f"システムChromeDriverでもエラー: {e2}")
                    # 最後の手段として、特定のバージョンを試す
                    try:
                        from webdriver_manager.chrome import ChromeDriverManager
                        service = Service(ChromeDriverManager(version="114.0.5735.90").install())
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                        self.logger.info("特定バージョンのChromeDriverで初期化成功")
                    except Exception as e3:
                        self.logger.error(f"すべてのChromeDriver初期化方法でエラー: {e3}")
                        raise e3
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(10)
            self.logger.info("Chromeドライバーの初期化が完了しました")
            
        except Exception as e:
            self.logger.error(f"ドライバー初期化エラー: {e}")
            raise
            
    def navigate_to_booking_page(self):
        """予約ページに移動"""
        try:
            self.logger.info(f"予約ページに移動中: {self.config['hospital_url']}")
            self.driver.get(self.config['hospital_url'])
            
            # ページ読み込み完了まで待機
            WebDriverWait(self.driver, self.config["wait_timeout"]).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # ページの完全な読み込みを待機
            time.sleep(3)
            
            self.logger.info("予約ページの読み込みが完了しました")
            return True
            
        except TimeoutException:
            self.logger.error("ページ読み込みがタイムアウトしました")
            return False
        except Exception as e:
            self.logger.error(f"ページ移動エラー: {e}")
            return False
            
    def navigate_to_reception_system(self):
        """受付システムに直接アクセス"""
        try:
            # 現在の日時を取得
            current_date = datetime.now()
            ymd = current_date.strftime("%Y%m%d%H%M")
            
            # 受付システムのURLを構築
            reception_url = f"https://www4.tandt.co.jp/rsvsys/jsp/JobDispatcher.jsp?q={int(time.time())}&agent=RSV1&jobid=rsvmodM02&callback=0&ymd={ymd}&subno=01&subname=BB6CDC019CAD7600&newtimetotime=1200"
            
            self.logger.info(f"受付システムに直接アクセス: {reception_url}")
            self.driver.get(reception_url)
            
            # ページ読み込み完了まで待機
            WebDriverWait(self.driver, self.config["wait_timeout"]).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # ページの完全な読み込みを待機
            time.sleep(3)
            
            self.logger.info("受付システムの読み込みが完了しました")
            return True
            
        except TimeoutException:
            self.logger.error("受付システムの読み込みがタイムアウトしました")
            return False
        except Exception as e:
            self.logger.error(f"受付システムアクセスエラー: {e}")
            return False
            
    def find_booking_button(self):
        """予約ボタンを探す"""
        try:
            page_elements = self.config["page_elements"]["booking_button"]
            
            for xpath in page_elements:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    self.logger.info(f"予約ボタンを発見: {xpath}")
                    return element
                except (NoSuchElementException, TimeoutException):
                    continue
                    
            self.logger.warning("予約ボタンが見つかりませんでした")
            return None
            
        except Exception as e:
            self.logger.error(f"予約ボタン検索エラー: {e}")
            return None
            
    def find_patient_number_input(self):
        """患者番号入力フィールドを探す"""
        try:
            page_elements = self.config["page_elements"]["patient_number_input"]
            
            for xpath in page_elements:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    self.logger.info(f"患者番号入力フィールドを発見: {xpath}")
                    return element
                except (NoSuchElementException, TimeoutException):
                    continue
                    
            self.logger.warning("患者番号入力フィールドが見つかりませんでした")
            return None
            
        except Exception as e:
            self.logger.error(f"患者番号入力フィールド検索エラー: {e}")
            return None
            
    def find_birth_date_input(self):
        """生年月日入力フィールドを探す"""
        try:
            page_elements = self.config["page_elements"]["birth_date_input"]
            
            for xpath in page_elements:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    self.logger.info(f"生年月日入力フィールドを発見: {xpath}")
                    return element
                except (NoSuchElementException, TimeoutException):
                    continue
                    
            self.logger.warning("生年月日入力フィールドが見つかりませんでした")
            return None
            
        except Exception as e:
            self.logger.error(f"生年月日入力フィールド検索エラー: {e}")
            return None
            
    def fill_patient_number(self):
        """患者番号を入力"""
        try:
            patient_info = self.config["patient_info"]
            patient_number = patient_info["patient_number"]
            
            # 患者番号入力フィールドを探す
            input_field = self.find_patient_number_input()
            if not input_field:
                raise Exception("患者番号入力フィールドが見つかりませんでした")
                
            # 入力フィールドをクリアして患者番号を入力
            input_field.clear()
            input_field.send_keys(patient_number)
            self.logger.info(f"患者番号を入力しました: {patient_number}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"患者番号入力エラー: {e}")
            return False
            
    def fill_birth_date(self):
        """生年月日を入力"""
        try:
            patient_info = self.config["patient_info"]
            birth_date = patient_info["birth_date"]
            
            # 生年月日入力フィールドを探す
            input_field = self.find_birth_date_input()
            if not input_field:
                raise Exception("生年月日入力フィールドが見つかりませんでした")
                
            # 入力フィールドをクリアして生年月日を入力
            input_field.clear()
            input_field.send_keys(birth_date)
            self.logger.info(f"生年月日を入力しました: {birth_date}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"生年月日入力エラー: {e}")
            return False
            
    def find_submit_button(self):
        """送信ボタンを探す"""
        try:
            page_elements = self.config["page_elements"]["submit_button"]
            
            for xpath in page_elements:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    self.logger.info(f"送信ボタンを発見: {xpath}")
                    return element
                except (NoSuchElementException, TimeoutException):
                    continue
                    
            self.logger.warning("送信ボタンが見つかりませんでした")
            return None
            
        except Exception as e:
            self.logger.error(f"送信ボタン検索エラー: {e}")
            return False
            
    def submit_booking(self):
        """予約を送信"""
        try:
            # 送信ボタンを探す
            submit_btn = self.find_submit_button()
            if not submit_btn:
                raise Exception("送信ボタンが見つかりませんでした")
                
            # 送信ボタンをクリック
            submit_btn.click()
            self.logger.info("予約フォームを送信しました")
            
            # 送信完了まで待機
            time.sleep(5)
            return True
            
        except Exception as e:
            self.logger.error(f"送信エラー: {e}")
            return False
            
    def take_screenshot(self, filename=None):
        """スクリーンショット取得"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_v3_{timestamp}.png"
                
            self.driver.save_screenshot(filename)
            self.logger.info(f"スクリーンショットを保存しました: {filename}")
            
        except Exception as e:
            self.logger.error(f"スクリーンショット保存エラー: {e}")
            
    def execute_booking(self, force_analyze=False):
        """予約実行のメイン処理"""
        # 受付時間チェック（強制解析モードの場合はスキップ）
        if not force_analyze and not self.check_booking_availability():
            self.logger.info("受付時間外のため、予約処理をスキップします")
            return False
            
        if force_analyze:
            self.logger.info("強制解析モード: 受付時間チェックをスキップして解析処理を実行します")
            
        retry_count = 0
        max_retries = self.config.get("retry_count", 3)
        
        while retry_count < max_retries:
            try:
                self.logger.info(f"予約処理を開始します（試行 {retry_count + 1}/{max_retries}）")
                
                # ドライバー設定
                self.setup_driver()
                
                # 予約ページに移動
                if not self.navigate_to_booking_page():
                    raise Exception("ページ移動に失敗しました")
                    
                # スクリーンショット取得
                self.take_screenshot("before_booking.png")
                
                # 予約ボタンを探す
                booking_button = self.find_booking_button()
                if not booking_button:
                    raise Exception("予約ボタンが見つかりませんでした")
                    
                # 予約ボタンをクリック
                booking_button.click()
                time.sleep(3)
                
                # 患者番号入力画面のスクリーンショット
                self.take_screenshot("patient_number_form.png")
                
                # 患者番号を入力
                if not self.fill_patient_number():
                    raise Exception("患者番号入力に失敗しました")
                    
                # 生年月日を入力
                if not self.fill_birth_date():
                    raise Exception("生年月日入力に失敗しました")
                    
                # 入力後のスクリーンショット
                self.take_screenshot("after_input_complete.png")
                
                # 予約送信
                if not self.submit_booking():
                    raise Exception("予約送信に失敗しました")
                    
                # 送信後のスクリーンショット
                self.take_screenshot("after_submit.png")
                
                self.logger.info("予約処理が完了しました")
                return True
                
            except Exception as e:
                retry_count += 1
                self.logger.error(f"予約処理エラー（試行 {retry_count}/{max_retries}）: {e}")
                
                if self.driver:
                    self.take_screenshot(f"error_screenshot_attempt_{retry_count}.png")
                    self.driver.quit()
                    self.driver = None
                
                if retry_count < max_retries:
                    self.logger.info(f"5秒後にリトライします...")
                    time.sleep(5)
                else:
                    self.logger.error("最大リトライ回数に達しました")
                    return False
                    
        return False
                
    def schedule_bookings(self):
        """予約スケジュール設定"""
        for booking_time in self.config["booking_times"]:
            if booking_time["enabled"]:
                day = booking_time["day"]
                time_str = booking_time["time"]
                
                if day == "monday":
                    schedule.every().monday.at(time_str).do(self.execute_booking)
                elif day == "tuesday":
                    schedule.every().tuesday.at(time_str).do(self.execute_booking)
                elif day == "wednesday":
                    schedule.every().wednesday.at(time_str).do(self.execute_booking)
                elif day == "thursday":
                    schedule.every().thursday.at(time_str).do(self.execute_booking)
                elif day == "friday":
                    schedule.every().friday.at(time_str).do(self.execute_booking)
                    
                self.logger.info(f"{day} {time_str}に予約処理をスケジュールしました")
                
    def run_scheduler(self):
        """スケジューラー実行"""
        self.logger.info("スケジューラーを開始しました")
        self.schedule_bookings()
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # 1分ごとにチェック
            except KeyboardInterrupt:
                self.logger.info("スケジューラーを停止します")
                break
            except Exception as e:
                self.logger.error(f"スケジューラーエラー: {e}")
                time.sleep(60)
                
    def run_once(self):
        """一度だけ実行"""
        self.logger.info("一度だけ予約処理を実行します")
        return self.execute_booking()

    def schedule_tomorrow_9_15(self):
        """明日9時15分に一度だけ実行をスケジュール"""
        tomorrow = datetime.now() + timedelta(days=1)
        target_time = tomorrow.replace(hour=9, minute=15, second=0, microsecond=0)
        
        self.logger.info(f"明日 {target_time.strftime('%Y年%m月%d日 %H:%M')} に解析処理を実行するようにスケジュールしました")
        
        # 明日9時15分に実行
        schedule.every().day.at("09:15").do(self.execute_booking)
        
        return target_time
    
    def run_tomorrow_9_15(self):
        """明日9時15分まで待機してから実行"""
        target_time = self.schedule_tomorrow_9_15()
        
        self.logger.info("明日9時15分まで待機中...")
        self.logger.info(f"現在時刻: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        self.logger.info(f"実行予定時刻: {target_time.strftime('%Y年%m月%d日 %H:%M:%S')}")
        
        while True:
            try:
                schedule.run_pending()
                current_time = datetime.now()
                
                # 現在時刻をログに出力（1時間ごと）
                if current_time.minute == 0:
                    self.logger.info(f"現在時刻: {current_time.strftime('%Y年%m月%d日 %H:%M:%S')}")
                
                time.sleep(60)  # 1分ごとにチェック
                
            except KeyboardInterrupt:
                self.logger.info("スケジューラーを停止します")
                break
            except Exception as e:
                self.logger.error(f"スケジューラーエラー: {e}")
                time.sleep(60)

    def analyze_current_status(self):
        """現在の受付状況を解析"""
        self.logger.info("現在の受付状況を解析します")
        
        try:
            # ドライバー設定
            self.setup_driver()
            
            # 予約ページに移動
            if not self.navigate_to_booking_page():
                raise Exception("ページ移動に失敗しました")
                
            # 現在のページ状態をスクリーンショットで保存
            self.take_screenshot("current_status_analysis.png")
            
            # ページのHTMLを取得して解析
            page_source = self.driver.page_source
            self.logger.info(f"ページのHTMLを取得しました（長さ: {len(page_source)}文字）")
            
            # 予約ボタンの有無を確認
            booking_button = self.find_booking_button()
            if booking_button:
                self.logger.info("予約ボタンが利用可能です")
                button_text = booking_button.text
                self.logger.info(f"ボタンテキスト: {button_text}")
            else:
                self.logger.warning("予約ボタンが見つかりませんでした")
            
            # ページタイトルを確認
            page_title = self.driver.title
            self.logger.info(f"ページタイトル: {page_title}")
            
            # 現在のURLを確認
            current_url = self.driver.current_url
            self.logger.info(f"現在のURL: {current_url}")
            
            # 受付可能な時間帯の情報を探す
            try:
                time_info_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '受付') or contains(text(), '予約') or contains(text(), '時間')]")
                if time_info_elements:
                    self.logger.info("受付時間関連の情報を発見:")
                    for i, elem in enumerate(time_info_elements[:5]):  # 最初の5件のみ表示
                        try:
                            text = elem.text.strip()
                            if text:
                                self.logger.info(f"  要素{i+1}: {text}")
                        except:
                            continue
            except Exception as e:
                self.logger.warning(f"受付時間情報の検索でエラー: {e}")
            
            self.logger.info("現在の状況の解析が完了しました")
            return True
            
        except Exception as e:
            self.logger.error(f"状況解析エラー: {e}")
            if self.driver:
                self.take_screenshot(f"error_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                self.driver.quit()
                self.driver = None
            return False

    def find_same_day_booking_button(self):
        """順番受付(当日外来)ボタンを探す"""
        try:
            # 順番受付関連の要素を探す
            same_day_patterns = [
                "//a[contains(text(), '順番受付(当日外来)')]",
                "//a[contains(text(), '順番受付')]",
                "//a[contains(text(), '当日外来')]",
                "//div[contains(text(), '順番受付')]//a",
                "//span[contains(text(), '順番受付')]//a"
            ]
            
            for xpath in same_day_patterns:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    self.logger.info(f"順番受付ボタンを発見: {xpath}")
                    return element
                except (NoSuchElementException, TimeoutException):
                    continue
                    
            self.logger.warning("順番受付ボタンが見つかりませんでした")
            return None
            
        except Exception as e:
            self.logger.error(f"順番受付ボタン検索エラー: {e}")
            return None
    
    def find_reception_button(self):
        """「受付中」ボタンを優先的に探す"""
        try:
            # 受付中ボタンを優先的に探す
            reception_patterns = [
                "//a[contains(text(), '受付中')]",
                "//button[contains(text(), '受付中')]",
                "//input[@value='受付中']",
                "//div[contains(text(), '受付中')]//a",
                "//span[contains(text(), '受付中')]//a"
            ]
            
            for xpath in reception_patterns:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    self.logger.info(f"受付中ボタンを発見: {xpath}")
                    return element
                except (NoSuchElementException, TimeoutException):
                    continue
                    
            self.logger.warning("受付中ボタンが見つかりませんでした")
            return None
            
        except Exception as e:
            self.logger.error(f"受付中ボタン検索エラー: {e}")
            return None

    def get_waiting_count(self):
        """現在の待ち人数を取得"""
        try:
            # 待ち人数の要素を探す
            wait_count_patterns = [
                "//div[contains(text(), '待ち人数')]//span",
                "//div[@class='dt-sts-su']//span",
                "//div[contains(@class, 'dt-sts')]//span"
            ]
            
            for xpath in wait_count_patterns:
                try:
                    element = self.driver.find_element(By.XPATH, xpath)
                    wait_count = element.text.strip()
                    if wait_count.isdigit():
                        self.logger.info(f"現在の待ち人数: {wait_count}人")
                        return int(wait_count)
                except (NoSuchElementException, Exception):
                    continue
            
            self.logger.warning("待ち人数を取得できませんでした")
            return None
            
        except Exception as e:
            self.logger.error(f"待ち人数取得エラー: {e}")
            return None
    
    def check_optimal_booking_time(self):
        """最適な予約タイミングをチェック"""
        try:
            wait_count = self.get_waiting_count()
            if wait_count is not None:
                if wait_count <= 10:
                    self.logger.info(f"待ち人数が{wait_count}人と少ないため、予約処理を実行します")
                    return True
                elif wait_count <= 20:
                    self.logger.info(f"待ち人数が{wait_count}人です。予約処理を実行します")
                    return True
                else:
                    self.logger.info(f"待ち人数が{wait_count}人と多いため、少し待機します")
                    return False
            return True  # 待ち人数が取得できない場合は実行
        except Exception as e:
            self.logger.error(f"最適タイミングチェックエラー: {e}")
            return True

    def execute_same_day_booking(self):
        """順番受付(当日外来)の自動処理"""
        self.logger.info("順番受付(当日外来)の処理を開始します")
        
        try:
            # ドライバー設定
            self.setup_driver()
            
            # 受付システムに直接アクセス
            if not self.navigate_to_reception_system():
                # 直接アクセスが失敗した場合は通常のページから開始
                self.logger.info("受付システムへの直接アクセスが失敗したため、通常のページから開始します")
                if not self.navigate_to_booking_page():
                    raise Exception("ページ移動に失敗しました")
                
            # 現在の状況をスクリーンショットで保存
            self.take_screenshot("before_same_day_booking.png")
            
            # 待ち人数をチェック
            if not self.check_optimal_booking_time():
                self.logger.info("待ち人数が多いため、30秒待機します")
                time.sleep(30)
                # 再度待ち人数をチェック
                if not self.check_optimal_booking_time():
                    self.logger.info("待ち人数が依然として多いため、処理を終了します")
                    return False
            
            # 受付中ボタンを優先的に探す
            booking_button = self.find_reception_button()
            if not booking_button:
                # 順番受付ボタンも試す
                booking_button = self.find_same_day_booking_button()
                if not booking_button:
                    # 通常の予約ボタンも試す
                    booking_button = self.find_booking_button()
                    if not booking_button:
                        raise Exception("受付ボタンが見つかりませんでした")
            
            # ボタンの詳細情報をログに出力
            button_text = booking_button.text
            button_tag = booking_button.tag_name
            button_href = booking_button.get_attribute('href') if button_tag == 'a' else 'N/A'
            self.logger.info(f"発見したボタン: タグ={button_tag}, テキスト='{button_text}', href='{button_href}'")
            
            # ボタンをクリック
            self.logger.info("受付ボタンをクリックします")
            booking_button.click()
            time.sleep(3)
            
            # クリック後の画面をスクリーンショットで保存
            self.take_screenshot("after_clicking_reception_button.png")
            
            # 次の画面で患者番号入力フィールドを探す
            if not self.fill_patient_number():
                raise Exception("患者番号入力に失敗しました")
                
            # 生年月日を入力
            if not self.fill_birth_date():
                raise Exception("生年月日入力に失敗しました")
                
            # 入力完了後のスクリーンショット
            self.take_screenshot("after_input_complete_same_day.png")
            
            # 送信ボタンを探して送信
            if not self.submit_booking():
                raise Exception("受付の送信に失敗しました")
                
            # 送信完了後のスクリーンショット
            self.take_screenshot("after_submit_same_day.png")
            
            self.logger.info("受付処理が完了しました")
            return True
            
        except Exception as e:
            self.logger.error(f"受付処理エラー: {e}")
            if self.driver:
                self.take_screenshot(f"error_reception_booking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                self.driver.quit()
                self.driver = None
            return False

    def run_force_analyze(self):
        """強制的に解析処理を実行"""
        self.logger.info("強制解析モードで解析処理を開始します")
        return self.execute_same_day_booking()

    def execute_lightweight_booking(self):
        """軽量版の自動予約処理（Selenium不使用）"""
        self.logger.info("軽量版の自動予約処理を開始します")
        
        max_retries = 5  # 最大リトライ回数を制限
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                retry_count += 1
                self.logger.info(f"試行 {retry_count}/{max_retries}")
                
                # まずトップページから開始
                top_url = "https://www5.tandt.co.jp/cti/hs713/index_p.html"
                self.logger.info(f"トップページにアクセス: {top_url}")
                
                # ヘッダーを設定
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Referer': 'https://www5.tandt.co.jp/cti/hs713/index_p.html'
                }
                
                # トップページを取得
                response = self.session.get(top_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # トップページを保存
                with open(f"top_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                
                self.logger.info(f"トップページを取得しました（サイズ: {len(response.text)}文字）")
                
                # 順番受付のリンクを探す（実際のHTMLの構造に基づく）
                import re
                reception_link_match = re.search(r'href="([^"]*nj=rsvmodG01[^"]*)"', response.text)
                if reception_link_match:
                    reception_link = reception_link_match.group(1)
                    if not reception_link.startswith('http'):
                        reception_link = "https://www4.tandt.co.jp/rsvsys/jsp/" + reception_link
                    
                    self.logger.info(f"順番受付リンクを発見: {reception_link}")
                    
                    # 順番受付ページにアクセス
                    self.logger.info("順番受付ページにアクセスします")
                    reception_response = self.session.get(reception_link, headers=headers, timeout=30)
                    reception_response.raise_for_status()
                    
                    # 順番受付ページを保存
                    with open(f"reception_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
                        f.write(reception_response.text)
                    
                    self.logger.info("順番受付ページを取得しました")
                    
                    # HTMLから待ち人数を抽出
                    wait_count_match = re.search(r'待ち人数.*?(\d+)', reception_response.text)
                    if wait_count_match:
                        wait_count = int(wait_count_match.group(1))
                        self.logger.info(f"現在の待ち人数: {wait_count}人")
                        self.logger.info("待ち人数に関係なく、即座に予約処理を実行します")
                    else:
                        self.logger.warning("待ち人数を取得できませんでした")
                    
                    # 受付中ボタンのリンクを探す
                    reception_button_match = re.search(r'href="([^"]*rsvmodM02[^"]*)"', reception_response.text)
                    if reception_button_match:
                        reception_button_link = reception_button_match.group(1)
                        if not reception_button_link.startswith('http'):
                            reception_button_link = "https://www4.tandt.co.jp/rsvsys/jsp/" + reception_button_link
                        
                        self.logger.info(f"受付ボタンリンクを発見: {reception_button_link}")
                        
                        # 受付フォームにアクセス
                        self.logger.info("受付フォームにアクセスします")
                        form_response = self.session.get(reception_button_link, headers=headers, timeout=30)
                        form_response.raise_for_status()
                        
                        # フォームページを保存
                        with open(f"reception_form_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
                            f.write(form_response.text)
                        
                        self.logger.info("受付フォームのページを取得しました")
                        
                        # 患者情報を送信
                        patient_data = {
                            'patient_number': self.config['patient_info']['patient_number'],
                            'birth_date': self.config['patient_info']['birth_date']
                        }
                        
                        self.logger.info(f"患者情報を送信: {patient_data}")
                        
                        # 実際のフォーム送信処理
                        self.logger.info("実際の予約フォームに患者情報を入力して送信します")
                        
                        # 生年月日を月と日に分割
                        birth_date = datetime.strptime(patient_data['birth_date'], '%Y-%m-%d')
                        birth_month = birth_date.strftime('%m')
                        birth_day = birth_date.strftime('%d')
                        
                        # 現在のセッションから必要なパラメータを取得
                        current_url = form_response.url
                        self.logger.info(f"現在のフォームURL: {current_url}")
                        
                        # URLから必要なパラメータを抽出
                        import re
                        ymd_match = re.search(r'ymd=(\d+)', current_url)
                        subno_match = re.search(r'subno=(\d+)', current_url)
                        subname_match = re.search(r'subname=([^&]+)', current_url)
                        
                        ymd = ymd_match.group(1) if ymd_match else datetime.now().strftime('%Y%m%d%H%M')
                        subno = subno_match.group(1) if subno_match else '01'
                        subname = subname_match.group(1) if subname_match else 'BB6CDC019CAD7600'
                        
                        self.logger.info(f"抽出されたパラメータ: ymd={ymd}, subno={subno}, subname={subname}")
                        
                        # フォームデータを準備（より正確なパラメータ）
                        form_data = {
                            'pNo': patient_data['patient_number'],  # 診察券番号
                            'pBDayMM': birth_month,  # 誕生月
                            'pBDayDD': birth_day,    # 誕生日
                            'pSessyu': '',
                            'pCondition': '',
                            'pComment': '',
                            'pCure': '',
                            'clr': '0',
                            'pCtl': '0',
                            'agent': 'RSV1',
                            'jobid': 'rsvmodM04',
                            'callback': '0',
                            'ymd': ymd,  # URLから抽出した値を使用
                            'subno': subno,  # URLから抽出した値を使用
                            'subname': subname,  # URLから抽出した値を使用
                            'pFamily': '1',
                            'pBTemp': ''
                        }
                        
                        self.logger.info(f"送信するフォームデータ: {form_data}")
                        
                        # セッションを維持するためにRefererを設定
                        headers['Referer'] = current_url
                        
                        # フォームを送信
                        submit_url = "https://www4.tandt.co.jp/rsvsys/jsp/rsvmodM04.jsp"
                        self.logger.info(f"送信先URL: {submit_url}")
                        
                        submit_response = self.session.post(submit_url, data=form_data, headers=headers, timeout=30)
                        submit_response.raise_for_status()
                        
                        # 送信結果を保存
                        with open(f"submit_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
                            f.write(submit_response.text)
                        
                        self.logger.info("予約フォームの送信が完了しました")
                        self.logger.info(f"送信結果のサイズ: {len(submit_response.text)}文字")
                        
                        # 送信結果を確認
                        if "サーバーエラー" in submit_response.text:
                            self.logger.error("サーバーエラーが発生しました。別のアプローチを試します")
                            
                            # 無限ループを防ぐため、再帰呼び出しは行わない
                            self.logger.info("フォームの送信方法を変更して再試行します")
                            
                            # 別のアプローチ: 直接的なPOSTではなく、フォームのaction属性を使用
                            try:
                                # フォームのHTMLからaction属性を取得
                                action_match = re.search(r'action="([^"]+)"', form_response.text)
                                if action_match:
                                    actual_action = action_match.group(1)
                                    self.logger.info(f"フォームの実際のaction: {actual_action}")
                                    
                                    # 相対パスを絶対パスに変換
                                    if actual_action.startswith('../'):
                                        base_url = "https://www4.tandt.co.jp/rsvsys/jsp/"
                                        full_action = base_url + actual_action[3:]
                                    else:
                                        full_action = actual_action
                                    
                                    self.logger.info(f"完全なaction URL: {full_action}")
                                    
                                    # 新しいaction URLで再送信
                                    retry_response = self.session.post(full_action, data=form_data, headers=headers, timeout=30)
                                    retry_response.raise_for_status()
                                    
                                    self.logger.info(f"再送信結果のサイズ: {len(retry_response.text)}文字")
                                    
                                    if "確認" in retry_response.text:
                                        self.logger.info("🎉 確認画面に到達しました！予約の確認が可能です")
                                        return True
                                    elif "完了" in retry_response.text:
                                        self.logger.info("🎉 予約が完了しました！")
                                        return True
                                    else:
                                        self.logger.warning("再送信も成功しませんでした")
                                        return False
                                else:
                                    self.logger.error("フォームのaction属性が見つかりませんでした")
                                    return False
                            except Exception as e:
                                self.logger.error(f"再送信でエラーが発生: {e}")
                                return False
                            
                        elif "確認" in submit_response.text:
                            self.logger.info("🎉 確認画面に到達しました！予約の確認が可能です")
                            return True
                        elif "完了" in submit_response.text:
                            self.logger.info("🎉 予約が完了しました！")
                            return True
                        else:
                            self.logger.warning("送信は完了しましたが、結果の確認が必要です")
                            self.logger.info(f"送信結果の内容: {submit_response.text[:200]}...")
                            return True
                    else:
                        self.logger.error("受付ボタンリンクが見つかりませんでした")
                        return False
                else:
                    self.logger.error("順番受付リンクが見つかりませんでした")
                    return False
                    
            except Exception as e:
                self.logger.error(f"軽量版予約処理エラー（試行 {retry_count}/{max_retries}）: {e}")
                if retry_count < max_retries:
                    self.logger.info("5秒後にリトライします")
                    time.sleep(5)
                    continue
                else:
                    self.logger.error("最大リトライ回数に達しました")
                    return False
        
        self.logger.error("最大リトライ回数に達しました")
        return False

def main():
    """メイン関数"""
    automation = HospitalBookingAutomationV3()
    
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "--once":
            # 一度だけ実行
            automation.run_once()
        elif sys.argv[1] == "--tomorrow-9-15":
            # 明日9時15分に実行
            automation.run_tomorrow_9_15()
        elif sys.argv[1] == "--force-analyze":
            # 強制解析モード（順番受付処理）
            automation.run_force_analyze()
        elif sys.argv[1] == "--lightweight-booking":
            # 軽量版の自動予約処理
            automation.execute_lightweight_booking()
        elif sys.argv[1] == "--same-day-booking":
            # 順番受付(当日外来)の自動処理
            automation.execute_same_day_booking()
        elif sys.argv[1] == "--analyze-status":
            # 現在の状況を解析
            automation.analyze_current_status()
        else:
            print("使用方法:")
            print("  python hospital_booking_automation_v3.py          # 通常のスケジューラー実行")
            print("  python hospital_booking_automation_v3.py --once   # 一度だけ実行")
            print("  python hospital_booking_automation_v3.py --tomorrow-9-15  # 明日9時15分に実行")
            print("  python hospital_booking_automation_v3.py --force-analyze  # 順番受付の自動処理")
            print("  python hospital_booking_automation_v3.py --lightweight-booking  # 軽量版の自動予約")
            print("  python hospital_booking_automation_v3.py --same-day-booking  # 順番受付(当日外来)の自動処理")
            print("  python hospital_booking_automation_v3.py --analyze-status # 現在の状況を解析")
    else:
        # スケジューラー実行
        automation.run_scheduler()

if __name__ == "__main__":
    main()
