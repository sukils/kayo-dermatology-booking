#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
かよ皮膚科平日AM自動分析ツール
平日の午前中に自動で予約システムを分析します
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

class AutoAnalyzer:
    def __init__(self):
        """初期化"""
        self.driver = None
        self.main_url = "https://www5.tandt.co.jp/cti/hs713/index_p.html"
        self.setup_logging()
        
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
                logging.FileHandler('auto_analyzer.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def check_weekday_morning(self):
        """平日・土曜午前中かチェック"""
        now = datetime.now()
        weekday = now.strftime("%A").lower()
        
        # 日曜日はスキップ
        if weekday == "sunday":
            self.logger.info(f"{weekday}は分析をスキップします")
            return False
            
        # 平日・土曜の午前中（9:15-12:00）かチェック
        if (9 <= now.hour < 12) and (now.hour > 9 or (now.hour == 9 and now.minute >= 15)):
            self.logger.info(f"{weekday} {now.hour}:{now.minute} - 平日・土曜午前中、分析を実行します")
            return True
        else:
            self.logger.info(f"{weekday} {now.hour}:{now.minute} - 午前中ではありません（9:15開始）")
            return False
            
    def setup_driver(self):
        """Chromeドライバー設定"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
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
            
    def analyze_booking_system(self):
        """予約システムの分析"""
        try:
            self.logger.info("=== 平日・土曜AM自動分析開始 ===")
            
            # 平日・土曜午前中かチェック
            if not self.check_weekday_morning():
                return False
                
            # ドライバー設定
            self.setup_driver()
            
            # メインページに移動
            self.logger.info(f"メインページに移動中: {self.main_url}")
            self.driver.get(self.main_url)
            time.sleep(5)
            
            # ページ情報取得
            page_title = self.driver.title
            current_url = self.driver.current_url
            self.logger.info(f"ページタイトル: {page_title}")
            self.logger.info(f"現在のURL: {current_url}")
            
            # 予約関連リンクの検索
            self.search_booking_links()
            
            # ページ要素の詳細分析
            self.analyze_page_elements()
            
            # スクリーンショット取得
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.driver.save_screenshot(f"auto_analysis_{timestamp}.png")
            self.logger.info(f"スクリーンショットを保存しました: auto_analysis_{timestamp}.png")
            
            # 分析結果の保存
            self.save_analysis_results(page_title, current_url, timestamp)
            
            self.logger.info("=== 平日・土曜AM自動分析完了 ===")
            return True
            
        except Exception as e:
            self.logger.error(f"分析エラー: {e}")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("ブラウザを終了しました")
                
    def search_booking_links(self):
        """予約関連リンクを検索"""
        try:
            self.logger.info("=== 予約関連リンクの検索 ===")
            
            # 順番受付(当日外来)のリンク
            same_day_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), '順番受付')]")
            self.logger.info(f"順番受付リンク: {len(same_day_links)}個")
            
            for i, link in enumerate(same_day_links):
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    self.logger.info(f"  {i+1}. '{text}' -> {href}")
                except Exception as e:
                    self.logger.error(f"    リンク{i+1}の詳細取得エラー: {e}")
                    
            # 予約の確認・取消のリンク
            booking_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), '予約の確認・取消')]")
            self.logger.info(f"予約確認リンク: {len(booking_links)}個")
            
            for i, link in enumerate(booking_links):
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    self.logger.info(f"  {i+1}. '{text}' -> {href}")
                except Exception as e:
                    self.logger.error(f"    リンク{i+1}の詳細取得エラー: {e}")
                    
            # 現在のお呼出状況のリンク
            status_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), '現在のお呼出状況')]")
            self.logger.info(f"呼出状況リンク: {len(status_links)}個")
            
            for i, link in enumerate(status_links):
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    self.logger.info(f"  {i+1}. '{text}' -> {href}")
                except Exception as e:
                    self.logger.error(f"    リンク{i+1}の詳細取得エラー: {e}")
                    
            # 全リンクの合計
            total_links = len(same_day_links) + len(booking_links) + len(status_links)
            self.logger.info(f"総予約関連リンク数: {total_links}個")
            
            if total_links == 0:
                self.logger.warning("⚠️  予約関連リンクが見つかりません。")
                self.logger.warning("    - 受付時間外の可能性")
                self.logger.warning("    - ページの読み込みが完了していない可能性")
                self.logger.warning("    - システムメンテナンス中の可能性")
            else:
                self.logger.info("✅ 予約関連リンクが正常に表示されています。")
                
        except Exception as e:
            self.logger.error(f"リンク検索エラー: {e}")
            
    def analyze_page_elements(self):
        """ページ要素の詳細分析"""
        try:
            self.logger.info("=== ページ要素の詳細分析 ===")
            
            # フォーム要素
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            self.logger.info(f"フォームの数: {len(forms)}")
            
            for i, form in enumerate(forms):
                try:
                    action = form.get_attribute("action")
                    method = form.get_attribute("method")
                    form_id = form.get_attribute("id")
                    form_class = form.get_attribute("class")
                    self.logger.info(f"フォーム{i+1}: action={action}, method={method}, id={form_id}, class={form_class}")
                    
                    # フォーム内の入力要素
                    inputs = form.find_elements(By.TAG_NAME, "input")
                    self.logger.info(f"  入力要素: {len(inputs)}個")
                    
                    for inp in inputs:
                        inp_type = inp.get_attribute("type")
                        inp_name = inp.get_attribute("name")
                        inp_id = inp.get_attribute("id")
                        inp_placeholder = inp.get_attribute("placeholder")
                        self.logger.info(f"    - タイプ: {inp_type}, 名前: {inp_name}, ID: {inp_id}, プレースホルダー: {inp_placeholder}")
                        
                except Exception as e:
                    self.logger.error(f"フォーム{i+1}の分析エラー: {e}")
                    
            # 入力要素（フォーム外も含む）
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            self.logger.info(f"全入力要素: {len(all_inputs)}個")
            
            for i, inp in enumerate(all_inputs):
                try:
                    inp_type = inp.get_attribute("type")
                    inp_name = inp.get_attribute("name")
                    inp_id = inp.get_attribute("id")
                    inp_placeholder = inp.get_attribute("placeholder")
                    
                    # 患者番号関連の可能性をチェック
                    is_patient_related = False
                    if any(keyword in str(inp_name).lower() for keyword in ["patient", "no", "id", "number"]):
                        is_patient_related = True
                    if any(keyword in str(inp_placeholder).lower() for keyword in ["患者", "番号", "no", "id"]):
                        is_patient_related = True
                        
                    if is_patient_related:
                        self.logger.info(f"  {i+1}. [患者番号関連] タイプ={inp_type}, 名前={inp_name}, ID={inp_id}, プレースホルダー={inp_placeholder}")
                    else:
                        self.logger.info(f"  {i+1}. タイプ={inp_type}, 名前={inp_name}, ID={inp_id}, プレースホルダー={inp_placeholder}")
                        
                except Exception as e:
                    self.logger.error(f"入力要素{i+1}の分析エラー: {e}")
                    
            # ボタン要素
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            self.logger.info(f"ボタンの数: {len(buttons)}")
            
            for i, button in enumerate(buttons):
                try:
                    text = button.text.strip()
                    button_type = button.get_attribute("type")
                    button_id = button.get_attribute("id")
                    if text:
                        self.logger.info(f"  {i+1}. テキスト='{text}', タイプ={button_type}, ID={button_id}")
                except Exception as e:
                    self.logger.error(f"ボタン{i+1}の分析エラー: {e}")
                    
        except Exception as e:
            self.logger.error(f"ページ要素分析エラー: {e}")
            
    def save_analysis_results(self, page_title, current_url, timestamp):
        """分析結果を保存"""
        try:
            results = {
                "timestamp": timestamp,
                "page_title": page_title,
                "current_url": current_url,
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "analysis_time": datetime.now().strftime("%H:%M:%S"),
                "weekday": datetime.now().strftime("%A")
            }
            
            # 結果をJSONファイルに保存
            filename = f"analysis_results_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"分析結果を保存しました: {filename}")
            
        except Exception as e:
            self.logger.error(f"結果保存エラー: {e}")
            
    def schedule_analysis(self):
        """分析スケジュール設定"""
        # 平日・土曜9:15に分析を実行
        schedule.every().monday.at("09:15").do(self.analyze_booking_system)
        schedule.every().tuesday.at("09:15").do(self.analyze_booking_system)
        schedule.every().wednesday.at("09:15").do(self.analyze_booking_system)
        schedule.every().thursday.at("09:15").do(self.analyze_booking_system)
        schedule.every().friday.at("09:15").do(self.analyze_booking_system)
        schedule.every().saturday.at("09:15").do(self.analyze_booking_system)
        
        self.logger.info("平日・土曜9:15に自動分析をスケジュールしました")
        
    def run_scheduler(self):
        """スケジューラー実行"""
        self.logger.info("平日・土曜AM自動分析スケジューラーを開始しました")
        self.schedule_analysis()
        
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
        self.logger.info("一度だけ分析を実行します")
        return self.analyze_booking_system()

def main():
    """メイン関数"""
    analyzer = AutoAnalyzer()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # 一度だけ実行
        analyzer.run_once()
    else:
        # スケジューラー実行
        analyzer.run_scheduler()

if __name__ == "__main__":
    main()
