from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from linkedin_api import Linkedin
from linkedin_api.client import Client

app = Flask(__name__)
# CORS super longgar supaya bisa dipanggil dari Gemini Canvas atau Localhost mana pun
CORS(app, resources={r"/*": {"origins": "*"}})

# --- JALUR NINJA AUTH (COOKIES) ---
def hack_authenticate(self, username, password):
    li_at = os.environ.get('LI_AT', '')
    jsessionid = os.environ.get('JSESSIONID', '')
    self.session.cookies.set("li_at", li_at, domain=".linkedin.com")
    self.session.cookies.set("JSESSIONID", jsessionid, domain=".linkedin.com")
    self.session.headers["csrf-token"] = jsessionid.strip('"')

Client.authenticate = hack_authenticate

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "message": "LinkedIn API Backend is Live!",
        "mode": "Cookies Injection"
    })

@app.route('/api/check', methods=['POST', 'OPTIONS'])
def check_linkedin():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    # Ambil Config dari Vercel Env
    LI_AT = os.environ.get('LI_AT')
    JSESSIONID = os.environ.get('JSESSIONID')
    PROXY_URL = os.environ.get('PROXY_URL')
    
    data = request.json
    target = data.get('target') if data else None
    
    if not target:
        return jsonify({"status": "error", "message": "Target username/ID kosong."}), 400

    if not LI_AT or not JSESSIONID:
        return jsonify({"status": "error", "message": "Backend Error: LI_AT/JSESSIONID belum diset di Vercel."}), 500

    # Setup Proxy jika ada
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

    try:
        # Inisialisasi API (Otomatis pakai cookies via hack_authenticate)
        api = Linkedin("", "", proxies=proxies)
        
        # Ambil hanya 1 postingan terbaru (count=1) agar cepat dan irit resource
        posts = api.get_profile_posts(public_id=target, count=1)
        
        if not posts or len(posts) == 0:
            return jsonify({
                "status": "success",
                "lastPost": None,
                "message": "No public posts found."
            })
        
        # Ambil timestamp milidetik
        latest_post = posts[0]
        timestamp = latest_post.get('createdAt') or latest_post.get('postedAtTime')
        
        return jsonify({
            "status": "success",
            "target": target,
            "lastPost": timestamp
        })
            
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg:
            return jsonify({"status": "error", "message": "Session Expired. Update LI_AT baru di Vercel!"}), 401
        return jsonify({"status": "error", "message": f"Scraping failed: {error_msg}"}), 500