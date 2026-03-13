from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import PyPDF2
import io
import os

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

def extract_pdf_text(pdf_bytes):
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages[:30]:
            text += page.extract_text() or ""
        return text.strip()
    except:
        return ""

def call_groq(system_prompt, user_content, max_tokens=1024):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + GROQ_API_KEY
    }
    body = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    }
    res = requests.post(GROQ_URL, headers=headers, json=body)
    data = res.json()
    if not res.ok:
        raise Exception(data.get("error", {}).get("message", "Groq API Error " + str(res.status_code)))
    return data["choices"][0]["message"]["content"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    content = file.read()
    try:
        if file.filename.lower().endswith(".pdf"):
            text = extract_pdf_text(content)
            if not text:
                return jsonify({"error": "PDF-ல text extract ஆகல. Image-based PDF-ஆ இருக்கலாம்."}), 400
        else:
            try:
                text = content.decode("utf-8")
            except:
                text = content.decode("latin-1")
        return jsonify({"success": True, "filename": file.filename, "text": text[:80000]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    doc_text = data.get("doc_text", "")
    history = data.get("history", [])
    question = data.get("question", "")
    if not doc_text or not question:
        return jsonify({"error": "Missing data"}), 400
    system = f"You are a document analysis expert. Here is the document:\n\n---\n{doc_text[:12000]}\n---\n\nAnswer questions based strictly on this document."
    conversation = ""
    for m in history[-6:]:
        role = "User" if m["role"] == "user" else "Assistant"
        conversation += f"{role}: {m['content']}\n"
    conversation += f"User: {question}"
    try:
        reply = call_groq(system, conversation)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/summarize", methods=["POST"])
def summarize():
    data = request.json
    doc_text = data.get("doc_text", "")
    if not doc_text:
        return jsonify({"error": "No document"}), 400
    try:
        result = call_groq(
            "You are an expert summarizer. Provide a clear structured summary with bullet points.",
            f"Summarize:\n\n---\n{doc_text[:12000]}\n---"
        )
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/translate", methods=["POST"])
def translate():
    data = request.json
    doc_text = data.get("doc_text", "")
    language = data.get("language", "Tamil")
    if not doc_text:
        return jsonify({"error": "No document"}), 400
    try:
        result = call_groq(
            f"You are a professional translator. Translate to {language}. Preserve structure and meaning.",
            f"Translate to {language}:\n\n---\n{doc_text[:8000]}\n---"
        )
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/keypoints", methods=["POST"])
def keypoints():
    data = request.json
    doc_text = data.get("doc_text", "")
    if not doc_text:
        return jsonify({"error": "No document"}), 400
    try:
        result = call_groq(
            "You are an expert analyst. Extract all key points as a numbered list with brief explanations.",
            f"Extract key points:\n\n---\n{doc_text[:12000]}\n---"
        )
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    if not GROQ_API_KEY:
        print("WARNING: GROQ_API_KEY not set!")
    print(f"DocMind AI starting on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
