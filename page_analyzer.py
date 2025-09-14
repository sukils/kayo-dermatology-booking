#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
かよ皮膚科予約ページ分析スクリプト
予約ページの構造を詳しく分析して、正しい要素を特定します
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

class PageAnalyzer:
    def __init__(self):
        """初期化"""
        self.driver = None
        self.hospital_url = "https://www5.tandt.co.jp/cti/hs713/index_p.html"
        
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
            self.driver.get(self.hospital_url)
            time.sleep(5)
            
            # ページタイトル
            print(f"ページタイトル: {self.driver.title}")
            
            # すべてのリンクを取得
            links = self.driver.find_elements(By.TAG_NAME, "a")
            print(f"\nリンクの数: {len(links)}")
            
            for i, link in enumerate(links[:20]):  # 最初の20個のみ表示
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    if text and href:
                        print(f"{i+1}. テキスト: '{text}' -> URL: {href}")
                except:
                    continue
                    
            # すべてのボタンを取得
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"\nボタンの数: {len(buttons)}")
            
            for i, button in enumerate(buttons):
                try:
                    text = button.text.strip()
                    button_type = button.get_attribute("type")
                    if text:
                        print(f"{i+1}. テキスト: '{text}' -> タイプ: {button_type}")
                except:
                    continue
                    
            # 予約関連の要素を探す
            print("\n=== 予約関連要素の検索 ===")
            booking_keywords = ["予約", "reserve", "booking", "appointment", "受診", "診察"]
            
            for keyword in booking_keywords:
                try:
                    # テキストを含む要素を検索
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                    if elements:
                        print(f"'{keyword}'を含む要素: {len(elements)}個")
                        for elem in elements[:3]:  # 最初の3個のみ表示
                            tag = elem.tag_name
                            text = elem.text.strip()[:50]  # 最初の50文字
                            print(f"  - {tag}: {text}")
                except:
                    continue
                    
        except Exception as e:
            print(f"メインページ分析エラー: {e}")
            
    def take_screenshot(self, filename):
        """スクリーンショット取得"""
        try:
            self.driver.save_screenshot(filename)
            print(f"スクリーンショットを保存しました: {filename}")
        except Exception as e:
            print(f"スクリーンショット保存エラー: {e}")
            
    def analyze_page_source(self):
        """ページソースの分析"""
        print("\n=== ページソースの分析 ===")
        
        try:
            page_source = self.driver.page_source
            
            # 予約関連のキーワードを検索
            keywords = ["予約", "reserve", "booking", "appointment", "患者番号", "patient", "number"]
            
            for keyword in keywords:
                if keyword in page_source:
                    count = page_source.count(keyword)
                    print(f"'{keyword}'の出現回数: {count}")
                    
            # フォーム要素を検索
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            print(f"\nフォームの数: {len(forms)}")
            
            for i, form in enumerate(forms):
                try:
                    action = form.get_attribute("action")
                    method = form.get_attribute("method")
                    print(f"フォーム{i+1}: action={action}, method={method}")
                    
                    # フォーム内の入力要素
                    inputs = form.find_elements(By.TAG_NAME, "input")
                    print(f"  入力要素: {len(inputs)}個")
                    
                    for inp in inputs:
                        inp_type = inp.get_attribute("type")
                        inp_name = inp.get_attribute("name")
                        inp_id = inp.get_attribute("id")
                        inp_placeholder = inp.get_attribute("placeholder")
                        print(f"    - タイプ: {inp_type}, 名前: {inp_name}, ID: {inp_id}, プレースホルダー: {inp_placeholder}")
                        
                except Exception as e:
                    print(f"フォーム{i+1}の分析エラー: {e}")
                    
        except Exception as e:
            print(f"ページソース分析エラー: {e}")
            
    def run_analysis(self):
        """分析実行"""
        try:
            print("かよ皮膚科予約ページの分析を開始します...")
            
            # ドライバー設定
            self.setup_driver()
            
            # メインページの分析
            self.analyze_main_page()
            
            # スクリーンショット取得
            self.take_screenshot("main_page_analysis.png")
            
            # ページソースの分析
            self.analyze_page_source()
            
            print("\n分析が完了しました。")
            
        except Exception as e:
            print(f"分析エラー: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
                print("ブラウザを終了しました")

def main():
    """メイン関数"""
    analyzer = PageAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
