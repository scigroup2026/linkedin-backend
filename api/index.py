from flask import Flask, request, jsonify
from flask_cors import CORS
import os

# Import library LinkedIn
from linkedin_api import Linkedin
from linkedin_api.client import Client

app = Flask(__name__)
# CORS diatur agar bisa ditembak dari domain frontend mana pun
CORS(app, resources={r"/*": {"origins": "*"}})

# --- FUNGSI ADAPTASI AUTH (COOKIES INJECTION) ---
# Mengganti fungsi authenticate bawaan agar langsung menggunakan session cookies
def hack_authenticate(self, username, password):
    li_at = os.environ.get('LI_AT', '')
    jsessionid = os.environ.get('JSESSIONID', '')
    
    # Masukkan cookies ke sesi browser virtual
    self.session.cookies.set("li_at", li_at, domain=".linkedin.com")
    self.session.cookies.set("JSESSIONID", jsessionid, domain=".linkedin.com")
    
    # CSRF Token biasanya diambil dari JSESSIONID tanpa tanda kutip
    self.session.headers["csrf-token"] = jsessionid.strip('"')

# Timpa fungsi asli library dengan fungsi bajakan kita
Client.authenticate = hack_authenticate

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "ok", "message": "Backend LinkedIn Bulk Analyzer is running!"})

@app.route('/api/check', methods=['POST', 'OPTIONS'])
def check_linkedin():
    # Menangani preflight request dari browser
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    # Ambil data identitas dari Environment Variables Vercel
    LI_AT = os.environ.get('LI_AT')
    JSESSIONID = os.environ.get('JSESSIONID')
    PROXY_URL = os.environ.get('PROXY_URL')
    
    if not LI_AT or not JSESSIONID:
        return jsonify({"status": "error", "message": "Konfigurasi Auth (LI_AT/JSESSIONID) hilang!"}), 500

    # Ambil payload dari frontend
    data = request.json
    target = data.get('target') if data else None
    
    if not target:
        return jsonify({"status": "error", "message": "Target username/ID kosong."}), 400

    # Konfigurasi Proxy jika ada
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

    try:
        # Inisialisasi API (Otomatis memanggil hack_authenticate)
        # Parameter email & pass diisi dummy karena kita pakai cookies
        api = Linkedin("dummy", "dummy", proxies=proxies)
        
        # Ambil postingan profil (Adaptasi untuk performa: ambil 1-2 post saja)
        # Catatan: Library linkedin-api versi terbaru terkadang mengubah argumennya.
        # Jika 'get_profile_posts' error, backend akan menangkapnya di block 'except'.
        posts = api.get_profile_posts(public_id=target)
        
        if not posts or len(posts) == 0:
            return jsonify({
                "status": "success", 
                "lastPost": None, 
                "followers": None, 
                "connections": None
            })
        
        # Ambil postingan terbaru (post pertama dalam list)
        latest_post = posts[0]
        
        # Ambil timestamp (createdAt adalah milidetik standar di LinkedIn)
        # Ini akan langsung dibaca oleh parseToMillisecondsAgo di frontend
        timestamp_ms = latest_post.get('createdAt')
        
        return jsonify({
            "status": "success",
            "lastPost": timestamp_ms,
            "target": target
        })
            
    except Exception as e:
        # Menangani error spesifik jika library tidak mendukung argumen 'count' atau session expired
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg:
            return jsonify({"status": "error", "message": "Sesi LinkedIn habis. Perbarui LI_AT!"}), 401
        
        return jsonify({"status": "error", "message": f"Scraping Error: {error_msg}"}), 500