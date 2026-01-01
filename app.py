from flask import Flask, request, jsonify
import json, os, uuid
from datetime import datetime, timedelta

app = Flask(__name__)

DATA_FILE = "keys.json"

# JSON yoksa oluştur
if not os.path.isfile(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f, indent=2)

def load_keys():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_keys(keys):
    with open(DATA_FILE, "w") as f:
        json.dump(keys, f, indent=2)

def temizle_gelmis_keys(keys):
    """Süresi dolan keyleri sil ve sadece geçerli veya süresiz keyleri bırak"""
    yeni_keys = []
    for k in keys:
        if k["expire"]:
            if datetime.fromisoformat(k["expire"]) > datetime.now():
                yeni_keys.append(k)
        else:
            yeni_keys.append(k)
    return yeni_keys

@app.route("/key/olustur/<tip>", methods=["POST"])
def key_olustur(tip):
    keys = load_keys()
    keys = temizle_gelmis_keys(keys)
    
    yeni_key = str(uuid.uuid4()).upper()
    expire = None
    if tip=="gunluk":
        expire = (datetime.now() + timedelta(days=1)).isoformat()
    elif tip=="haftalik":
        expire = (datetime.now() + timedelta(weeks=1)).isoformat()
    elif tip=="aylik":
        expire = (datetime.now() + timedelta(days=30)).isoformat()
    elif tip=="yillik":
        expire = (datetime.now() + timedelta(days=365)).isoformat()
    elif tip in ["admin","sinirsiz"]:
        expire = None

    key_data = {
        "key": yeni_key,
        "tip": tip,
        "olusturma_tarihi": datetime.now().isoformat(),
        "expire": expire
    }
    keys.append(key_data)
    save_keys(keys)
    return jsonify({"durum":"ok","key":yeni_key,"tip":tip,"expire":expire})

@app.route("/key/kontrol")
def key_kontrol():
    key = request.args.get("key")
    keys = load_keys()
    keys = temizle_gelmis_keys(keys)
    save_keys(keys)
    
    for k in keys:
        if k["key"] == key:
            return jsonify({"gecerli": True, "tip": k["tip"], "expire": k["expire"]})
    return jsonify({"gecerli": False})

@app.route("/key/sil")
def key_sil():
    key = request.args.get("key")
    keys = load_keys()
    yeni_keys = [k for k in keys if k["key"] != key]
    
    if len(yeni_keys) == len(keys):
        return jsonify({"durum":"hata","mesaj":"Key yok"})
    
    save_keys(yeni_keys)
    return jsonify({"durum":"ok"})

@app.route("/key/liste")
def key_liste():
    keys = load_keys()
    keys = temizle_gelmis_keys(keys)
    save_keys(keys)
    return jsonify(keys)

if __name__=="__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
