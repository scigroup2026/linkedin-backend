from flask import Flask, request, jsonify
from flask_cors import CORS
import os

# Import library LinkedIn
from linkedin_api import Linkedin
from linkedin_api.client import Client

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 1. ILMU HITAM: Kita bajak fungsi 'authenticate' bawaan library LinkedIn
# Biar dia nggak login pakai email/password, tapi langsung nyuntikkin Cookies!
def hack_authenticate(self, username, password):
    li_at = os.environ.get('LI_AT', '')
    jsessionid = os.environ.get('JSESSIONID', '')
    
    # Masukin cookies ke sesi browser virtual
    self.session.cookies.set("li_at", li_at, domain=".linkedin.com")
    self.session.cookies.set("JSESSIONID", jsessionid, domain=".linkedin.com")
    
    # CSRF Token butuh JSESSIONID tanpa tanda kutip
    self.session.headers["csrf-token"] = jsessionid.strip('"')

# Timpa fungsi aslinya dengan fungsi bajakan kita
Client.authenticate = hack_authenticate

@app.route('/api/check', methods=['GET', 'POST', 'OPTIONS'])
def check_linkedin():
    if request.method == 'GET':
        return jsonify({"status": "ok", "message": "Endpoint ini siap nerima POST data!"})

@app.route('/api/check', methods=['POST'])
def check_linkedin():
    EMAIL = os.environ.get('LINKEDIN_EMAIL')
    LI_AT = os.environ.get('LI_AT')
    JSESSIONID = os.environ.get('JSESSIONID')
    PROXY_URL = os.environ.get('PROXY_URL')
    
    if not LI_AT or not JSESSIONID:
        return jsonify({"status": "error", "message": "Cookies LI_AT atau JSESSIONID belum disetting di Vercel!"})

    data = request.json
    target = data.get('target')
    
    if not target:
        return jsonify({"status": "error", "message": "Target kosong cuy."})

    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

    try:
        # 2. Panggil API. Karena udah dibajak, parameter dummy ini bakal diabaikan
        # dan sistem langsung pakai Cookies kamu.
        api = Linkedin("dummy_email", "dummy_pass", proxies=proxies)
        
        # Tarik data postingan target (Mau akun profil atau Company kayak Ditekindo, harusnya tembus!)
        posts = api.get_profile_posts(target)
        
        if not posts:
            return jsonify({"status": "success", "lastPost": None})
        
        if 'createdAt' in posts[0]:
            timestamp_ms = posts[0]['createdAt'] 
            return jsonify({"status": "success", "lastPost": timestamp_ms})
        
        return jsonify({"status": "error", "message": "Timestamp nggak nemu nih."})
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error scraping: {str(e)}"})