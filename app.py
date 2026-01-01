from flask import Flask, request, jsonify, Response
import json, os, random
from datetime import datetime, timedelta

app = Flask(__name__)

DATA_FILE = "keys.json"
FREE_KEY = "FREESORGUPANELİ2026"

# ------------------ DOSYA İŞLEMLERİ ------------------

def init_file():
    if not os.path.isfile(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([{
                "key": FREE_KEY,
                "rol": "free",
                "tip": "sabit",
                "olusturma_tarihi": datetime.now().isoformat(),
                "expire": None
            }], f, indent=2, ensure_ascii=False)

def load_keys():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_keys(keys):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f, indent=2, ensure_ascii=False)

init_file()

# ------------------ KEY ÜRETİCİ ------------------

KARAKTERLER = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

def generate_key(existing_keys, length=10):
    while True:
        key = "".join(random.choice(KARAKTERLER) for _ in range(length))
        if key not in existing_keys:
            return key

# ------------------ SÜRELER ------------------

SURELER = {
    "gunluk": timedelta(days=1),
    "haftalik": timedelta(weeks=1),
    "aylik": timedelta(days=30),
    "yillik": timedelta(days=365)
}

def temizle_expire(keys):
    yeni = []
    for k in keys:
        if k["key"] == FREE_KEY:
            yeni.append(k)
        elif k["expire"] is None:
            yeni.append(k)
        else:
            try:
                if datetime.fromisoformat(k["expire"]) > datetime.now():
                    yeni.append(k)
            except:
                pass
    return yeni

# ------------------ API ------------------

@app.route("/key/olustur/<tip>")
def key_olustur(tip):
    if "_" not in tip:
        return jsonify({"hata": "Tip hatalı (örn: admin_haftalik)"}), 400

    rol, sure = tip.split("_", 1)
    keys = temizle_expire(load_keys())

    mevcut_keyler = [k["key"] for k in keys]
    yeni_key = generate_key(mevcut_keyler, 10)

    expire = None
    if sure != "suresiz":
        if sure not in SURELER:
            return jsonify({"hata": "Geçersiz süre"}), 400
        expire = (datetime.now() + SURELER[sure]).isoformat()

    keys.append({
        "key": yeni_key,
        "rol": rol,
        "tip": sure,
        "olusturma_tarihi": datetime.now().isoformat(),
        "expire": expire
    })

    save_keys(keys)

    return jsonify({
        "durum": "ok",
        "key": yeni_key,
        "rol": rol,
        "tip": sure,
        "expire": expire
    })

@app.route("/key/kontrol")
def key_kontrol():
    key = request.args.get("key")
    keys = temizle_expire(load_keys())
    save_keys(keys)

    for k in keys:
        if k["key"] == key:
            return jsonify({
                "gecerli": True,
                "rol": k["rol"],
                "tip": k["tip"],
                "expire": k["expire"]
            })
    return jsonify({"gecerli": False})

@app.route("/key/sil")
def key_sil():
    key = request.args.get("key")
    if key == FREE_KEY:
        return jsonify({"hata": "Free key silinemez"})

    keys = load_keys()
    yeni = [k for k in keys if k["key"] != key]

    if len(yeni) == len(keys):
        return jsonify({"hata": "Key bulunamadı"})

    save_keys(yeni)
    return jsonify({"durum": "silindi"})

@app.route("/key/liste")
def key_liste():
    keys = temizle_expire(load_keys())
    save_keys(keys)
    return jsonify(keys)

# ------------------ HTML ANA MENÜ ------------------

@app.route("/")
def index():
    return Response("""
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Sorgu Paneli</title>
<style>
body{font-family:Arial;background:#f4f4f4}
main{background:#fff;padding:20px;max-width:800px;margin:40px auto;border-radius:10px}
button{padding:8px 12px;margin:5px}
input,select{padding:6px}
pre{background:#eee;padding:10px;max-height:300px;overflow:auto}
</style>
</head>
<body>
<main>
<h2>Sorgu Paneli</h2>

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
<button onclick="olustur()">Key Oluştur</button>

<hr>

<input id="k" placeholder="Key">
<button onclick="kontrol()">Kontrol</button>
<button onclick="sil()">Sil</button>
<button onclick="liste()">Liste</button>

<pre id="out"></pre>
</main>

<script>
const api = location.origin;
const out = document.getElementById("out");

function olustur(){
 fetch(api+"/key/olustur/"+tip.value).then(r=>r.json()).then(d=>out.textContent=JSON.stringify(d,null,2))
}
function kontrol(){
 fetch(api+"/key/kontrol?key="+k.value).then(r=>r.json()).then(d=>out.textContent=JSON.stringify(d,null,2))
}
function sil(){
 fetch(api+"/key/sil?key="+k.value).then(r=>r.json()).then(d=>out.textContent=JSON.stringify(d,null,2))
}
function liste(){
 fetch(api+"/key/liste").then(r=>r.json()).then(d=>out.textContent=JSON.stringify(d,null,2))
}
</script>
</body>
</html>
""", mimetype="text/html")

# ------------------ SERVER ------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
