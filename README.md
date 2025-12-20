# SmartStockLight 智慧股票燈具

這是一個桌面端應用程式，用於監控特定股票價格。當價格低於「目標價 (Target Price)」時，透過 Wi-Fi 控制家中的 TP-Link Tapo 智慧燈泡變色（綠色），並發出語音警報。

## 功能特色

- 📈 **即時股價監控**：使用 `yfinance` 抓取即時股價
- 💡 **智慧燈泡控制**：透過 Wi-Fi 控制 TP-Link Tapo L530E 燈泡
- 🔊 **語音警報**：當價格達到目標時自動播放語音
- ⏱️ **防抖動機制**：5 分鐘冷卻時間，防止燈泡瘋狂閃爍
- 💾 **設定持久化**：自動儲存設定到 `config.json`
- 📝 **即時日誌**：GUI 中顯示詳細的執行日誌

## 系統需求

- **OS**: macOS (Mac mini)
- **Python**: 3.10+
- **硬體**: TP-Link Tapo L530E 智慧燈泡

## 安裝步驟

### 前置需求

- **Poetry**：專案使用 Poetry 管理依賴
  ```bash
  # 如果尚未安裝 Poetry
  curl -sSL https://install.python-poetry.org | python3 -
  ```

### 安裝與執行

1. **安裝依賴**（Poetry 會自動建立虛擬環境）：
   ```bash
   poetry install
   ```

2. **執行應用程式**：
   ```bash
   poetry run python smart_stock_light.py
   ```

   或者先啟動 Poetry shell：
   ```bash
   poetry shell
   python smart_stock_light.py
   ```

### 注意事項

- **tkinter**：macOS 上通常已內建，無需額外安裝
  - 如果遇到 `ModuleNotFoundError: No module named '_tkinter'` 錯誤，請安裝 Python 的 tkinter 支援：
    ```bash
    # 使用 Homebrew 安裝的 Python
    brew install python-tk
    ```
- **asyncio**：Python 3.4+ 標準庫，無需安裝
- Poetry 會自動管理虛擬環境，無需手動建立 `venv`
- 所有依賴（`plugp100`、`yfinance`、`pyttsx3`）已包含在 `pyproject.toml` 中

## 使用說明

1. **輸入設定**：
   - Tapo Email：您的 Tapo 帳號 Email
   - Tapo Password：您的 Tapo 帳號密碼
   - Tapo IP Address：燈泡的 IP 位址（可在 Tapo App 中查看）
   - 股票代碼：例如 `2330.TW`（台積電）
   - 目標價格：觸發警報的價格閾值

2. **開始監控**：
   - 點擊「開始監控」按鈕
   - 系統會每 60 秒檢查一次股價
   - 當價格低於目標價格時，會觸發警報（燈泡變綠 + 語音播報）

3. **停止監控**：
   - 點擊「停止監控」按鈕
   - 系統會優雅地停止監控迴圈

## 專案結構

```
SmartStockLight/
├── tapo_controller.py    # 硬體層：Tapo 燈泡控制
├── stock_monitor.py       # 邏輯層：股價監控與警報邏輯
├── smart_stock_light.py  # 展示層：GUI 介面
├── pyproject.toml        # Poetry 專案設定檔
├── poetry.lock           # Poetry 鎖定檔（自動生成）
├── requirements.txt      # 依賴套件清單（備用）
├── config.json          # 設定檔（自動生成）
└── # SmartStockLight (股市亮燈提醒系統) 🟢

這是一個專為非工程師設計的股市監控系統。當您關注的股票跌破目標價時，系統會自動透過 **Tapo 智慧插座** 點亮家中綠燈，並發出語音提醒。

## ✨ 特色
- **一鍵啟動**：專為 Mac 使用者設計的簡易腳本。
- **手機操控**：掃描電腦螢幕上的 QR Code，即可直接用手機設定股票代號與目標價。
- **高品質界面**：全新升級的深色模式 Web UI，高端大氣且直覺。
- **語音警示**：跌破價格時會自動朗讀警報。

---

## 🚀 快速開始 (Mac 使用者)

### 1. 安裝 Python
如果您電腦還沒有 Python，請先至 [Python 官網](https://www.python.org/downloads/) 下載並安裝。

### 2. 下載專案並執行
1. 下載本專案並解壓縮。
2. 打開 **終端機 (Terminal)**。
3. 將此資料夾拖入終端機視窗。
4. 輸入以下指令並按 Enter：
   ```bash
   ./setup_and_run.sh
   ```

---

## 📱 如何使用 Web 界面
1. 程式啟動後，電腦螢幕會出現一個 **QR Code**。
2. 使用手機相機掃描 QR Code。
3. 在手機網頁上輸入：
   - **股票代號** (例如台積電為 `2330.TW`)。
   - **目標價格** (當股價低於此數字時會觸發亮燈)。
4. 點擊 **"更新智慧監控"**。

---

## 🛠 硬體需求
- **TP-Link Tapo 智慧插座** (例如 P100/P110)。
- 插座需與電腦連接在同一個 Wi-Fi 環境下。
- 預設 IP: `192.168.100.150` (請在 `tapo_controller.py` 中視需求修改)。

---

## ⚠️ 注意事項
- 請確保您的電腦與手機在同一個 Wi-Fi 網路下，QR Code 才能正常連接。
- 此系統僅供參考，股市投資有風險，請謹慎操作。
            # 本檔案

## 技術架構

### 三層架構設計

1. **Hardware Layer** (`tapo_controller.py`)
   - 負責與 TP-Link Tapo L530E 溝通
   - 提供 Thread-safe 的同步介面

2. **Logic Layer** (`stock_monitor.py`)
   - 負責抓取股價與判斷邏輯
   - 實作 Debounce 機制（5 分鐘冷卻時間）
   - 整合 TTS 語音播報

3. **Presentation Layer** (`smart_stock_light.py`)
   - 使用 tkinter 建構 GUI
   - 管理背景監控 Thread
   - 提供即時日誌顯示

### 關鍵技術

- **Threading**：監控迴圈在背景 Thread 執行，不阻塞 GUI
- **Async/Await**：Tapo 控制使用 `plugp100` 的 Async API
- **Logging Handler**：自訂 Handler 將日誌輸出到 GUI
- **Config Persistence**：自動儲存/載入使用者設定

## 注意事項

- 確保 Mac 與 Tapo 燈泡連接到同一個 Wi-Fi 網路
- 首次使用時，建議先測試燈泡連接（可在程式中加入測試按鈕）
- 監控迴圈每 60 秒執行一次，避免過度頻繁的 API 請求
- 防抖動機制確保在 5 分鐘內不會重複觸發警報

## 授權

本專案為個人專案，僅供學習與研究使用。

