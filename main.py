import tkinter as tk
from tkinter import ttk
from dotenv import load_dotenv
import os

load_dotenv() # 載入 .env 設定
from PIL import ImageTk
import qrcode
import socket
import sys

from core.config import SharedConfig
from devices.controller import TapoController
from core.monitor import StockMonitor
from web.server import WebServer
from system.instance import SingleInstance

def get_local_ip():
    try:
        # Create a dummy socket to connect to an internet address (doesn't actually connect)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class SmartStockLight:
    def __init__(self, root):
        self.root = root
        self.root.title("SmartStockLight Server")
        self.root.geometry("400x500")

        # Initialize Components
        self.shared_config = SharedConfig()
        self.tapo = TapoController(self.shared_config)
        
        # Start Threads
        self.monitor = StockMonitor(self.shared_config, self.tapo)
        self.monitor.start()
        
        self.server = WebServer(self.shared_config, self.tapo, self.monitor)
        self.server.start()

        # GUI Elements
        self.label_title = ttk.Label(root, text="SmartStockLight Server Running", font=("Arial", 16))
        self.label_title.pack(pady=20)

        self.ip_address = get_local_ip()
        self.url = f"http://{self.ip_address}:5001"
        
        self.label_info = ttk.Label(root, text=f"Scan QR code to configure:\n{self.url}", font=("Arial", 12), justify="center")
        self.label_info.pack(pady=10)

        # QR Code Generation
        self.qr_label = ttk.Label(root)
        self.qr_label.pack(pady=10)
        self.generate_qr(self.url)

        # Status Label
        self.status_label = ttk.Label(root, text="System Status: Monitoring...", foreground="green")
        self.status_label.pack(pady=20)

        # Handle Exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def generate_qr(self, data):
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")
        
        # Convert to PhotoImage
        self.tk_img = ImageTk.PhotoImage(img)
        self.qr_label.configure(image=self.tk_img)

    def on_closing(self):
        print("Shutting down...")
        self.monitor.stop()
        # Flask thread is daemon, will exit with main
        self.root.destroy()
        sys.exit(0)

from system.license import check_license

if __name__ == "__main__":
    try:
        # 確保只有一個執行實體
        instance_lock = SingleInstance()
        
        if not check_license():
            sys.exit(1)
            
        root = tk.Tk()
        app = SmartStockLight(root)
        root.mainloop()
    except Exception as e:
        import traceback
        import datetime
        
        error_msg = f"[{datetime.datetime.now()}] Critical Error:\n{traceback.format_exc()}\n"
        print(error_msg)
        
        # 寫入 crash log
        with open("crash_log.txt", "a", encoding="utf-8") as f:
            f.write(error_msg)
            
        print("程式發生嚴重錯誤，已記錄至 crash_log.txt")
        input("請按 Enter 鍵離開... (Press Enter to exit)")

