import json, os, random, string
from flask import Flask, jsonify, request, Response

app = Flask(__name__)

KEYS_FILE = "keys.json"

# keys.json varsa oku, yoksa oluştur
if os.path.exists(KEYS_FILE):
    with open(KEYS_FILE, "r") as f:
        KEYS = json.load(f)
else:
    KEYS = {}

def save_keys():
    with open(KEYS_FILE, "w") as f:
        json.dump(KEYS, f, indent=2)

def generate_short_key(length=10):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))

# ------------------ API ------------------

@app.route("/key/olustur/<tip>")
def olustur(tip):
    key = generate_short_key(10)
    
    if "gunluk" in tip:
        expire = 1
    elif "haftalik" in tip:
        expire = 7
    elif "aylik" in tip:
        expire = 30
    elif "yillik" in tip:
        expire = 365
    else:
        expire = None  # süresiz
    
    KEYS[key] = {"tip": tip, "expire": expire}
    save_keys()
    
    return jsonify({"durum":"basarili","key":key,"tip":tip,"expire":expire})

@app.route("/key/kontrol")
def kontrol():
    key = request.args.get("key")
    if key in KEYS:
        return jsonify({"gecerli": True, **KEYS[key]})
    return jsonify({"gecerli": False})

@app.route("/key/sil")
def sil():
    key = request.args.get("key")
    if key in KEYS:
        KEYS.pop(key)
        save_keys()
        return jsonify({"durum":"silindi","key":key})
    return jsonify({"durum":"bulunamadi","key":key})

@app.route("/key/liste")
def liste():
    return jsonify(KEYS)

# ------------------ HTML ANA MENÜ ------------------

@app.route("/", methods=["GET"])
def index():
    html = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Sorgu Paneli</title>
<style>
    body {{ font-family: Arial, sans-serif; background: #f2f2f2; margin:0; padding:0; }}
    header {{ background: #4CAF50; color: white; padding: 15px; text-align: center; }}
    main {{ padding: 20px; max-width: 800px; margin: auto; background: white; margin-top: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
    button {{ padding: 10px 15px; margin: 5px; cursor: pointer; border:none; border-radius:5px; background:#4CAF50; color:white; }}
    input, select {{ padding:8px; margin:5px; }}
    #output {{ background:#eee; padding:10px; margin-top:10px; border-radius:5px; white-space: pre-wrap; max-height:300px; overflow:auto; }}
</style>
</head>
<body>
<header>
    <h1>Sorgu Paneli</h1>
</header>
<main>
    <h2>Key İşlemleri</h2>

    <div>
        <label>Key Tipi:</label>
        <select id="keyTip">
            <option value="vip_gunluk">VIP Günlük</option>
            <option value="vip_haftalik">VIP Haftalık</option>
            <option value="vip_aylik">VIP Aylık</option>
            <option value="vip_yillik">VIP Yıllık</option>
            <option value="vip_suresiz">VIP Süresiz</option>
            <option value="admin_gunluk">Admin Günlük</option>
            <option value="admin_haftalik">Admin Haftalık</option>
            <option value="admin_aylik">Admin Aylık</option>
            <option value="admin_yillik">Admin Yıllık</option>
            <option value="admin_suresiz">Admin Süresiz</option>
        </select>
        <button onclick="olustur()">Oluştur</button>
    </div>

    <div>
        <label>Key Kontrol:</label>
        <input type="text" id="kontrolKey" placeholder="Key girin">
        <button onclick="kontrol()">Kontrol Et</button>
    </div>

    <div>
        <label>Key Sil:</label>
        <input type="text" id="silKey" placeholder="Key girin">
        <button onclick="sil()">Sil</button>
    </div>

    <div>
        <button onclick="listele()">Tüm Keyleri Listele</button>
    </div>

    <h3>Sonuç:</h3>
    <div id="output">Sonuç burada görünecek...</div>
</main>

<script>
const baseUrl = window.location.origin;

function olustur(){{
    const tip = document.getElementById("keyTip").value;
    fetch(`${{baseUrl}}/key/olustur/${{tip}}`)
    .then(res => res.json())
    .then(data => {{ document.getElementById("output").innerText = JSON.stringify(data,null,2); }});
}}

function kontrol(){{
    const key = document.getElementById("kontrolKey").value;
    fetch(`${{baseUrl}}/key/kontrol?key=${{key}}`)
    .then(res => res.json())
    .then(data => {{ document.getElementById("output").innerText = JSON.stringify(data,null,2); }});
}}

function sil(){{
    const key = document.getElementById("silKey").value;
    fetch(`${{baseUrl}}/key/sil?key=${{key}}`)
    .then(res => res.json())
    .then(data => {{ document.getElementById("output").innerText = JSON.stringify(data,null,2); }});
}}

function listele(){{
    fetch(`${{baseUrl}}/key/liste`)
    .then(res => res.json())
    .then(data => {{ document.getElementById("output").innerText = JSON.stringify(data,null,2); }});
}}
</script>
</body>
</html>
"""
    return Response(html, mimetype="text/html")

# ------------------ SUNUCU ------------------

if __name__=="__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
