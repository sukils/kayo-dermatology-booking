#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
病院予約自動化プログラム
かよ皮膚科のWeb予約システムを自動で操作するプログラム
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

class HospitalBookingAutomation:
    def __init__(self, config_file="config.json"):
        """初期化"""
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        self.driver = None
        
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('hospital_booking.log', encoding='utf-8'),
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
                        "time": "12:00",
                        "enabled": True
                    },
                    {
                        "day": "tuesday", 
                        "time": "12:00",
                        "enabled": True
                    },
                    {
                        "day": "wednesday",
                        "time": "12:00", 
                        "enabled": True
                    },
                    {
                        "day": "thursday",
                        "time": "12:00",
                        "enabled": True
                    },
                    {
                        "day": "friday",
                        "time": "12:00",
                        "enabled": True
                    }
                ],
                "patient_info": {
                    "name": "患者様",
                    "phone": "090-0000-0000",
                    "email": "patient@example.com"
                },
                "chrome_options": {
                    "headless": False,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                "wait_timeout": 20,
                "retry_count": 3
            }
            self.save_config(default_config)
            return default_config
            
    def save_config(self, config):
        """設定ファイル保存"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
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
            
    def find_booking_form(self):
        """予約フォームを探す"""
        try:
            # 予約ボタンやフォーム要素を探す
            # 実際のページ構造に応じて調整が必要
            booking_elements = [
                "//a[contains(text(), '予約')]",
                "//button[contains(text(), '予約')]",
                "//input[@type='submit']",
                "//a[contains(@href, 'booking')]",
                "//a[contains(@href, 'reserve')]",
                "//button[contains(text(), 'Web予約')]",
                "//a[contains(text(), 'Web予約')]"
            ]
            
            for xpath in booking_elements:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    self.logger.info(f"予約要素を発見: {xpath}")
                    return element
                except (NoSuchElementException, TimeoutException):
                    continue
                    
            self.logger.warning("予約フォームが見つかりませんでした")
            return None
            
        except Exception as e:
            self.logger.error(f"フォーム検索エラー: {e}")
            return None
            
    def fill_booking_form(self):
        """予約フォームに情報を入力"""
        try:
            # 患者情報の入力
            patient_info = self.config["patient_info"]
            
            # 名前入力フィールドを探す
            name_fields = [
                "//input[@name='name']",
                "//input[@placeholder='お名前']",
                "//input[@id='name']",
                "//input[@name='patient_name']",
                "//input[@name='full_name']"
            ]
            
            for xpath in name_fields:
                try:
                    name_field = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    name_field.clear()
                    name_field.send_keys(patient_info["name"])
                    self.logger.info("患者名を入力しました")
                    break
                except (NoSuchElementException, TimeoutException):
                    continue
                    
            # 電話番号入力
            phone_fields = [
                "//input[@name='phone']",
                "//input[@placeholder='電話番号']",
                "//input[@id='phone']",
                "//input[@name='tel']",
                "//input[@name='telephone']"
            ]
            
            for xpath in phone_fields:
                try:
                    phone_field = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    phone_field.clear()
                    phone_field.send_keys(patient_info["phone"])
                    self.logger.info("電話番号を入力しました")
                    break
                except (NoSuchElementException, TimeoutException):
                    continue
                    
            # メールアドレス入力
            email_fields = [
                "//input[@name='email']",
                "//input[@type='email']",
                "//input[@placeholder='メールアドレス']",
                "//input[@name='mail']"
            ]
            
            for xpath in email_fields:
                try:
                    email_field = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    email_field.clear()
                    email_field.send_keys(patient_info["email"])
                    self.logger.info("メールアドレスを入力しました")
                    break
                except (NoSuchElementException, TimeoutException):
                    continue
                    
            return True
            
        except Exception as e:
            self.logger.error(f"フォーム入力エラー: {e}")
            return False
            
    def submit_booking(self):
        """予約を送信"""
        try:
            # 送信ボタンを探す
            submit_buttons = [
                "//button[@type='submit']",
                "//input[@type='submit']",
                "//button[contains(text(), '送信')]",
                "//button[contains(text(), '予約')]",
                "//button[contains(text(), '確認')]",
                "//input[@value='送信']",
                "//input[@value='予約']"
            ]
            
            for xpath in submit_buttons:
                try:
                    submit_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    submit_btn.click()
                    self.logger.info("予約フォームを送信しました")
                    
                    # 送信完了まで待機
                    time.sleep(5)
                    return True
                    
                except (NoSuchElementException, TimeoutException):
                    continue
                    
            self.logger.warning("送信ボタンが見つかりませんでした")
            return False
            
        except Exception as e:
            self.logger.error(f"送信エラー: {e}")
            return False
            
    def take_screenshot(self, filename=None):
        """スクリーンショット取得"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                
            self.driver.save_screenshot(filename)
            self.logger.info(f"スクリーンショットを保存しました: {filename}")
            
        except Exception as e:
            self.logger.error(f"スクリーンショット保存エラー: {e}")
            
    def execute_booking(self):
        """予約実行のメイン処理"""
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
                
                # 予約フォームを探す
                booking_element = self.find_booking_form()
                if not booking_element:
                    raise Exception("予約フォームが見つかりませんでした")
                    
                # フォームをクリック
                booking_element.click()
                time.sleep(3)
                
                # フォーム入力
                if not self.fill_booking_form():
                    raise Exception("フォーム入力に失敗しました")
                    
                # 送信前のスクリーンショット
                self.take_screenshot("before_submit.png")
                
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
    automation = HospitalBookingAutomation()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # 一度だけ実行
        automation.run_once()
    else:
        # スケジューラー実行
        automation.run_scheduler()

if __name__ == "__main__":
    main()
