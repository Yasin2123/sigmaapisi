from flask import Flask, request, jsonify
import json, os, uuid
from datetime import datetime, timedelta

app = Flask(__name__)

DATA_FILE = "keys.json"

if not os.path.isfile(DATA_FILE):
    # Free key başta ekleniyor
    with open(DATA_FILE, "w") as f:
        json.dump([{
            "key": "FREESORGUPANELİ2026",
            "rol": "free",
            "tip": "sabit",
            "olusturma_tarihi": datetime.now().isoformat(),
            "expire": None
        }], f, indent=2)

def load_keys():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_keys(keys):
    json.dump(keys, f, indent=2)

def temizle_gelmis_keys(keys):
    yeni_keys = []
    for k in keys:
        # Free key her zaman kalır
        if k["key"] == "FREESORGUPANELİ2026":
            yeni_keys.append(k)
        elif k["expire"]:
            if datetime.fromisoformat(k["expire"]) > datetime.now():
                yeni_keys.append(k)
        else:
            yeni_keys.append(k)
    return yeni_keys

SURELER = {
    "gunluk": timedelta(days=1),
    "haftalik": timedelta(weeks=1),
    "aylik": timedelta(days=30),
    "yillik": timedelta(days=365)
}

@app.route("/key/olustur/<tip>", methods=["POST"])
def key_olustur(tip):
    keys = load_keys()
    keys = temizle_gelmis_keys(keys)

    yeni_key = str(uuid.uuid4()).upper()

    if "_" in tip:
        rol, sure_key = tip.split("_", 1)
        expire = None
        if sure_key != "suresiz":
            if sure_key not in SURELER:
                return jsonify({"durum":"hata","mesaj":"Geçersiz süre tipi"}),400
            expire = (datetime.now() + SURELER[sure_key]).isoformat()
    else:
        return jsonify({"durum":"hata","mesaj":"Tip formatı hatalı. Örn: admin_haftalik veya vip_suresiz"}),400

    key_data = {
        "key": yeni_key,
        "rol": rol,      # admin, vip
        "tip": sure_key, # haftalik, gunluk, suresiz
        "olusturma_tarihi": datetime.now().isoformat(),
        "expire": expire
    }

    keys.append(key_data)
    save_keys(keys)

    return jsonify({"durum":"ok","key":yeni_key,"rol":rol,"tip":sure_key,"expire":expire})

@app.route("/key/kontrol")
def key_kontrol():
    key = request.args.get("key")
    keys = load_keys()
    keys = temizle_gelmis_keys(keys)
    save_keys(keys)

    for k in keys:
        if k["key"] == key:
            return jsonify({"gecerli": True, "rol": k["rol"], "tip": k["tip"], "expire": k["expire"]})
    return jsonify({"gecerli": False})

@app.route("/key/sil")
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

@app.route("/key/liste")
def key_liste():
    keys = load_keys()
    keys = temizle_gelmis_keys(keys)
    save_keys(keys)
    return jsonify(keys)

if __name__=="__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
