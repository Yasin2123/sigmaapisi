from flask import Flask, request, jsonify, Response
import json, os, random, string
from datetime import datetime, timedelta

app = Flask(__name__)

DATA_FILE = "keys.json"
FREE_KEY = "FREESORGUPANELİ2026A"

SURELER = {
    "gunluk": timedelta(days=1),
    "haftalik": timedelta(days=7),
    "aylik": timedelta(days=30),
    "yillik": timedelta(days=365)
}

# ------------------ YARDIMCI ------------------

def generate_key(length=20):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))

def save_keys(keys):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f, indent=2, ensure_ascii=False)

def load_keys():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            keys = json.load(f)
    else:
        keys = []

    # Free key HER ZAMAN olsun
    if not any(k["key"] == FREE_KEY for k in keys):
        keys.append({
            "key": FREE_KEY,
            "rol": "free",
            "tip": "sabit",
            "olusturma": datetime.now().isoformat(),
            "expire": None
        })
        save_keys(keys)

    return keys

def key_aktif_mi(k):
    if k["expire"] is None:
        return True
    try:
        return datetime.fromisoformat(k["expire"]) > datetime.now()
    except:
        return False

# ------------------ API ------------------

@app.route("/key/olustur/<tip>")
def key_olustur(tip):
    if "_" not in tip:
        return jsonify({"durum": "hata", "mesaj": "Format: vip_gunluk / admin_suresiz"})

    rol, sure = tip.split("_", 1)
    expire = None

    if sure != "suresiz":
        if sure not in SURELER:
            return jsonify({"durum": "hata", "mesaj": "Geçersiz süre"})
        expire = (datetime.now() + SURELER[sure]).isoformat()

    keys = load_keys()
    yeni_key = generate_key(20)

    keys.append({
        "key": yeni_key,
        "rol": rol,
        "tip": sure,
        "olusturma": datetime.now().isoformat(),
        "expire": expire
    })

    save_keys(keys)

    return jsonify({
        "durum": "aktif",
        "key": yeni_key,
        "rol": rol,
        "tip": sure,
        "expire": expire
    })

@app.route("/key/kontrol")
def key_kontrol():
    key = request.args.get("key")
    keys = load_keys()

    for k in keys:
        if k["key"] == key:
            if key_aktif_mi(k):
                return jsonify({
                    "durum": "aktif",
                    "rol": k["rol"],
                    "tip": k["tip"],
                    "expire": k["expire"]
                })
            else:
                return jsonify({"durum": "gecersiz"})

    return jsonify({"durum": "gecersiz"})

@app.route("/key/sil")
def key_sil():
    key = request.args.get("key")
    if key == FREE_KEY:
        return jsonify({"durum": "hata", "mesaj": "Free key silinemez"})

    keys = load_keys()
    yeni = [k for k in keys if k["key"] != key]

    if len(yeni) == len(keys):
        return jsonify({"durum": "gecersiz"})

    save_keys(yeni)
    return jsonify({"durum": "ok"})

@app.route("/key/liste")
def key_liste():
    keys = load_keys()
    sonuc = []

    for k in keys:
        sonuc.append({
            **k,
            "durum": "aktif" if key_aktif_mi(k) else "gecersiz"
        })

    return jsonify(sonuc)

# ------------------ HTML ------------------

@app.route("/")
def index():
    return Response("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Key Panel</title>
</head>
<body>
<h2>Key Panel</h2>

<select id="tip">
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

<button onclick="olustur()">Oluştur</button><br><br>

<input id="key" placeholder="Key">
<button onclick="kontrol()">Kontrol</button>
<button onclick="sil()">Sil</button>
<br><br>

<button onclick="liste()">Liste</button>

<pre id="out"></pre>

<script>
const base = location.origin;

function olustur(){
 fetch(base+"/key/olustur/"+tip.value)
 .then(r=>r.json()).then(d=>out.innerText=JSON.stringify(d,null,2))
}
function kontrol(){
 fetch(base+"/key/kontrol?key="+key.value)
 .then(r=>r.json()).then(d=>out.innerText=JSON.stringify(d,null,2))
}
function sil(){
 fetch(base+"/key/sil?key="+key.value)
 .then(r=>r.json()).then(d=>out.innerText=JSON.stringify(d,null,2))
}
function liste(){
 fetch(base+"/key/liste")
 .then(r=>r.json()).then(d=>out.innerText=JSON.stringify(d,null,2))
}
</script>
</body>
</html>
""", mimetype="text/html")

# ------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
