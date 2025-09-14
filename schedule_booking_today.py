#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
今日の9時15分に予約を実行するスケジュールプログラム
"""

import schedule
import time
import logging
from datetime import datetime
from hospital_booking_automation_v3 import HospitalBookingAutomationV3

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/schedule_booking.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def execute_booking():
    """予約を実行する関数"""
    try:
        logger.info("=== 予約実行開始 ===")
        logger.info(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 予約プログラムを実行
        automation = HospitalBookingAutomationV3()
        result = automation.execute_lightweight_booking()
        
        if result:
            logger.info("✅ 予約が成功しました！")
        else:
            logger.warning("❌ 予約に失敗しました")
            
        logger.info("=== 予約実行終了 ===")
        
    except Exception as e:
        logger.error(f"予約実行中にエラーが発生しました: {e}")

def main():
    """メイン処理"""
    logger.info("予約スケジューラーを開始します")
    
    # 今日の9時15分に予約を実行
    schedule.every().day.at("09:15").do(execute_booking)
    
    logger.info("今日の9時15分に予約を実行するスケジュールを設定しました")
    logger.info("スケジューラーを実行中... (Ctrl+Cで停止)")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにチェック
    except KeyboardInterrupt:
        logger.info("スケジューラーを停止しました")

if __name__ == "__main__":
    main()
