from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from linkedin_api import Linkedin
from linkedin_api.client import Client

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- HYBRID AUTH LOGIC ---
def hack_authenticate(self, username, password):
    li_at = os.environ.get('LI_AT')
    jsessionid = os.environ.get('JSESSIONID')
    if li_at and jsessionid:
        self.session.cookies.set("li_at", li_at, domain=".linkedin.com")
        self.session.cookies.set("JSESSIONID", jsessionid, domain=".linkedin.com")
        self.session.headers["csrf-token"] = jsessionid.strip('"')
    else:
        return self._old_authenticate(username, password)

Client._old_authenticate = Client.authenticate
Client.authenticate = hack_authenticate

@app.route('/api/check', methods=['POST', 'OPTIONS'])
def check_linkedin():
    if request.method == 'OPTIONS': return jsonify({"status": "ok"}), 200

    EMAIL = os.environ.get('LINKEDIN_EMAIL')
    PASSWORD = os.environ.get('LINKEDIN_PASS')
    PROXY_URL = os.environ.get('PROXY_URL')
    
    data = request.json
    target = data.get('target') # Username atau Company ID
    is_company = data.get('isCompany', False) # Flag untuk bedain tipe
    
    if not target:
        return jsonify({"status": "error", "message": "Target kosong"}), 400

    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

    try:
        api = Linkedin(EMAIL or "dummy", PASSWORD or "dummy", proxies=proxies)
        
        posts = []
        if is_company:
            # Gunakan fungsi khusus Company
            print(f"Scraping Company: {target}")
            posts = api.get_company_updates(public_id=target, container_count=1)
        else:
            # Gunakan fungsi khusus Profile Pribadi
            print(f"Scraping Profile: {target}")
            posts = api.get_profile_posts(public_id=target, post_count=1)

        if not posts:
            return jsonify({"status": "success", "lastPost": None, "message": "Tidak ada post ditemukan"})

        # Ambil timestamp (LinkedIn biasanya pakai 'createdAt' atau 'time')
        last_post = posts[0]
        timestamp = last_post.get('createdAt') or last_post.get('time')
        
        return jsonify({
            "status": "success",
            "lastPost": timestamp,
            "target": target,
            "type": "Company" if is_company else "Profile"
        })
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Endpoint khusus buat kamu test di browser langsung
@app.route('/api/test', methods=['GET'])
def test_scraping():
    return jsonify({
        "info": "Gunakan POST ke /api/check dengan JSON body",
        "contoh_ebiskraf_profile": {
            "target": "lsp-ekonomi-dan-bisreatif-65aa11322",
            "isCompany": false
        },
        "contoh_ditekindo_company": {
            "target": "lsp-ditekindo",
            "isCompany": true
        }
    })