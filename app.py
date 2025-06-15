from flask import Flask, request, jsonify
import yt_dlp
import re
import tempfile
import os

app = Flask(__name__)

def clean_subtitles(text):
    text = re.sub(r"^(WEBVTT|Kind:.*|Language:.*)$", "", text, flags=re.MULTILINE)
    text = re.sub(r"</?c>", "", text)
    text = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", text)
    text = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}", "", text)
    return text.strip()

@app.route("/subtitle", methods=["GET"])
def extract_subtitle():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts = {
            "writesubtitles": True,
            "skip_download": True,
            "subtitleslangs": ["ko", "en"],
            "subtitlesformat": "vtt",
            "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_id = info["id"]
                vtt_path = os.path.join(tmpdir, f"{video_id}.ko.vtt")
                if not os.path.exists(vtt_path):
                    vtt_path = os.path.join(tmpdir, f"{video_id}.en.vtt")
                if not os.path.exists(vtt_path):
                    return jsonify({"error": "No subtitles found"}), 404

                with open(vtt_path, "r", encoding="utf-8") as f:
                    raw = f.read()
                    clean = clean_subtitles(raw)
                    return jsonify({"subtitle": clean})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

# ✅ 서버 포트 바인딩 (Render에서 필수)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
