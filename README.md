# 🤖 ANN - Tamil AI Telegram Chatbot

**ANN** is a production-ready, human-like Telegram AI chatbot built with **Python 3.13+**, **python-telegram-bot** (v20+), **Google Gemini API**, and **SQLite**.

She represents a 23-year-old Tamil Software Engineer who chats naturally in **Tamil**, **Tanglish** (Tamil written in English letters), and **English**.

---

## 🌟 Key Features

* **Authentic Persona**: Speaks like a real Tamil friend (friendly, cheerful, software engineer, in a happy relationship, uses expressions like *dei*, *machi*, *seri*, *ayyoo* naturally).
* **Multi-language & Script Support**:
  * **Tanglish**: Replies in Tanglish when messaged in Tanglish ("enna panra?").
  * **Tamil**: Replies in Tamil script when messaged in Tamil ("என்ன பண்றீங்க?").
  * **English**: Replies in English when messaged in English.
* **Per-User Conversational Memory**: Uses **SQLite (`aiosqlite`)** to store and retrieve the last 20 messages per user for smooth context awareness.
* **Telegram Typing Indicator**: Shows a live "typing..." status in Telegram while generating answers.
* **Long Message Handler**: Automatically splits long responses exceeding Telegram's 4096 character limit into clean, readable chunks.
* **Rate Limiting**: Protects against spamming and API quota depletion (10 requests per minute per user).
* **Production Ready**: Full async design, clean modular architecture, error resilience, and environment variable configuration.

---

## 📁 Project Structure

```text
ann_telegram_bot/
├── .env                  # Environment variables (DO NOT commit to git)
├── .env.example          # Environment variable template
├── requirements.txt      # Python dependencies
├── config.py             # Configuration loader & validator
├── database.py           # SQLite asynchronous DB operations (aiosqlite)
├── gemini_service.py     # Gemini API integration & persona system prompt
├── main.py               # Main bot execution script & telegram event loop
├── Procfile              # Worker command for Railway/Cloud deployment
└── README.md             # Project documentation & setup guide
```

---

## 🔑 1. Obtaining API Keys

### A. Telegram Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Start a chat and send the command `/newbot`.
3. Follow the prompts to name your bot (e.g., `ANN Chatbot`) and set a username (e.g., `AnnTamilAiBot`).
4. Copy the HTTP API token provided by BotFather (e.g., `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).

### B. Google Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. Click on **Get API key** and select **Create API key**.
4. Copy your generated API Key.

---

## 🚀 2. Local Setup & Execution

### Prerequisites
* Python 3.13 or Python 3.10+ installed on your system.
* Git installed.

### Step-by-step Setup

1. **Navigate to the project folder**:
   ```bash
   cd ann_telegram_bot
   ```

2. **Create and activate a virtual environment**:
   * **On Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   * **On Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   * **Windows (PowerShell)**:
     ```powershell
     Copy-Item .env.example .env
     ```
   * **Linux / macOS**:
     ```bash
     cp .env.example .env
     ```

   Open `.env` in any text editor and fill in your keys:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
   GEMINI_API_KEY=AIzaSyYourActualGeminiApiKeyHere
   DATABASE_PATH=ann_chat.db
   MAX_HISTORY_MESSAGES=20
   RATE_LIMIT_MESSAGES=10
   RATE_LIMIT_WINDOW_SECONDS=60
   GEMINI_MODEL=gemini-2.5-flash
   ```

5. **Run the Bot**:
   ```bash
   python main.py
   ```

6. Open Telegram, search for your bot username, and send `/start` or start chatting!

---

## ☁️ 3. Cloud Deployment Guide

### Option A: Railway (Recommended)

1. Sign up/log in at [Railway.app](https://railway.app/).
2. Click **New Project** -> **Deploy from GitHub repo** (or use Railway CLI).
3. Connect your GitHub repository containing this bot's code.
4. Go to the **Variables** tab in your Railway service and add the environment variables:
   * `TELEGRAM_BOT_TOKEN`: `your_bot_token`
   * `GEMINI_API_KEY`: `your_gemini_api_key`
   * `DATABASE_PATH`: `ann_chat.db`
   * `MAX_HISTORY_MESSAGES`: `20`
   * `GEMINI_MODEL`: `gemini-2.5-flash`
5. Railway will automatically detect the `Procfile` (`worker: python main.py`) and deploy your bot!

### Option B: VPS (Ubuntu / Linux with Systemd)

1. SSH into your VPS server:
   ```bash
   ssh user@your_vps_ip
   ```
2. Clone your repo and set up virtual environment:
   ```bash
   git clone <your-repo-url> ann_telegram_bot
   cd ann_telegram_bot
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   nano .env  # Add your API keys
   ```
3. Create a Systemd service (`/etc/systemd/system/annbot.service`):
   ```ini
   [Unit]
   Description=ANN Telegram AI Bot
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/ann_telegram_bot
   ExecStart=/home/ubuntu/ann_telegram_bot/venv/bin/python main.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```
4. Start and enable the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start annbot
   sudo systemctl enable annbot
   ```
5. Check status:
   ```bash
   sudo systemctl status annbot
   ```

---

## 💬 Conversation Commands & Features

* `/start` - Start conversation with ANN.
* `/reset` - Clear chat history and start fresh.
* **Casual Chatting**: Talk about tech, movies, music, food, relationships, or work!
* **Automatic Language Adaptation**: Speak in Tamil script, Tanglish, or English—ANN will respond in the same language.

---

## 📜 License

MIT License. Feel free to customize and extend ANN for your own projects!
