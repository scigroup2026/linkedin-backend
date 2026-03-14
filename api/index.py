from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from linkedin_api import Linkedin
from linkedin_api.client import Client

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Logic Override Auth LinkedIn
def hack_authenticate(self, username, password):
    li_at = os.environ.get('LI_AT', '')
    jsessionid = os.environ.get('JSESSIONID', '')
    self.session.cookies.set("li_at", li_at, domain=".linkedin.com")
    self.session.cookies.set("JSESSIONID", jsessionid, domain=".linkedin.com")
    self.session.headers["csrf-token"] = jsessionid.strip('"')

Client.authenticate = hack_authenticate

@app.route('/api/check', methods=['POST', 'OPTIONS'])
def check_linkedin():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    LI_AT = os.environ.get('LI_AT')
    JSESSIONID = os.environ.get('JSESSIONID')
    
    if not LI_AT or not JSESSIONID:
        return jsonify({"status": "error", "message": "Backend: Env Cookies Not Set"}), 500

    data = request.json
    target = data.get('target') if data else None
    
    if not target:
        return jsonify({"status": "error", "message": "Target empty"}), 400

    try:
        api = Linkedin("", "") # Email/Pass dummy karena pakai cookies
        posts = api.get_profile_posts(public_id=target, count=1)
        
        last_post = posts[0].get('createdAt') if posts and len(posts) > 0 else None
        
        return jsonify({
            "status": "success",
            "lastPost": last_post,
            "target": target
        })
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/health')
def health():
    return jsonify({"status": "online"})