from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from linkedin_api import Linkedin
from linkedin_api.client import Client

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- HYBRID AUTH ---
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

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "ok", "message": "Backend SCI Active!"})

@app.route('/api/check', methods=['POST', 'OPTIONS'])
def check_linkedin():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Payload JSON kosong"}), 400
            
        target = data.get('target')
        is_company = data.get('isCompany', False)
        
        if not target:
            return jsonify({"status": "error", "message": "Target kosong"}), 400

        # Gunakan 'dummy' jika Env belum diisi
        api = Linkedin(os.environ.get('LINKEDIN_EMAIL', 'dummy'), 
                       os.environ.get('LINKEDIN_PASS', 'dummy'))
        
        # PANGGILAN API TANPA ARGUMEN COUNT (Biar gak crash 500)
        if is_company:
            posts = api.get_company_updates(public_id=target)
        else:
            posts = api.get_profile_posts(public_id=target)

        if not posts:
            return jsonify({"status": "success", "lastPost": None, "message": "Kosong"})

        # LinkedIn mengembalikan list, ambil yang pertama (terbaru)
        latest = posts[0]
        timestamp = latest.get('createdAt') or latest.get('time')
        
        return jsonify({
            "status": "success", 
            "lastPost": timestamp, 
            "message": "Data berhasil ditarik"
        })
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server Error: {str(e)}"}), 500