#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
かよ皮膚科予約フローインタラクティブ追跡ツール
実際の予約プロセスを手動で追跡して、正しい要素を特定します
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

class InteractiveAnalyzer:
    def __init__(self):
        """初期化"""
        self.driver = None
        self.main_url = "https://www5.tandt.co.jp/cti/hs713/index_p.html"
        self.current_page = "main"
        
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
            
    def start_main_page(self):
        """メインページを開始"""
        try:
            print(f"\n=== メインページに移動中 ===")
            self.driver.get(self.main_url)
            time.sleep(3)
            
            print(f"ページタイトル: {self.driver.title}")
            print(f"現在のURL: {self.driver.current_url}")
            
            # 予約関連のリンクを表示
            self.show_booking_links()
            
            self.current_page = "main"
            
        except Exception as e:
            print(f"メインページ移動エラー: {e}")
            
    def show_booking_links(self):
        """予約関連のリンクを表示"""
        try:
            print("\n=== 予約関連リンク ===")
            
            # 順番受付(当日外来)のリンク
            same_day_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), '順番受付')]")
            for i, link in enumerate(same_day_links):
                href = link.get_attribute("href")
                text = link.text.strip()
                print(f"{i+1}. 順番受付: '{text}' -> {href}")
                
            # 予約の確認・取消のリンク
            booking_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), '予約の確認・取消')]")
            for i, link in enumerate(booking_links):
                href = link.get_attribute("href")
                text = link.text.strip()
                print(f"{len(same_day_links)+i+1}. 予約確認: '{text}' -> {href}")
                
            # 現在のお呼出状況のリンク
            status_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), '現在のお呼出状況')]")
            for i, link in enumerate(status_links):
                href = link.get_attribute("href")
                text = link.text.strip()
                print(f"{len(same_day_links)+len(booking_links)+i+1}. 呼出状況: '{text}' -> {href}")
                
        except Exception as e:
            print(f"リンク表示エラー: {e}")
            
    def click_link_by_number(self, link_number):
        """指定された番号のリンクをクリック"""
        try:
            print(f"\n=== リンク{link_number}をクリック中 ===")
            
            # すべての予約関連リンクを取得
            all_links = []
            
            # 順番受付リンク
            same_day_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), '順番受付')]")
            all_links.extend(same_day_links)
            
            # 予約確認リンク
            booking_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), '予約の確認・取消')]")
            all_links.extend(booking_links)
            
            # 呼出状況リンク
            status_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), '現在のお呼出状況')]")
            all_links.extend(status_links)
            
            if 1 <= link_number <= len(all_links):
                link = all_links[link_number - 1]
                href = link.get_attribute("href")
                text = link.text.strip()
                
                print(f"クリックするリンク: '{text}' -> {href}")
                
                # リンクをクリック
                link.click()
                time.sleep(5)
                
                print(f"新しいページタイトル: {self.driver.title}")
                print(f"新しいURL: {self.driver.current_url}")
                
                # 新しいページの要素を分析
                self.analyze_current_page()
                
                return True
            else:
                print(f"エラー: リンク番号{link_number}は無効です。1から{len(all_links)}の間で指定してください。")
                return False
                
        except Exception as e:
            print(f"リンククリックエラー: {e}")
            return False
            
    def analyze_current_page(self):
        """現在のページを分析"""
        try:
            print(f"\n=== 現在のページの分析 ===")
            
            # フォーム要素
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            print(f"フォームの数: {len(forms)}")
            
            for i, form in enumerate(forms):
                try:
                    action = form.get_attribute("action")
                    method = form.get_attribute("method")
                    form_id = form.get_attribute("id")
                    print(f"フォーム{i+1}: action={action}, method={method}, id={form_id}")
                    
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
                    
            # 入力要素（フォーム外も含む）
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            print(f"\n全入力要素: {len(all_inputs)}個")
            
            for i, inp in enumerate(all_inputs):
                try:
                    inp_type = inp.get_attribute("type")
                    inp_name = inp.get_attribute("name")
                    inp_id = inp.get_attribute("id")
                    inp_placeholder = inp.get_attribute("placeholder")
                    inp_value = inp.get_attribute("value")
                    
                    # 患者番号関連の可能性をチェック
                    is_patient_related = False
                    if any(keyword in str(inp_name).lower() for keyword in ["patient", "no", "id", "number"]):
                        is_patient_related = True
                    if any(keyword in str(inp_placeholder).lower() for keyword in ["患者", "番号", "no", "id"]):
                        is_patient_related = True
                        
                    if is_patient_related:
                        print(f"  {i+1}. [患者番号関連] タイプ={inp_type}, 名前={inp_name}, ID={inp_id}, プレースホルダー={inp_placeholder}")
                    else:
                        print(f"  {i+1}. タイプ={inp_type}, 名前={inp_name}, ID={inp_id}, プレースホルダー={inp_placeholder}")
                        
                except Exception as e:
                    print(f"入力要素{i+1}の分析エラー: {e}")
                    
            # ボタン要素
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"\nボタンの数: {len(buttons)}")
            
            for i, button in enumerate(buttons):
                try:
                    text = button.text.strip()
                    button_type = button.get_attribute("type")
                    button_id = button.get_attribute("id")
                    if text:
                        print(f"  {i+1}. テキスト='{text}', タイプ={button_type}, ID={button_id}")
                except Exception as e:
                    print(f"ボタン{i+1}の分析エラー: {e}")
                    
        except Exception as e:
            print(f"ページ分析エラー: {e}")
            
    def take_screenshot(self, filename=None):
        """スクリーンショット取得"""
        try:
            if filename is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"interactive_analysis_{timestamp}.png"
                
            self.driver.save_screenshot(filename)
            print(f"スクリーンショットを保存しました: {filename}")
            
        except Exception as e:
            print(f"スクリーンショット保存エラー: {e}")
            
    def show_menu(self):
        """メニューを表示"""
        print("\n" + "="*50)
        print("かよ皮膚科予約フロー分析ツール")
        print("="*50)
        print("1. メインページに移動")
        print("2. 現在のページを分析")
        print("3. スクリーンショット取得")
        print("4. リンクをクリック（番号指定）")
        print("5. 前のページに戻る")
        print("6. 終了")
        print("="*50)
        
    def run_interactive(self):
        """インタラクティブ実行"""
        try:
            print("かよ皮膚科予約フロー分析ツールを開始します...")
            
            # ドライバー設定
            self.setup_driver()
            
            # メインページを開始
            self.start_main_page()
            
            while True:
                self.show_menu()
                choice = input("選択してください (1-6): ").strip()
                
                if choice == "1":
                    self.start_main_page()
                    
                elif choice == "2":
                    self.analyze_current_page()
                    
                elif choice == "3":
                    self.take_screenshot()
                    
                elif choice == "4":
                    try:
                        link_num = int(input("クリックするリンクの番号を入力してください: "))
                        self.click_link_by_number(link_num)
                    except ValueError:
                        print("エラー: 有効な番号を入力してください。")
                        
                elif choice == "5":
                    try:
                        self.driver.back()
                        time.sleep(3)
                        print("前のページに戻りました。")
                        print(f"現在のページ: {self.driver.title}")
                    except Exception as e:
                        print(f"戻るエラー: {e}")
                        
                elif choice == "6":
                    print("分析ツールを終了します。")
                    break
                    
                else:
                    print("無効な選択です。1から6の間で選択してください。")
                    
        except Exception as e:
            print(f"実行エラー: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
                print("ブラウザを終了しました")

def main():
    """メイン関数"""
    analyzer = InteractiveAnalyzer()
    analyzer.run_interactive()

if __name__ == "__main__":
    main()
