from flask import Flask, request, jsonify
import json, os, uuid
from datetime import datetime, timedelta

app = Flask(__name__)

# Kalıcı dosya
DATA_FILE = "keys.json"

# JSON dosyası yoksa oluştur
if not os.path.isfile(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

def load_keys():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_keys(keys):
    with open(DATA_FILE, "w") as f:
        json.dump(keys, f, indent=2)

@app.route("/key/olustur/<tip>", methods=["POST"])
def key_olustur(tip):
    keys = load_keys()
    yeni_key = str(uuid.uuid4()).upper()
    expire = None
    if tip=="gunluk":
        expire=(datetime.now()+timedelta(days=1)).isoformat()
    elif tip=="haftalik":
        expire=(datetime.now()+timedelta(weeks=1)).isoformat()
    elif tip=="aylik":
        expire=(datetime.now()+timedelta(days=30)).isoformat()
    elif tip=="yillik":
        expire=(datetime.now()+timedelta(days=365)).isoformat()
    elif tip in ["admin","sinirsiz"]:
        expire=None

    keys.append({
        "key":yeni_key,
        "tip":tip,
        "aktif":True,
        "olusturma_tarihi":datetime.now().isoformat(),
        "expire":expire
    })
    save_keys(keys)
    return jsonify({"durum":"ok","key":yeni_key,"tip":tip,"expire":expire})

@app.route("/key/kontrol")
def key_kontrol():
    key = request.args.get("key")
    keys = load_keys()
    for k in keys:
        if k["key"]==key:
            if k["expire"] and datetime.fromisoformat(k["expire"])<datetime.now():
                k["aktif"]=False
                save_keys(keys)
            return jsonify({"gecerli":k["aktif"],"tip":k["tip"],"expire":k["expire"]})
    return jsonify({"gecerli":False})

@app.route("/key/sil")
def key_sil():
    key=request.args.get("key")
    keys=load_keys()
    new_keys=[k for k in keys if k["key"]!=key]
    if len(new_keys)==len(keys):
        return jsonify({"durum":"hata","mesaj":"Key yok"})
    save_keys(new_keys)
    return jsonify({"durum":"ok"})

@app.route("/key/liste")
def key_liste():
    return jsonify(load_keys())

if __name__=="__main__":
    app.run(host="0.0.0.0",port=10000)
