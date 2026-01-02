import sys
import os
from flask import Flask, render_template, request, jsonify
import threading
from system.updater import AutoUpdater
from devices.scanner import get_tapo_devices_sync

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class WebServer(threading.Thread):
    def __init__(self, shared_config, tapo_controller, stock_monitor, open_browser=True):
        super().__init__()
        # Ensure Flask knows where to look for templates in the frozen app
        template_dir = resource_path('templates')
        self.app = Flask(__name__, template_folder=template_dir)
        self.shared_config = shared_config
        self.tapo = tapo_controller
        self.monitor = stock_monitor
        self.updater = AutoUpdater()
        self.daemon = True
        self.open_browser = open_browser
        
        # 定義路由
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/api/config', 'update_config', self.update_config, methods=['POST'])
        self.app.add_url_rule('/api/test_green', 'test_green', self.test_green, methods=['POST'])
        self.app.add_url_rule('/api/test_yellow', 'test_yellow', self.test_yellow, methods=['POST'])
        self.app.add_url_rule('/api/test_purple', 'test_purple', self.test_purple, methods=['POST'])
        self.app.add_url_rule('/api/run_test', 'run_test', self.run_test, methods=['POST'])
        self.app.add_url_rule('/api/turn_off', 'turn_off', self.turn_off, methods=['POST'])
        self.app.add_url_rule('/api/market_status', 'market_status', self.market_status, methods=['GET'])
        self.app.add_url_rule('/api/demo_alert', 'demo_alert', self.demo_alert, methods=['POST'])
        self.app.add_url_rule('/api/market_data', 'market_data', self.market_data, methods=['GET'])
        self.app.add_url_rule('/api/logs', 'get_logs', self.get_logs, methods=['GET'])
        self.app.add_url_rule('/api/check_update', 'check_update', self.check_update, methods=['GET'])
        self.app.add_url_rule('/api/apply_update', 'apply_update', self.apply_update, methods=['POST'])
        self.app.add_url_rule('/api/stop_alarm', 'stop_alarm', self.stop_alarm, methods=['POST'])
        self.app.add_url_rule('/api/simulate_data', 'simulate_data', self.simulate_data, methods=['POST'])
        self.app.add_url_rule('/api/scan_devices', 'scan_devices', self.scan_devices, methods=['GET'])
        self.app.add_url_rule('/api/scan_devices', 'scan_devices', self.scan_devices, methods=['GET'])
        self.app.add_url_rule('/api/scan_tapo', 'scan_tapo', self.scan_tapo, methods=['GET'])
        self.app.add_url_rule('/api/connect_qr', 'connect_qr', self.get_connect_qr, methods=['GET'])

    def get_connect_qr(self):
        import qrcode
        import io
        import base64
        import socket
        
        # Get Local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except Exception:
            ip = "127.0.0.1"
            
        url = f"http://{ip}:5001"
        
        # Generate QR
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to buffer
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        
        return jsonify({
            "status": "success", 
            "url": url,
            "qr_image": f"data:image/png;base64,{img_str}"
        })
    def index(self):
        config = self.shared_config.get_config()
        return render_template('index.html', config=config)

    def update_config(self):
        data = request.json
        symbol = data.get('symbol')
        target = data.get('target_price')
        stop_loss = data.get('stop_loss_price')
        tapo_email = data.get('tapo_email')
        tapo_password = data.get('tapo_password')
        tapo_ip = data.get('tapo_ip')
        device_type = data.get('device_type')
        
        print(f"網頁更新請求: {symbol}, {target}, {stop_loss}, Tapo: {tapo_email}@{tapo_ip}, Device: {device_type}")
        self.shared_config.update_config(symbol, target, stop_loss, tapo_email, tapo_password, tapo_ip, device_type)
        
        return jsonify({"status": "success", "config": self.shared_config.get_config()})
    
    def test_green(self):
        print("網頁請求: 測試亮綠燈")
        self.monitor.device_off = False
        import time
        self.monitor.test_mode_until = time.time() + 5 # 暫停監控 5 秒
        self.tapo.turn_on_green()
        return jsonify({"status": "success", "message": "綠燈已開啟 (維持5秒)"})

    def test_yellow(self):
        print("網頁請求: 測試亮黃燈")
        self.monitor.device_off = False
        self.tapo.turn_on_yellow()
        return jsonify({"status": "success", "message": "黃燈已開啟"})

    def test_purple(self):
        print("網頁請求: 測試亮紫燈 (閃崩)")
        self.monitor.device_off = False
        import time
        self.monitor.test_mode_until = time.time() + 5 # 暫停監控 5 秒
        self.tapo.turn_on_purple()
        return jsonify({"status": "success", "message": "紫燈已開啟 (維持5秒)"})

    def run_test(self):
        print("網頁請求: 執行漸暗閃爍測試")
        self.monitor.device_off = False
        self.tapo.run_test_sequence()
        return jsonify({"status": "success", "message": "測試序列已啟動"})

    def turn_off(self):
        print("網頁請求: 睡眠待命模式")
        print("網頁請求: 睡眠待命模式")
        self.monitor.device_off = True # 標記為睡眠模式，阻止自動亮黃燈
        self.tapo.set_sleep_standby()  # 調暗至 0.01% 亮度
        # 語音通知
        import subprocess
        try:
            subprocess.run(["say", "燈光待命亮度零度流明，但發生闃崩燈還是會亮起"])
        except Exception:
            pass
        return jsonify({"status": "success", "message": "睡眠待命模式已啟動"})
    
    def stop_alarm(self):
        print("網頁請求: 停止警報")
        success = self.monitor.stop_alarm()
        if success:
            return jsonify({"status": "success", "message": "警報已停止"})
        else:
            return jsonify({"status": "info", "message": "當前沒有活躍的警報"})

    def market_status(self):
        config = self.shared_config.get_config()
        symbol = config.get('symbol')
        status_text = self.monitor.get_market_status_text() # get_market_status_text already pulls config internally in my update
        return jsonify({
            "status": status_text,
            "is_open": self.monitor.is_market_open(symbol)
        })

    def demo_alert(self):
        print("網頁請求: 全功能示範")
        self.monitor.trigger_demo_alert()
        return jsonify({"status": "success", "message": "演示已啟動"})

    def market_data(self):
        return jsonify({
            "market_index": self.monitor.last_market_index,
            "market_change": self.monitor.last_market_change,
            "stock_price": self.monitor.last_stock_price,
            "stock_name": self.monitor.last_stock_name,
            "update_time": self.monitor.last_update_time,
            "symbol": self.shared_config.get_config()['symbol'],
            "alert_active": self.monitor.alarm_active or self.monitor.tapo.is_alerting_state() # Hybrid logic
        })

    def simulate_data(self):
        data = request.json
        price = data.get('price')
        if price is not None:
            self.monitor.mock_current_price = float(price)
            return jsonify({"status": "success", "message": f"模擬現價已設定為 {price}"})
        else:
            self.monitor.mock_current_price = None
            return jsonify({"status": "success", "message": "模擬數據已清除"})

    def get_logs(self):
        return jsonify({
            "logs": self.monitor.log_messages
        })

    def check_update(self):
        has_update, msg = self.updater.check_for_updates()
        return jsonify({"has_update": has_update, "message": msg})

    def apply_update(self):
        success, msg = self.updater.apply_update()
        return jsonify({"status": "success" if success else "error", "message": msg})

    def scan_tapo(self):
        print("網頁請求: 掃描 Tapo 設備")
        devices = get_tapo_devices_sync()
        return jsonify({"status": "success", "devices": devices})
    
    def scan_devices(self):
        print("網頁請求: 掃描區域網路裝置")
        devices = self.tapo.scan_devices()
        return jsonify({"status": "success", "devices": devices})

    def run(self):
        if self.open_browser:
            # 自動開啟瀏覽器
            import webbrowser
            try:
                webbrowser.open('http://127.0.0.1:5001')
            except Exception:
                pass
            
        # 使用 5001 連接埠以避開 Mac 系統衝突
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            print(f"\n📱 手機連線網址: http://{ip}:5001")
            print("💡 提示: iOS Safari 可點擊分享 -> 加入主畫面，獲得 App 體驗\n")
        except Exception:
            pass
            
        self.app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

