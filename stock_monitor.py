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
        self.log_messages = [] # 新增：日誌緩存
        self.max_logs = 50     # 最多保留 50 條日誌
        
        # 數據緩存
        self.last_stock_price = None
        self.last_stock_name = "監控中..."
        self.last_market_index = None
        self.last_market_change = None
        self.last_update_time = "尚未更新"
        self.device_off = False  # 追蹤硬體是否被使用者手動關閉
        self.alert_mode = None   # 'above' 或 'below'，自動判定
        self._price_history = [] # 儲存最近幾分鐘的價格，偵測閃崩
        
        # 初始化 TTS 元件
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
        except Exception as e:
            print(f"TTS 初始化失敗 (將改用系統原生語音): {e}")
            self.engine = None

    def is_crypto(self, symbol):
        """判斷是否為虛擬貨幣 (yfinance 中通常帶有 -USD, -BTC 等，或為特定符號)。"""
        # yfinance 虛擬貨幣通常包含 "-" 且結尾為 USD, BTC, ETH 等
        crypto_suffixes = ['-USD', '-BTC', '-ETH', '-USDT']
        return any(suffix in symbol.upper() for suffix in crypto_suffixes) or symbol.upper().endswith('=X')

    def is_market_open(self, symbol=None):
        """判斷市場是否在交易時間。支援台股、美股與虛擬貨幣。"""
        if symbol and self.is_crypto(symbol):
            return True
            
        now = datetime.now()
        
        # 決定市場時區與時間
        if symbol and ('.TW' in symbol.upper() or '.TWO' in symbol.upper()):
            # 台股範疇
            market = "TW"
            if now.weekday() >= 5: return False
            current_time = now.time()
            return dt_time(9, 0) <= current_time <= dt_time(13, 30)
        else:
            # 預設為美股範疇 (無後綴 or 其他)
            market = "US"
            # 美股開盤概略時間 (台灣時間): 
            # 冬季: 22:30 - 05:00 (+1)
            # 夏季: 21:30 - 04:00 (+1)
            # 為了簡化與保險，我們監測 21:00 - 06:00
            if now.weekday() == 5: # 週六早上 06:00 前還算週五美股
                return now.time() <= dt_time(6, 0)
            if now.weekday() == 6: # 週日全天休息
                return False
            if now.weekday() == 0: # 週一早上 21:00 前休息
                return now.time() >= dt_time(21, 0)
            
            # 週一到週五的夜間
            current_time = now.time()
            return current_time >= dt_time(21, 0) or current_time <= dt_time(6, 0)

    def get_market_status_text(self):
        """取得市場狀態的文字描述。"""
        config = self.shared_config.get_config()
        symbol = config.get('symbol', '2330.TW')
        
        is_open = self.is_market_open(symbol)
        
        if self.is_crypto(symbol):
            return "虛擬貨幣 24/7 交易中 🟢"
            
        if '.TW' in symbol.upper() or '.TWO' in symbol.upper():
            return "台股交易中 🟢" if is_open else "台股收盤/未開盤 🔴"
        else:
            return "美股交易中 🟢" if is_open else "美股收盤/未開盤 🔴"

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

    def add_log(self, message):
        """將日誌加入緩存，供 Web 端讀取。"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry) # 同步保存在終端機顯示
        self.log_messages.append(log_entry)
        if len(self.log_messages) > self.max_logs:
            self.log_messages.pop(0)

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
                stop_loss = config.get('stop_loss_price', 0.0)
                
                # 如果代號或目標價變更，重置警報模式與價格緩存
                if not hasattr(self, '_last_symbol') or self._last_symbol != symbol:
                    self.alert_mode = None
                    self.last_stock_name = "監控中..."
                    self.last_stock_price = None  # 同時清除舊價格
                    self._price_history = []      # 清除舊股票的價格歷史，防止誤判閃崩
                    self._last_symbol = symbol
                
                if not hasattr(self, '_last_target') or self._last_target != target:
                    self.alert_mode = None
                    self._last_target = target

                # 無論是否休市都更新一次大盤（休市時顯示最後價格）
                self.fetch_market_index()

                # 如果是台股且休市，則降低檢查頻率
                if not self.is_crypto(symbol) and not self.is_market_open(symbol):
                    self.add_log(f"台股目前休市中，監控暫緩。")
                    time.sleep(60)
                    continue

                # 抓取監控個股數據
                try:
                    ticker = yf.Ticker(symbol)
                    
                    # 獲取股價 - 優先順序調整
                    current_price = None
                    
                    # 1. 嘗試快速獲取 (fast_info)
                    try:
                        current_price = ticker.fast_info.get('last_price')
                    except:
                        pass

                    # 2. 如果 1 失敗，嘗試 history (1m interval)
                    if current_price is None or current_price == 0:
                        try:
                            hist = ticker.history(period="1d", interval="1m")
                            if not hist.empty:
                                current_price = hist['Close'].iloc[-1]
                        except Exception as e:
                            self.add_log(f"History 抓取失敗: {e}")

                    # 3. 如果 2 失敗，嘗試 5d history
                    if current_price is None or current_price == 0:
                        hist = ticker.history(period="5d")
                        if not hist.empty:
                            current_price = hist['Close'].iloc[-1]
                    
                    if current_price is None:
                        self.add_log(f"無法獲取 {symbol} 股價 (市場可能未開盤或代號錯誤)")
                        time.sleep(10)
                        continue

                    self.last_stock_price = current_price
                    self.last_update_time = datetime.now().strftime("%H:%M:%S")

                    # 獲取股票名稱 (完全由系統自動抓取)
                    if self.last_stock_name == "監控中..." or self.last_stock_name == symbol:
                        try:
                            info = ticker.info
                            # 優先取長、短名
                            fetched_name = info.get('longName') or info.get('shortName') or symbol
                            if fetched_name != self.last_stock_name:
                                self.last_stock_name = fetched_name
                                self.add_log(f"成功識別股票名稱：{self.last_stock_name}")
                        except:
                            self.last_stock_name = symbol

                    self.last_stock_price = current_price
                    self.last_update_time = datetime.now().strftime("%H:%M:%S")

                    # --- 閃崩偵測 (Purple Light) ---
                    now_ts = time.time()
                    
                    # 數據清洗：忽略異常價格（如 0 或變動過於誇張的極端值）
                    if current_price > 0:
                        if self.last_stock_price and abs(current_price - self.last_stock_price) / self.last_stock_price > 0.5:
                            self.add_log(f"⚠️ 偵測到價格劇烈跳變 ({self.last_stock_price} -> {current_price})，暫不記入閃崩歷史。")
                        else:
                            self._price_history.append((now_ts, current_price))
                    
                    # 只保留最近 5 分鐘的數據
                    self._price_history = [p for p in self._price_history if now_ts - p[0] <= 300]
                    
                    if len(self._price_history) >= 5: # 增加數據量要求，避免單次跳動觸發
                        # 檢查最近 1 分鐘內的跌幅
                        one_min_ago = [p for p in self._price_history if now_ts - p[0] <= 60]
                        if len(one_min_ago) >= 3: # 至少要有 3 個點
                            price_old = one_min_ago[0][1]
                            drop_rate = (price_old - current_price) / price_old
                            if drop_rate >= 0.015: # 閃崩 1.5%
                                self.add_log(f"⚠️ 偵測到閃崩！一分鐘實質跌幅 {drop_rate*100:.1f}%")
                                self.tapo.turn_on_purple()
                                self.speak(f"警告，{self.last_stock_name} 偵測到恐慌性閃崩，目前跌幅百分之 {drop_rate*100:.1f}。")
                                time.sleep(5) # 稍微暫停避免連續觸發

                    # --- 數據異常診斷 (Red Light part 1) ---
                    # 如果能跑到這代表抓到資料了

                    # 自動判定警報模式 (第一次抓到價格，或設定變更後)
                    if self.alert_mode is None:
                        if current_price < target:
                            self.alert_mode = 'above' # 目前低於目標，監控「漲破」
                            self.add_log(f"警報模式：設定為「等待漲破」 {target} (現價 {current_price:.2f})")
                        else:
                            self.alert_mode = 'below' # 目前高於目標，監控「跌破」
                            self.add_log(f"警報模式：設定為「等待跌破」 {target} (現價 {current_price:.2f})")

                    # 檢查警報是否達成
                    is_alert_hit = False
                    is_stop_loss_hit = False

                    # --- 停損監控 (Red Light part 2) ---
                    if stop_loss > 0 and current_price <= stop_loss:
                        is_stop_loss_hit = True

                    if self.alert_mode == 'above' and current_price >= target:
                        is_alert_hit = True
                    elif self.alert_mode == 'below' and current_price <= target:
                        is_alert_hit = True
                    
                    if is_stop_loss_hit:
                        self.add_log(f"🆘 觸發停損警報: {symbol} 跌破停損價 {stop_loss} ({current_price:.2f})")
                        self.device_off = False
                        self.tapo.turn_on_red()
                        self.speak(f"緊急通知，{self.last_stock_name} 已經跌破停損價 {stop_loss}，目前價格 {current_price:.1f}，請注意風險。")
                        self.last_alert_time = now_ts # 使用冷卻時間防護
                    elif is_alert_hit:
                        now = time.time()
                        if now - self.last_alert_time > self.cooldown_seconds:
                            self.add_log(f"!!! 觸發警報: {symbol} 已達標 ({current_price:.2f}) !!!")
                            self.device_off = False
                            self.tapo.turn_on_green()
                            
                            # TTS 優化：針對虛擬貨幣改讀法
                            if self.is_crypto(symbol):
                                # BTC-USD -> "B T C"
                                crypto_name = symbol.split("-")[0]
                                spaced_symbol = " ".join(list(crypto_name))
                                alert_msg = f"注意，虛擬貨幣 {spaced_symbol} {self.last_stock_name} 目前價格為 {current_price:.2f}，已達到您的目標價。"
                            else:
                                spaced_symbol = " ".join(list(symbol.split(".")[0]))
                                alert_msg = f"注意，股票代號 {spaced_symbol} {self.last_stock_name} 目前價格為 {current_price:.1f}，已達到您的目標價。"
                                
                            self.speak(alert_msg)
                            self.last_alert_time = now
                    else:
                        # 未達標時，若沒手動關閉則維持黃燈
                        if not self.device_off:
                            self.tapo.turn_on_yellow()
                            self.add_log(f"{symbol}: {current_price:.2f} (目標 {target} | 監控中)")
                        else:
                            self.add_log(f"監控中，但裝置目前為手動關閉。")

                except Exception as e:
                    self.add_log(f"數據抓取或警報診斷異常: {e}")
                    # --- 異常診斷 (Red Light part 3) ---
                    if not self.device_off:
                        self.tapo.turn_on_red()
                        self.add_log("系統診斷：無法取得數據，切換為紅燈警示。")
                
                time.sleep(10)

            except Exception as e:
                print(f"監控迴圈出錯: {e}")
                time.sleep(10)

    def stop(self):
        self.running = False
