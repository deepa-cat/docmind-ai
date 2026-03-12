# 🧠 DocMind AI — Python + HTML Web App

## 📁 Project Structure
```
docmind-project/
├── app.py              ← Flask backend (Python)
├── requirements.txt    ← Python packages
├── templates/
│   └── index.html      ← Frontend (HTML + CSS + JS)
└── README.md
```

## ⚡ Setup (One time)

### Step 1 — Python packages install பண்ணுங்க
VS Code terminal-ல:
```bash
pip install -r requirements.txt
```

### Step 2 — API Key set பண்ணுங்க
`app.py` file open பண்ணுங்க, இந்த line தேடுங்க:
```python
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "your-api-key-here")
```
`your-api-key-here` மாத்தி உங்க Anthropic API key paste பண்ணுங்க.

👉 API Key: https://console.anthropic.com → API Keys → Create Key

### Step 3 — Run பண்ணுங்க
```bash
python app.py
```
Browser-ல open ஆகும்: **http://localhost:5000**

---

## 🚀 Every time use பண்ண
```bash
python app.py
```
அவ்வளவுதான்! Browser-ல http://localhost:5000 போங்க.

---

## ✨ Features
- 📄 PDF, TXT, MD, CSV, JSON, HTML, PY, JS upload
- 💬 Q&A — document பத்தி கேள்விகள்
- ◎ Summarize — smart summary
- ⇄ Translate — 12 languages
- ✦ Key Points — important insights
- 🎤 Voice Input (Chrome)
- 🔊 TTS — Listen to answers
