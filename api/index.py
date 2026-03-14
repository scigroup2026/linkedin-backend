from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from linkedin_api import Linkedin
from linkedin_api.client import Client

app = Flask(__name__)
# Izinkan CORS untuk semua rute agar HTML lokal bisa akses
CORS(app, resources={r"/*": {"origins": "*"}})

# 1. ILMU HITAM: Override fungsi authenticate
def hack_authenticate(self, username, password):
    li_at = os.environ.get('LI_AT', '')
    jsessionid = os.environ.get('JSESSIONID', '')
    
    self.session.cookies.set("li_at", li_at, domain=".linkedin.com")
    self.session.cookies.set("JSESSIONID", jsessionid, domain=".linkedin.com")
    self.session.headers["csrf-token"] = jsessionid.strip('"')

Client.authenticate = hack_authenticate

# 2. ROUTE TUNGGAL (Digabung agar tidak bentrok)
@app.route('/api/check', methods=['GET', 'POST', 'OPTIONS'])
def check_linkedin():
    # Jika browser cuma ngetes lewat link (GET)
    if request.method == 'GET':
        return jsonify({"status": "ok", "message": "Backend Cookies SIAP!"})

    # Jika dipanggil dari kodingan HTML (POST)
    LI_AT = os.environ.get('LI_AT')
    JSESSIONID = os.environ.get('JSESSIONID')
    PROXY_URL = os.environ.get('PROXY_URL')
    
    if not LI_AT or not JSESSIONID:
        return jsonify({"status": "error", "message": "Cookies belum diset di Environment Vercel!"})

    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Payload JSON tidak ditemukan."})
        
    target = data.get('target')
    if not target:
        return jsonify({"status": "error", "message": "Target username kosong."})

    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

    try:
        api = Linkedin("dummy", "dummy", proxies=proxies)
        posts = api.get_profile_posts(target)
        
        if not posts:
            return jsonify({"status": "success", "lastPost": None})
        
        if 'createdAt' in posts[0]:
            return jsonify({"status": "success", "lastPost": posts[0]['createdAt']})
        
        return jsonify({"status": "error", "message": "Timestamp tidak ditemukan."})
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"Scraping error: {str(e)}"})

# Tambahan route root agar tidak muncul 404 di halaman utama vercel
@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Vercel Python is Live!"})