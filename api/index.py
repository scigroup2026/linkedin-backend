from flask import Flask, request, jsonify
from flask_cors import CORS
from linkedin_api import Linkedin
import os

app = Flask(__name__)
# Wajib pakai CORS biar nggak diblokir pas dipanggil dari HTML kamu
CORS(app)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "ok", "message": "Backend Vercel is running, ges!"})

@app.route('/api/check', methods=['POST'])
def check_linkedin():
    # Ngambil credential dari Vercel Environment Variables biar aman
    EMAIL = os.environ.get('LINKEDIN_EMAIL')
    PASSWORD = os.environ.get('LINKEDIN_PASS')
    PROXY_URL = os.environ.get('PROXY_URL') # Opsional, tapi highly recommended
    
    if not EMAIL or not PASSWORD:
        return jsonify({"status": "error", "message": "Oops, Email/Password belum di-set di Vercel!"})

    data = request.json
    target = data.get('target')
    
    if not target:
        return jsonify({"status": "error", "message": "Kasih target username dulu dong."})

    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

    try:
        api = Linkedin(EMAIL, PASSWORD, proxies=proxies)
        posts = api.get_profile_posts(target)
        
        if not posts:
            return jsonify({"status": "success", "lastPost": None})
        
        if 'createdAt' in posts[0]:
            timestamp_ms = posts[0]['createdAt'] 
            return jsonify({"status": "success", "lastPost": timestamp_ms})
        
        return jsonify({"status": "error", "message": "Timestamp nggak nemu nih."})
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error scraping: {str(e)}"})

# Follow this account for life and love tips