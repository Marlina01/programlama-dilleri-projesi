#app.py
# Soru: Bu Python dosyası ne yapacak?
# Cevap: Flask ile bir web sunucusu çalıştıracak, fetal_health.csv verisini okuyacak,
# eğitilmiş modeli ve yorumlayıcıyı yükleyip:
# - /satirlar   : tabloda gösterilecek satırları
# - /analiz     : seçilen satır için tıbbi analiz ve model tahmini

# endpoint'leriyle front-end'e JSON olarak gönderecek.
import os
import sys
from flask import Flask, jsonify, request, send_file
import pandas as pd
import joblib
from yorumlayici import clsYorumlayici
from yorumlayici import figo_skoru, nichd_skoru, hipoksi_risk_puani, kiyaslama
from yorumlayici import kolon_analizi, neuro_risk_score


# Flask uygulamasını oluştur
# static_folder='.' ve static_url_path='' -> aynı klasördeki style.css, script.js vb. direkt servis edilir
uygulama = Flask(__name__, static_folder='.', static_url_path='')

# Veriyi yükle
veri = pd.read_csv("fetal_health.csv", encoding="utf-8")
veri.reset_index(drop=True, inplace=True)
veri["satir_id"] = veri.index + 1  # index'i ayrı bir sütun olarak tutmak için
veri.rename(columns={"index": "satir_id"}, inplace=True)

# Grup ortalamaları (fetal_health sınıflarına göre)
grup_ortalamalari = veri.groupby("fetal_health").mean(numeric_only=True)

# Modeli yükle
model = joblib.load("tahmin_model.pkl")

# Yorumlayıcıyı hazırla
yorumlayici = clsYorumlayici(grup_ortalamalari)

# Kullanacağımız özellik sütunları (modelle aynı sırada)
hedef_etiket = "fetal_health"
ozellik_sutunlari = [s for s in veri.columns if s not in ["satir_id", hedef_etiket]]

@uygulama.route("/")
def ana_sayfa():
    # index.html dosyasını gönder
    return send_file("index.html")

@uygulama.route("/satirlar")
def satirlar():
    alt_veri = veri.copy()
    kolon_sirasi = list(veri.columns)

    sonuc_liste = []
    for _, row in alt_veri.iterrows():
        sonuc = {col: row[col] for col in kolon_sirasi}
        sonuc_liste.append(sonuc)

    return jsonify({
        "kolonlar": kolon_sirasi,
        "satirlar": sonuc_liste
    })

    



@uygulama.route("/analiz", methods=["GET"])
def analiz():
    """
    Tek bir satır için:
    - gerçek fetal_health
    - model tahmini
    - tıbbi yorumlar
    - FIGO / NICHD / hipoksi skoru
    - kiyaslama (kılavuzlar arası)
    döndürür.
    """
    try:
        satir_id = int(request.args.get("satir_id"))
    except (TypeError, ValueError):
        return jsonify({"hata": "satir_id parametresi eksik veya hatalı."}), 400

    satir_df = veri.loc[veri["satir_id"] == satir_id]
    if satir_df.empty:
        return jsonify({"hata": "Bu satir_id için kayıt bulunamadı."}), 404

    satir = satir_df.iloc[0]

    # Model tahmini
    X_satir = satir[ozellik_sutunlari].values.reshape(1, -1)
    tahmin = model.predict(X_satir)[0]
    olasiliklar = model.predict_proba(X_satir)[0]

    figo_sonuc=figo_skoru(satir)
    nichd_sonuc=nichd_skoru(satir)
    hipoksi_sonuc=hipoksi_risk_puani(satir)
    
    # Yorumlayıcı
    yorum = yorumlayici.satir_analiz_et(satir, model_tahmin_etiket=tahmin)

    cevap = {
        "satir_id": int(satir["satir_id"]),
        "gercek_sinif": int(satir[hedef_etiket]),
        "tahmin_sinif": int(tahmin),
        "tahmin_olasiliklari": {
            "sinif_1_normal": float(olasiliklar[0]),
            "sinif_2_supheli": float(olasiliklar[1]),
            "sinif_3_patolojik": float(olasiliklar[2]),
        },
        "yorum": yorum,
        "figo": figo_skoru(satir),
        "nichd": nichd_skoru(satir),
        "hipoksi": hipoksi_risk_puani(satir),
        "kolon_analizi": kolon_analizi(satir),
        "neuro_risk": neuro_risk_score(satir),
        "kiyaslama": kiyaslama(
            figo_sonuc,
            nichd_sonuc,
            hipoksi_sonuc
        )

    
    }
    

    return jsonify(cevap)



    karsilastirma_listesi = []
    for sutun in onemli_sutunlar:
        karsilastirma_listesi.append({
            "ozellik": sutun,
            "satir1_deger": float(satir1[sutun]),
            "satir2_deger": float(satir2[sutun]),
            "fark": float(satir2[sutun] - satir1[sutun])
        })

    cevap = {
        "satir1": {
            "satir_id": int(satir1["satir_id"]),
            "gercek_sinif": int(satir1[hedef_etiket]),
            "tahmin_sinif": int(tahmin1),
            "yorum": yorum1,
        },
        "satir2": {
            "satir_id": int(satir2["satir_id"]),
            "gercek_sinif": int(satir2[hedef_etiket]),
            "tahmin_sinif": int(tahmin2),
            "yorum": yorum2,
        },
        "karsilastirma": karsilastirma_listesi
    }

    return jsonify(cevap)

@uygulama.route("/model_grafik_veri")
def model_grafik_veri():
    importances = model.feature_importances_
    labels = ozellik_sutunlari

    return jsonify({
        "labels": labels,
        "values": importances.tolist()
    })


if __name__ == "__main__":
    # Debug=True: geliştirme sırasında hataları görmen için
    uygulama.run(debug=True)
