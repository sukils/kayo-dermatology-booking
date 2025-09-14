#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
かよ皮膚科予約システム詳細分析スクリプト v2
実際の予約システムページの構造を詳しく分析します
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class DetailedPageAnalyzer:
    def __init__(self):
        """初期化"""
        self.driver = None
        self.main_url = "https://www5.tandt.co.jp/cti/hs713/index_p.html"
        self.booking_url = "https://www4.tandt.co.jp/rsvsys/jsp/JobDispatcher.jsp?agent=RSV1&jobid=rsvmod000&callback=0&gc=KQhkYPLO&portal=index_P.html&nj=rsvmodG01&"
        
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
            
    def analyze_main_page(self):
        """メインページの分析"""
        print("\n=== メインページの分析 ===")
        
        try:
            self.driver.get(self.main_url)
            time.sleep(5)
            
            print(f"ページタイトル: {self.driver.title}")
            
            # 予約関連のリンクを詳しく分析
            print("\n=== 予約関連リンクの詳細分析 ===")
            
            # 順番受付(当日外来)のリンクを探す
            try:
                same_day_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), '順番受付')]")
                for i, link in enumerate(same_day_links):
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    print(f"順番受付リンク{i+1}: '{text}' -> {href}")
                    
                    # リンクの親要素も確認
                    parent = link.find_element(By.XPATH, "..")
                    print(f"  親要素: {parent.tag_name}, クラス: {parent.get_attribute('class')}")
                    
            except Exception as e:
                print(f"順番受付リンク分析エラー: {e}")
                
            # 予約の確認・取消のリンクを探す
            try:
                booking_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), '予約の確認・取消')]")
                for i, link in enumerate(booking_links):
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    print(f"予約確認リンク{i+1}: '{text}' -> {href}")
                    
            except Exception as e:
                print(f"予約確認リンク分析エラー: {e}")
                
        except Exception as e:
            print(f"メインページ分析エラー: {e}")
            
    def analyze_booking_system(self):
        """予約システムページの分析"""
        print("\n=== 予約システムページの分析 ===")
        
        try:
            print(f"予約システムページに移動中: {self.booking_url}")
            self.driver.get(self.booking_url)
            time.sleep(5)
            
            print(f"ページタイトル: {self.driver.title}")
            
            # ページの基本情報
            print(f"現在のURL: {self.driver.current_url}")
            
            # すべてのフォーム要素を検索
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            print(f"\nフォームの数: {len(forms)}")
            
            for i, form in enumerate(forms):
                try:
                    action = form.get_attribute("action")
                    method = form.get_attribute("method")
                    form_id = form.get_attribute("id")
                    form_class = form.get_attribute("class")
                    print(f"フォーム{i+1}: action={action}, method={method}, id={form_id}, class={form_class}")
                    
                    # フォーム内の入力要素
                    inputs = form.find_elements(By.TAG_NAME, "input")
                    print(f"  入力要素: {len(inputs)}個")
                    
                    for inp in inputs:
                        inp_type = inp.get_attribute("type")
                        inp_name = inp.get_attribute("name")
                        inp_id = inp.get_attribute("id")
                        inp_placeholder = inp.get_attribute("placeholder")
                        inp_value = inp.get_attribute("value")
                        print(f"    - タイプ: {inp_type}, 名前: {inp_name}, ID: {inp_id}, プレースホルダー: {inp_placeholder}, 値: {inp_value}")
                        
                except Exception as e:
                    print(f"フォーム{i+1}の分析エラー: {e}")
                    
            # すべてのボタン要素を検索
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"\nボタンの数: {len(buttons)}")
            
            for i, button in enumerate(buttons):
                try:
                    text = button.text.strip()
                    button_type = button.get_attribute("type")
                    button_id = button.get_attribute("id")
                    button_class = button.get_attribute("class")
                    if text:
                        print(f"ボタン{i+1}: テキスト='{text}', タイプ={button_type}, ID={button_id}, クラス={button_class}")
                except Exception as e:
                    print(f"ボタン{i+1}の分析エラー: {e}")
                    
            # 患者番号関連の要素を検索
            print("\n=== 患者番号関連要素の検索 ===")
            patient_keywords = ["患者番号", "患者No", "患者ID", "patient", "number", "id", "no"]
            
            for keyword in patient_keywords:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                    if elements:
                        print(f"'{keyword}'を含む要素: {len(elements)}個")
                        for elem in elements[:3]:
                            tag = elem.tag_name
                            text = elem.text.strip()[:50]
                            print(f"  - {tag}: {text}")
                except:
                    continue
                    
            # 入力フィールドを詳しく検索
            print("\n=== 入力フィールドの詳細分析 ===")
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            print(f"全入力要素: {len(all_inputs)}個")
            
            for i, inp in enumerate(all_inputs):
                try:
                    inp_type = inp.get_attribute("type")
                    inp_name = inp.get_attribute("name")
                    inp_id = inp.get_attribute("id")
                    inp_placeholder = inp.get_attribute("placeholder")
                    inp_value = inp.get_attribute("value")
                    inp_class = inp.get_attribute("class")
                    
                    # 患者番号関連の可能性がある要素を特定
                    is_patient_related = False
                    if any(keyword in str(inp_name).lower() for keyword in ["patient", "no", "id", "number"]):
                        is_patient_related = True
                    if any(keyword in str(inp_placeholder).lower() for keyword in ["患者", "番号", "no", "id"]):
                        is_patient_related = True
                        
                    if is_patient_related:
                        print(f"患者番号関連の可能性: タイプ={inp_type}, 名前={inp_name}, ID={inp_id}, プレースホルダー={inp_placeholder}")
                    else:
                        print(f"入力要素{i+1}: タイプ={inp_type}, 名前={inp_name}, ID={inp_id}, プレースホルダー={inp_placeholder}")
                        
                except Exception as e:
                    print(f"入力要素{i+1}の分析エラー: {e}")
                    
        except Exception as e:
            print(f"予約システム分析エラー: {e}")
            
    def take_screenshots(self):
        """スクリーンショット取得"""
        try:
            # メインページのスクリーンショット
            self.driver.get(self.main_url)
            time.sleep(3)
            self.driver.save_screenshot("main_page_detailed.png")
            print("メインページのスクリーンショットを保存しました: main_page_detailed.png")
            
            # 予約システムページのスクリーンショット
            self.driver.get(self.booking_url)
            time.sleep(5)
            self.driver.save_screenshot("booking_system_page.png")
            print("予約システムページのスクリーンショットを保存しました: booking_system_page.png")
            
        except Exception as e:
            print(f"スクリーンショット保存エラー: {e}")
            
    def run_detailed_analysis(self):
        """詳細分析実行"""
        try:
            print("かよ皮膚科予約システムの詳細分析を開始します...")
            
            # ドライバー設定
            self.setup_driver()
            
            # メインページの分析
            self.analyze_main_page()
            
            # 予約システムページの分析
            self.analyze_booking_system()
            
            # スクリーンショット取得
            self.take_screenshots()
            
            print("\n詳細分析が完了しました。")
            
        except Exception as e:
            print(f"詳細分析エラー: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
                print("ブラウザを終了しました")

def main():
    """メイン関数"""
    analyzer = DetailedPageAnalyzer()
    analyzer.run_detailed_analysis()

if __name__ == "__main__":
    main()
