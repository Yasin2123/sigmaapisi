from flask import Flask, request, jsonify, Response
import json, os, uuid
from datetime import datetime, timedelta

app = Flask(__name__)

DATA_FILE = "keys.json"

# Başlangıç: keys.json yoksa oluştur ve Free key ekle
if not os.path.isfile(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([{
            "key": "FREESORGUPANELİ2026",
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

def temizle_gelmis_keys(keys):
    yeni_keys = []
    for k in keys:
        if k["key"] == "FREESORGUPANELİ2026":
            yeni_keys.append(k)
        elif k["expire"]:
            try:
                if datetime.fromisoformat(k["expire"]) > datetime.now():
                    yeni_keys.append(k)
            except:
                continue
        else:
            yeni_keys.append(k)
    return yeni_keys

SURELER = {
    "gunluk": timedelta(days=1),
    "haftalik": timedelta(weeks=1),
    "aylik": timedelta(days=30),
    "yillik": timedelta(days=365)
}

# ------------------ API ------------------

@app.route("/key/olustur/<tip>", methods=["GET"])
def key_olustur(tip):
    keys = load_keys()
    keys = temizle_gelmis_keys(keys)

    yeni_key = str(uuid.uuid4()).upper()

    if "_" in tip:
        rol, sure_key = tip.split("_", 1)
        expire = None
        if sure_key != "suresiz":
            if sure_key not in SURELER:
                return jsonify({"durum":"hata","mesaj":"Geçersiz süre tipi"}), 400
            expire = (datetime.now() + SURELER[sure_key]).isoformat()
    else:
        return jsonify({"durum":"hata","mesaj":"Tip formatı hatalı. Örn: admin_haftalik veya vip_suresiz"}), 400

    key_data = {
        "key": yeni_key,
        "rol": rol,
        "tip": sure_key,
        "olusturma_tarihi": datetime.now().isoformat(),
        "expire": expire
    }

    keys.append(key_data)
    save_keys(keys)

    return jsonify({"durum":"ok","key":yeni_key,"rol":rol,"tip":sure_key,"expire":expire})

@app.route("/key/kontrol", methods=["GET"])
def key_kontrol():
    key = request.args.get("key")
    keys = load_keys()
    keys = temizle_gelmis_keys(keys)
    save_keys(keys)

    for k in keys:
        if k["key"] == key:
            return jsonify({"gecerli": True, "rol": k["rol"], "tip": k["tip"], "expire": k["expire"]})
    return jsonify({"gecerli": False})

@app.route("/key/sil", methods=["GET"])
def key_sil():
    key = request.args.get("key")
    if key == "FREESORGUPANELİ2026":
        return jsonify({"durum":"hata","mesaj":"Free key silinemez"})

    keys = load_keys()
    yeni_keys = [k for k in keys if k["key"] != key]

    if len(yeni_keys) == len(keys):
        return jsonify({"durum":"hata","mesaj":"Key yok"})

    save_keys(yeni_keys)
    return jsonify({"durum":"ok"})

@app.route("/key/liste", methods=["GET"])
def key_liste():
    keys = load_keys()
    keys = temizle_gelmis_keys(keys)
    save_keys(keys)
    return jsonify(keys)

# ------------------ HTML ANA MENÜ ------------------

@app.route("/", methods=["GET"])
def index():
    html = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Sorgu Paneli</title>
<style>
    body { font-family: Arial, sans-serif; background: #f2f2f2; margin:0; padding:0; }
    header { background: #4CAF50; color: white; padding: 15px; text-align: center; }
    main { padding: 20px; max-width: 800px; margin: auto; background: white; margin-top: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    button { padding: 10px 15px; margin: 5px; cursor: pointer; border:none; border-radius:5px; background:#4CAF50; color:white; }
    input, select { padding:8px; margin:5px; }
    #output { background:#eee; padding:10px; margin-top:10px; border-radius:5px; white-space: pre-wrap; max-height:300px; overflow:auto; }
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

function olustur(){
    const tip = document.getElementById("keyTip").value;
    fetch(`${baseUrl}/key/olustur/${tip}`)
    .then(res => res.json())
    .then(data => { document.getElementById("output").innerText = JSON.stringify(data,null,2); });
}

function kontrol(){
    const key = document.getElementById("kontrolKey").value;
    fetch(`${baseUrl}/key/kontrol?key=${key}`)
    .then(res => res.json())
    .then(data => { document.getElementById("output").innerText = JSON.stringify(data,null,2); });
}

function sil(){
    const key = document.getElementById("silKey").value;
    fetch(`${baseUrl}/key/sil?key=${key}`)
    .then(res => res.json())
    .then(data => { document.getElementById("output").innerText = JSON.stringify(data,null,2); });
}

function listele(){
    fetch(`${baseUrl}/key/liste`)
    .then(res => res.json())
    .then(data => { document.getElementById("output").innerText = JSON.stringify(data,null,2); });
}
</script>
</body>
</html>
"""
    return Response(html, mimetype="text/html")

# ------------------ SUNUCU ------------------

if __name__=="__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
