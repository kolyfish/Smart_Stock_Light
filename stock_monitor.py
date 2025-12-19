import time
import threading
import yfinance as yf
import os
import subprocess
from datetime import datetime, time as dt_time
from tapo_controller import TapoController

class StockMonitor(threading.Thread):
    def __init__(self, shared_config, tapo_controller):
        super().__init__()
        self.shared_config = shared_config
        self.tapo = tapo_controller
        self.running = True
        self.daemon = True
        self.last_alert_time = 0
        self.cooldown_seconds = 300  # 5 分鐘
        
        # 數據緩存
        self.last_stock_price = None
        self.last_stock_name = "監控中..."
        self.last_market_index = None
        self.last_market_change = None
        self.last_update_time = "尚未更新"
        self.device_off = False  # 新增：追蹤硬體是否被使用者手動關閉
        
        # 初始化 TTS 元件
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
        except Exception as e:
            print(f"TTS 初始化失敗 (將改用系統原生語音): {e}")
            self.engine = None

    def is_market_open(self):
        """判斷台股是否在交易時間 (週一至週五 09:00 - 13:30)。"""
        now = datetime.now()
        if now.weekday() >= 5:
            return False
        
        current_time = now.time()
        start_time = dt_time(9, 0)
        end_time = dt_time(13, 30)
        
        return start_time <= current_time <= end_time

    def get_market_status_text(self):
        """取得市場狀態的文字描述。"""
        if self.is_market_open():
            return "交易中 🟢"
        else:
            return "已收盤/未開盤 🔴"

    def fetch_market_index(self):
        """抓取台股大盤指數 (^TWII)，優先使用 fast_info，失敗則使用 history。"""
        try:
            twii = yf.Ticker("^TWII")
            info = twii.fast_info
            price = info.get('last_price')
            
            if price is None:
                # 嘗試使用 history
                hist = twii.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
            
            self.last_market_index = price
            
            # 獲取今日漲跌 (如果有的話)
            prev_close = info.get('previous_close')
            if price and prev_close:
                self.last_market_change = price - prev_close
        except Exception as e:
            print(f"抓取大盤指數失敗: {e}")

    def speak(self, text):
        """朗讀文字，優先使用 pyttsx3，失敗則調用 Mac 原生 say 指令。"""
        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
                return
            except Exception as e:
                print(f"pyttsx3 朗讀出錯: {e}")
        
        # Mac 原生 fallback
        try:
            subprocess.run(["say", text])
        except Exception as e:
            print(f"原生語音指令執行失敗: {e}")

    def trigger_demo_alert(self):
        """執行全功能示範：執行燈光測試序列 (演示開關、漸暗、變色) + 語音說明。"""
        self.device_off = False # 演示時恢復通訊
        print("執行全功能演示模式：正在測試燈光動態與語音輸出...")
        # 1. 執行燈光動態序列 (漸暗 -> 關閉 -> 紅綠黃跳變)
        self.tapo.run_test_sequence()
        # 2. 語音同步說明
        self.speak("系統測試中。燈光已演示漸暗與開關功能，並完成紅、綠、黃三色校準。目前運作正常，準備進入監控模式。")
        return True

    def run(self):
        print("StockMonitor 已啟動。")
        # 初始狀態：顯示黃色，表示待機/監控中 (使用者要求的常態色)
        try:
            self.tapo.turn_on_yellow()
        except Exception as e:
            print(f"初始設定黃燈失敗: {e}")

        while self.running:
            try:
                config = self.shared_config.get_config()
                symbol = config['symbol']
                target = config['target_price']

                # 無論是否休市都更新一次大盤（休市時顯示最後價格）
                self.fetch_market_index()

                # 如果休市，則降低檢查頻率
                if not self.is_market_open():
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 台股目前休市中。")
                    time.sleep(60)
                    continue

                # 抓取監控個股數據
                try:
                    ticker = yf.Ticker(symbol)
                    
                    # 獲取股價
                    current_price = ticker.fast_info.get('last_price')
                    if current_price is None:
                        daily_data = ticker.history(period='1d')
                        if not daily_data.empty:
                            current_price = daily_data['Close'].iloc[-1]
                    
                    # 獲取股票名稱 (嘗試從 info 獲取，若失敗則維持代號)
                    try:
                        # yfinance info 抓取較慢，我們可以用快一點的方式或快取
                        if self.last_stock_name == "監控中..." or self.last_stock_name == symbol:
                            info = ticker.info
                            self.last_stock_name = info.get('longName') or info.get('shortName') or symbol
                    except:
                        self.last_stock_name = symbol

                    self.last_stock_price = current_price
                    self.last_update_time = datetime.now().strftime("%H:%M:%S")
                except Exception as e:
                    print(f"抓取 {symbol} 股價時發生網路錯誤: {e}")
                    current_price = None

                if current_price is not None:
                    # 如果使用者手動關閉了裝置，且股價未達標，我們就不自動打開它
                    if self.device_off and current_price > target:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 監控中，但裝置目前為手動關閉狀態。")
                    else:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {symbol}: {current_price:.2f} | 目標: {target:.2f}")

                    if current_price <= target:
                        now = time.time()
                        if now - self.last_alert_time > self.cooldown_seconds:
                            print(f"!!! 觸發警報: {symbol} 價格 {current_price:.2f} <= {target:.2f} !!!")
                            # 觸發警告時，強制取消關閉狀態
                            self.device_off = False
                            self.tapo.turn_on_green()
                            alert_msg = f"注意，{symbol}目前價格為{current_price:.1f}，已達到您的目標價。"
                            self.speak(alert_msg)
                            self.last_alert_time = now
                    else:
                        # 如果股價回到目標價以上，且冷卻已過，可以切回紅燈（可選）
                        # 或者保持綠燈直到冷卻結束
                        pass
                
                # 每 10 分鐘強制重設一次黃燈，確保顏色正確 (常態燈色)
                # 只有在非手動關閉狀態下才執行
                if not self.device_off and int(time.time()) % 600 < 10:
                    self.tapo.turn_on_yellow()

                time.sleep(10)

            except Exception as e:
                print(f"監控迴圈出錯: {e}")
                time.sleep(10)

    def stop(self):
        self.running = False
