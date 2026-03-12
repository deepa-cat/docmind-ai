from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import anthropic
import PyPDF2
import io
import base64
import os

app = Flask(__name__)
CORS(app)

# ── Anthropic client ──────────────────────────────────────────────────────
# உங்க API key இங்க paste பண்ணுங்க (அல்லது .env file use பண்ணலாம்)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    print("WARNING: ANTHROPIC_API_KEY not set!")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

MODEL = "claude-haiku-4-5-20251001"


# ── Helper: Extract text from PDF ─────────────────────────────────────────
def extract_pdf_text(pdf_bytes):
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages[:30]:  # max 30 pages
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        return ""


# ── Helper: Call Claude ───────────────────────────────────────────────────
def call_claude(system_prompt, user_content, max_tokens=1024):
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}]
    )
    return response.content[0].text


# ── Routes ─────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    """Upload a document and extract its text"""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = file.filename
    content = file.read()

    try:
        if filename.lower().endswith(".pdf"):
            text = extract_pdf_text(content)
            if not text:
                return jsonify({"error": "PDF-ல text extract ஆகல. Image-based PDF-ஆ இருக்கலாம்."}), 400
        else:
            # TXT, MD, CSV, JSON, HTML, PY, JS etc.
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1")

        return jsonify({
            "success": True,
            "filename": filename,
            "text": text[:80000],  # limit
            "chars": len(text)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    """Q&A about the document"""
    data = request.json
    doc_text = data.get("doc_text", "")
    history = data.get("history", [])  # [{role, content}]
    question = data.get("question", "")

    if not doc_text:
        return jsonify({"error": "Document not loaded"}), 400
    if not question:
        return jsonify({"error": "Question is empty"}), 400

    system = f"""You are a document analysis expert. Here is the document content:

---
{doc_text[:12000]}
---

Answer questions based strictly on this document. Be precise, clear and helpful. If the answer is not in the document, say so."""

    # Build conversation for Claude
    recent = history[-6:]  # last 6 turns
    messages = recent + [{"role": "user", "content": question}]

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system,
            messages=messages
        )
        reply = response.content[0].text
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/summarize", methods=["POST"])
def summarize():
    """Generate document summary"""
    data = request.json
    doc_text = data.get("doc_text", "")

    if not doc_text:
        return jsonify({"error": "Document not loaded"}), 400

    try:
        result = call_claude(
            "You are an expert summarizer. Provide a clear, structured summary with bullet points highlighting all key ideas. Be comprehensive but concise.",
            f"Summarize this document:\n\n---\n{doc_text[:12000]}\n---",
            max_tokens=1024
        )
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/translate", methods=["POST"])
def translate():
    """Translate document content"""
    data = request.json
    doc_text = data.get("doc_text", "")
    target_lang = data.get("language", "Tamil")

    if not doc_text:
        return jsonify({"error": "Document not loaded"}), 400

    try:
        result = call_claude(
            f"You are a professional translator. Translate the given document into {target_lang}. Preserve the structure and meaning accurately.",
            f"Translate to {target_lang}:\n\n---\n{doc_text[:8000]}\n---",
            max_tokens=1024
        )
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/keypoints", methods=["POST"])
def keypoints():
    """Extract key points"""
    data = request.json
    doc_text = data.get("doc_text", "")

    if not doc_text:
        return jsonify({"error": "Document not loaded"}), 400

    try:
        result = call_claude(
            "You are an expert analyst. Extract all key points and important insights as a numbered list. Each point should have a brief explanation.",
            f"Extract key points from:\n\n---\n{doc_text[:12000]}\n---",
            max_tokens=1024
        )
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    print(f"  DocMind AI starting on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=debug)
