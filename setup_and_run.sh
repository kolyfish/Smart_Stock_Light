#!/bin/bash

# Stock-to-Home Alert 一鍵安裝與執行腳本
# 適用於 macOS

echo "------------------------------------------"
echo "   Stock-to-Home Alert 啟動中..."
echo "------------------------------------------"

# 1. 檢查 Python 是否安裝
if ! command -v python3 &> /dev/null
then
    echo "錯誤: 未偵測到 Python3。請先安裝 Python (https://www.python.org/)"
    exit 1
fi

# 2. 建立虛擬環境 (若不存在)
if [ ! -d "venv" ]; then
    echo "正在建立虛擬環境 (venv)..."
    python3 -m venv venv
fi

# 3. 啟動虛擬環境並安裝依賴
echo "正在安裝/更新必要套件..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. 啟動主程式
echo "啟動伺服器與監控系統..."
python3 main_gui.py

# 結束後離開點
deactivate
