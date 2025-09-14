#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
かよ皮膚科受付時間対応分析ツール
受付時間内でのみ予約リンクが表示される仕様に対応
"""

import time
import json
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class TimingAnalyzer:
    def __init__(self):
        """初期化"""
        self.driver = None
        self.main_url = "https://www5.tandt.co.jp/cti/hs713/index_p.html"
        
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
        
    def setup_driver(self):
        """Chromeドライバー設定"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # ChromeDriverを自動でダウンロード・管理
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(10)
            print("Chromeドライバーの初期化が完了しました")
            
        except Exception as e:
            print(f"ドライバー初期化エラー: {e}")
            raise
            
    def check_booking_availability(self):
        """受付可能時間をチェック"""
        now = datetime.now()
        weekday = now.strftime("%A").lower()
        
        # 日本語の曜日名に変換
        weekday_jp = {
            "monday": "月曜日",
            "tuesday": "火曜日", 
            "wednesday": "水曜日",
            "thursday": "木曜日",
            "friday": "金曜日",
            "saturday": "土曜日",
            "sunday": "日曜日"
        }
        
        print(f"\n=== 現在時刻: {now.strftime('%Y年%m月%d日 %H:%M:%S')} ===")
        print(f"曜日: {weekday_jp.get(weekday, weekday)}")
        
        if weekday in self.booking_hours:
            hours = self.booking_hours[weekday]
            print(f"診察時間: 午前 {hours['morning']}, 午後 {hours['afternoon']}")
            print(f"Web予約受付: {hours['web']}")
            
            # Web予約受付可能かチェック
            if hours['web'] == "休診":
                print("❌ 本日はWeb予約受付不可（休診日）")
                return False
            elif hours['web'] == "12:00まで":
                if now.hour < 12:
                    print("✅ Web予約受付可能（午前中）")
                    return True
                else:
                    print("❌ Web予約受付終了（午前のみ）")
                    return False
            else:  # 12:00-16:00
                if 12 <= now.hour < 16:
                    print("✅ Web予約受付可能（午後）")
                    return True
                elif now.hour < 12:
                    print("⏳ Web予約受付開始まで待機中（12:00開始）")
                    return False
                else:
                    print("❌ Web予約受付終了（16:00まで）")
                    return False
        else:
            print("❌ 不明な曜日")
            return False
            
    def wait_for_booking_time(self):
        """受付時間まで待機"""
        now = datetime.now()
        weekday = now.strftime("%A").lower()
        
        if weekday in ["saturday", "sunday"]:
            print("土日は受付不可です。平日に実行してください。")
            return False
            
        # 次の受付時間を計算
        if now.hour < 12:
            # 12:00まで待機
            target_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
            wait_seconds = (target_time - now).total_seconds()
            
            if wait_seconds > 0:
                print(f"⏰ 受付開始時刻（12:00）まで {int(wait_seconds/60)}分 待機します...")
                time.sleep(wait_seconds)
                print("✅ 受付時間開始！")
                return True
        else:
            print("✅ 現在受付時間内です")
            return True
            
        return False
        
    def analyze_page_with_timing(self):
        """受付時間を考慮したページ分析"""
        try:
            print("\n=== 受付時間チェック ===")
            
            # 受付可能かチェック
            if not self.check_booking_availability():
                print("\n受付時間外のため、予約リンクは表示されません。")
                print("受付時間内に実行してください。")
                return
                
            # 受付時間まで待機が必要かチェック
            if not self.wait_for_booking_time():
                return
                
            print("\n=== ページ分析開始 ===")
            
            # メインページに移動
            self.driver.get(self.main_url)
            time.sleep(5)
            
            print(f"ページタイトル: {self.driver.title}")
            print(f"現在のURL: {self.driver.current_url}")
            
            # 予約関連リンクの検索
            self.search_booking_links()
            
            # スクリーンショット取得
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.driver.save_screenshot(f"booking_analysis_{timestamp}.png")
            print(f"スクリーンショットを保存しました: booking_analysis_{timestamp}.png")
            
        except Exception as e:
            print(f"ページ分析エラー: {e}")
            
    def search_booking_links(self):
        """予約関連リンクを検索"""
        try:
            print("\n=== 予約関連リンクの検索 ===")
            
            # 順番受付(当日外来)のリンク
            same_day_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), '順番受付')]")
            print(f"順番受付リンク: {len(same_day_links)}個")
            
            for i, link in enumerate(same_day_links):
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    print(f"  {i+1}. '{text}' -> {href}")
                except Exception as e:
                    print(f"    リンク{i+1}の詳細取得エラー: {e}")
                    
            # 予約の確認・取消のリンク
            booking_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), '予約の確認・取消')]")
            print(f"予約確認リンク: {len(booking_links)}個")
            
            for i, link in enumerate(booking_links):
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    print(f"  {i+1}. '{text}' -> {href}")
                except Exception as e:
                    print(f"    リンク{i+1}の詳細取得エラー: {e}")
                    
            # 現在のお呼出状況のリンク
            status_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), '現在のお呼出状況')]")
            print(f"呼出状況リンク: {len(status_links)}個")
            
            for i, link in enumerate(status_links):
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    print(f"  {i+1}. '{text}' -> {href}")
                except Exception as e:
                    print(f"    リンク{i+1}の詳細取得エラー: {e}")
                    
            # 全リンクの合計
            total_links = len(same_day_links) + len(booking_links) + len(status_links)
            print(f"\n総予約関連リンク数: {total_links}個")
            
            if total_links == 0:
                print("⚠️  予約関連リンクが見つかりません。")
                print("    - 受付時間外の可能性")
                print("    - ページの読み込みが完了していない可能性")
                print("    - システムメンテナンス中の可能性")
            else:
                print("✅ 予約関連リンクが正常に表示されています。")
                
        except Exception as e:
            print(f"リンク検索エラー: {e}")
            
    def run_analysis(self):
        """分析実行"""
        try:
            print("かよ皮膚科受付時間対応分析ツールを開始します...")
            
            # ドライバー設定
            self.setup_driver()
            
            # 受付時間を考慮したページ分析
            self.analyze_page_with_timing()
            
            print("\n分析が完了しました。")
            
        except Exception as e:
            print(f"実行エラー: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
                print("ブラウザを終了しました")

def main():
    """メイン関数"""
    analyzer = TimingAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
