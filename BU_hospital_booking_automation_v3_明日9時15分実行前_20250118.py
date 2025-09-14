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
        """Chromeドライバー設定"""
        try:
            chrome_options = Options()
            
            if self.config["chrome_options"]["headless"]:
                chrome_options.add_argument("--headless")
                
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"--user-agent={self.config['chrome_options']['user_agent']}")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # ChromeDriverを自動でダウンロード・管理
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
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
            
    def execute_booking(self):
        """予約実行のメイン処理"""
        # 受付時間チェック
        if not self.check_booking_availability():
            self.logger.info("受付時間外のため、予約処理をスキップします")
            return False
            
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

def main():
    """メイン関数"""
    automation = HospitalBookingAutomationV3()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # 一度だけ実行
        automation.run_once()
    else:
        # スケジューラー実行
        automation.run_scheduler()

if __name__ == "__main__":
    main()
