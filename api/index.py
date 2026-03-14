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

# RUTE UTAMA (Biar gak 404 pas buka domain utama)
@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "ok", "message": "Backend SCI Group Active!"})

# RUTE ANALISIS
@app.route('/api/check', methods=['POST', 'OPTIONS'])
def check_linkedin():
    if request.method == 'OPTIONS': return jsonify({"status": "ok"}), 200

    data = request.json
    target = data.get('target') # misal: 'lsp-ditekindo' atau 'lsp-ekonomi-dan-bisreatif-65aa11322'
    is_company = data.get('isCompany', False) 
    
    EMAIL = os.environ.get('LINKEDIN_EMAIL')
    PASSWORD = os.environ.get('LINKEDIN_PASS')

    try:
        api = Linkedin(EMAIL or "dummy", PASSWORD or "dummy")
        
        if is_company:
            # Jalur khusus Company (DITEKINDO)
            posts = api.get_company_updates(public_id=target, container_count=1)
        else:
            # Jalur khusus Profile (EBISKRAF)
            posts = api.get_profile_posts(public_id=target, post_count=1)

        if not posts:
            return jsonify({"status": "success", "lastPost": None})

        timestamp = posts[0].get('createdAt') or posts[0].get('time')
        return jsonify({"status": "success", "lastPost": timestamp, "target": target})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500