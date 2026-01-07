# yorumlayici.py
# Soru: Bu Python dosyası ne yapacak?
# Cevap: Bir satırdaki CTG (fetal kalp atım) verilerini tıbbi açıdan yorumlayacak,
# risk seviyesini belirleyecek ve klinik notlar üretecek.

import numpy as np

class clsYorumlayici:
    def __init__(self, grup_ortalamalari):
        """
        grup_ortalamalari: fetal_health sınıflarına göre sütun ortalamalarını içeren DataFrame
        (veri.groupby('fetal_health').mean() ile oluşturulmuş)
        """
        self.grup_ort = grup_ortalamalari

    def _grup_adi(self, etiket):
        if etiket == 1:
            return "Normal"
        elif etiket == 2:
            return "Şüpheli"
        elif etiket == 3:
            return "Patolojik"
        else:
            return "Bilinmiyor"

    def satir_analiz_et(self, satir, model_tahmin_etiket=None):
        """
        satir : pandas Series (tek satır)
        model_tahmin_etiket : modelin tahmin ettiği fetal_health (1,2,3)
        çıktı: sözlük (dict) -> risk_seviyesi, klinik_notlar, kisa_ozet, grup_karsilastirma
        """
        notlar = []
        klinik_yorum = ""
        yakin_grup = ""
        baseline = satir["baseline value"]
        acc = satir["accelerations"]
        uterine = satir["uterine_contractions"]
        light_dec = satir["light_decelerations"]
        severe_dec = satir["severe_decelerations"]
        prolong_dec = satir["prolongued_decelerations"]
        width = satir["histogram_width"]
        mode = satir["histogram_mode"]
        min_hist = satir["histogram_min"]
        max_hist = satir["histogram_max"]
        mean_hist = satir["histogram_mean"]

        # --- 1) Baseline kalp atım hızı değerlendirmesi ---
        if baseline < 110:
            notlar.append(f"Fetal kalp atım hızı (baseline={baseline}) düşük, bradikardi / hipoksi riski olabilir.")
        elif baseline > 160:
            notlar.append(f"Fetal kalp atım hızı (baseline={baseline}) yüksek, taşikardi ve enfeksiyon / stres ihtimali var.")
        else:
            notlar.append(f"Fetal kalp atım hızı (baseline={baseline}) normal aralıkta (110-160 bpm).")

        # --- 2) Hızlanmalar (accelerations) ---
        if acc < 0.002:
            notlar.append(
                f"Hızlanmalar (accelerations={acc:.3f}) oldukça az, fetal oksijenlenme açısından dikkatle izlenmeli."
            )
        else:
            notlar.append(
                f"Hızlanmalar (accelerations={acc:.3f}) yeterli, bu genelde iyi fetal durum göstergesidir."
            )

        # --- 3) Yavaşlamalar (decelerations) ve kontraksiyon ---
        if prolong_dec > 0 or severe_dec > 0:
            notlar.append(
                "Uzamış veya şiddetli yavaşlamalar mevcut, fetal distress ve akut hipoksi açısından yüksek risk."
            )
        elif light_dec > 0:
            notlar.append(
                "Hafif yavaşlamalar var, uterin kontraksiyonlarla ilişkili olabilir; klinik durumla birlikte değerlendirilmelidir."
            )
        else:
            notlar.append("Belirgin patolojik yavaşlama (deceleration) gözlenmiyor.")

        if uterine > 0.01:
            notlar.append(f"Uterin kontraksiyon düzeyi (uterine_contractions={uterine:.3f}) belirgin, doğum eylemiyle uyumlu olabilir.")

        # --- 4) Histogram / Variability ---
        if width < 30:
            notlar.append(
                f"Histogram genişliği (width={width}) dar, beat-to-beat variabilite azalmış, kronik hipoksi riski olabilir."
            )
        elif width > 50:
            notlar.append(
                f"Histogram genişliği (width={width}) oldukça geniş, variabilite artmış; genelde iyi bir bulgu ancak aşırı ise irritabilite göstergesi olabilir."
            )
        else:
            notlar.append(
                f"Histogram genişliği (width={width}) orta düzeyde, variabilite çoğunlukla fizyolojik sınırlar içinde."
            )

        if mean_hist < 110 or mean_hist > 160:
            notlar.append(
                f"Histogram ortalaması (mean={mean_hist}) normal referansların dışında, temel ritim kayması olabilir."
            )

        # --- 5) Normal / Patolojik gruplara yakınlık kıyaslaması ---
        grup_karsilastirma = {}
        if 1 in self.grup_ort.index and 3 in self.grup_ort.index:
            normal_ort = self.grup_ort.loc[1]
            patolojik_ort = self.grup_ort.loc[3]

            # Sadece birkaç önemli sütun üzerinden mesafe hesabı (Euclidean)
            onemli_sutunlar = [
                "baseline value",
                "accelerations",
                "uterine_contractions",
                "prolongued_decelerations",
                "histogram_width",
                "histogram_mean",
            ]

            satir_vec = satir[onemli_sutunlar].values.astype(float)
            norm_vec = normal_ort[onemli_sutunlar].values.astype(float)
            pat_vec = patolojik_ort[onemli_sutunlar].values.astype(float)

            mesafe_normal = float(np.linalg.norm(satir_vec - norm_vec))
            mesafe_patolojik = float(np.linalg.norm(satir_vec - pat_vec))

            if mesafe_normal < mesafe_patolojik:
                yakin_grup = "Normal profile daha yakın"
            else:
                yakin_grup = "Patolojik profile daha yakın"

            if 'yakin_grup' not in locals():
                yakin_grup = "Belirsiz"

            grup_karsilastirma = {
                "mesafe_normal": round(mesafe_normal, 3),
                "mesafe_patolojik": round(mesafe_patolojik, 3),
                "yorum": yakin_grup

            }

        sinif = int(model_tahmin_etiket)

        if sinif in [1,2] and yakin_grup == "Normal profile daha yakın":
            klinik_yorum = (
                "Model şüpheli/normal sınıf veriyor ve ölçümler normale yakın. "
                "Ani risk sinyali yok. Rutin kontrol ve fetal hareket izlemi yeterli olabilir."
            )

        elif sinif in [1,2] and yakin_grup == "Patolojik profile daha yakın":
            klinik_yorum = (
            "Sınıf normal/şüpheli olmasına rağmen ölçümler patolojik kümeye yakın. "
            "Bu durum ilerleyici risk göstergesi olabilir. Klinik kontrol sıklaştırılmalı."
            )

        elif sinif == 3 and yakin_grup == "Normal profile daha yakın":
            klinik_yorum = (
            "Model patolojik olmasına rağmen ölçümler normal profile daha yakın. "
            "Bu durum sınırda vakayı işaret edebilir. Tekrar CTG/USG ile doğrulama önerilir."
            )

        elif sinif == 3 and yakin_grup == "Patolojik profile daha yakın":
            klinik_yorum = (
            "Patolojik sınıf ve patolojik profile yakınlık birlikte mevcut. "
            "Bu yüksek riskli olasılıktır. Perinatoloji değerlendirmesi ve yakın fetal izlem gerekir."
            )


        # --- 6) Genel risk seviyesi karar ağacı (basit ama klinik mantıklı) ---
        risk_puan = 0
        if baseline < 110 or baseline > 160:
            risk_puan += 2
        if acc < 0.002:
            risk_puan += 1
        if severe_dec > 0:
            risk_puan += 3
        if prolong_dec > 0:
            risk_puan += 3
        if width < 30:
            risk_puan += 2

        if risk_puan <= 2:
            risk_seviyesi = "Düşük Risk (çoğunlukla fizyolojik)"
        elif risk_puan <= 5:
            risk_seviyesi = "Orta Risk (yakın takip önerilir)"
        else:
            risk_seviyesi = "Yüksek Risk (fetal distress olasılığı)"

        # --- 7) Kısa özet metni ---
        model_yorum = ""
        if model_tahmin_etiket is not None:
            model_yorum = f"Model tahmini: {self._grup_adi(int(model_tahmin_etiket))} (sınıf {int(model_tahmin_etiket)}). "

        kisa_ozet = (
            f"{model_yorum}"
            f"Genel klinik değerlendirmeye göre durum: {risk_seviyesi}. "
            f"Normal ve patolojik gruplara olan benzerlik: {grup_karsilastirma.get('yorum', 'Veri yetersiz')}."
        )

        return {
            "risk_seviyesi": risk_seviyesi,
            "klinik_notlar": notlar,
            "kisa_ozet": kisa_ozet,
            "grup_karsilastirma": grup_karsilastirma,
            "klinik_profil": klinik_yorum,
        }
    # --- Klinik Yorum Modülü ---

def figo_skoru(satir):
    baseline = satir["baseline value"]
    accel = satir["accelerations"]
    severe = satir["severe_decelerations"]
    prolong = satir["prolongued_decelerations"]
    width = satir["histogram_width"]

    if 110 <= baseline <= 160 and accel > 0 and severe == 0 and prolong == 0 and width > 30:
        return "Normal"
    elif severe > 0 or prolong > 0 or baseline < 110 or baseline > 160:
        return "Patolojik"
    else:
        return "Şüpheli"


def nichd_skoru(satir):
    accel = satir["accelerations"]
    width = satir["histogram_width"]
    severe = satir["severe_decelerations"]

    if accel > 0 and width > 30 and severe == 0:
        return "Category I (Normal)"
    elif severe > 0 or width < 20:
        return "Category III (Abnormal)"
    else:
        return "Category II (Indeterminate)"


def hipoksi_risk_puani(satir):
    puan = 0

    if satir["baseline value"] < 110 or satir["baseline value"] > 160:
        puan += 2
    if satir["accelerations"] == 0:
        puan += 2
    if satir["prolongued_decelerations"] > 0:
        puan += 3
    if satir["severe_decelerations"] > 0:
        puan += 3
    if satir["histogram_width"] < 30:
        puan += 2

    if puan <= 2:
        seviye = "Düşük"
    elif puan <= 6:
        seviye = "Orta"
    else:
        seviye = "Yüksek"

    return {"puan": puan, "seviye": seviye}

def kolon_analizi(satir):
    tablo = {}

    # Baseline
    b = satir["baseline value"]
    if b < 110 or b > 160:
        tablo["baseline value"] = {
            "deger": float(b),
            "durum": "Abnormal",
            "aciklama": "Hipoksi / Taşikardi riski"
        }
    else:
        tablo["baseline value"] = {
            "deger": float(b),
            "durum": "Normal",
            "aciklama": "110–160 bpm aralığı"
        }

    # Accelerations
    a = satir["accelerations"]
    if a == 0:
        tablo["accelerations"] = {
            "deger": float(a),
            "durum": "Abnormal",
            "aciklama": "Fetal oksijen yokluğu"
        }
    elif a < 0.002:
        tablo["accelerations"] = {
            "deger": float(a),
            "durum": "Borderline",
            "aciklama": "Düşük hızlanma — dikkat"
        }
    else:
        tablo["accelerations"] = {
            "deger": float(a),
            "durum": "Normal",
            "aciklama": "İyi oksijenlenme"
        }

    # Decelerations
    sd = satir["severe_decelerations"]
    pd = satir["prolongued_decelerations"]
    if sd > 0 or pd > 0:
        tablo["decelerations"] = {
            "deger": float(sd + pd),
            "durum": "Abnormal",
            "aciklama": "Fetal distress"
        }
    else:
        tablo["decelerations"] = {
            "deger": 0.0,
            "durum": "Normal",
            "aciklama": "Ciddi deselerasyon yok"
        }

    # Variability (width)
    w = satir["histogram_width"]
    if w < 30:
        tablo["variability"] = {
            "deger": float(w),
            "durum": "Abnormal",
            "aciklama": "Beat-to-beat variability ↓"
        }
    else:
        tablo["variability"] = {
            "deger": float(w),
            "durum": "Normal",
            "aciklama": "Fizyolojik aralık"
        }

    # Histogram mean
    hm = satir["histogram_mean"]
    if hm < 110 or hm > 160:
        tablo["hist_mean"] = {
            "deger": float(hm),
            "durum": "Borderline",
            "aciklama": "Ritim kayması"
        }
    else:
        tablo["hist_mean"] = {
            "deger": float(hm),
            "durum": "Normal",
            "aciklama": "110–160 bpm ortalama"
        }

    return tablo


def neuro_risk_score(satir):
    
    puan = 0

    # Baseline
    b = satir["baseline value"]
    if b < 110 or b > 160:
        puan += 2

    # Accelerations
    if satir["accelerations"] == 0:
        puan += 2

    # Decelerations
    if satir["prolongued_decelerations"] > 0:
        puan += 3
    if satir["severe_decelerations"] > 0:
        puan += 3

    # Low variability
    if satir["histogram_width"] < 30:
        puan += 2

    # Sonuç seviyeleri
    if puan <= 2:
        seviye = "Düşük" 
    elif puan < 6:
        seviye = "Orta"
    else:
        seviye = "Yüksek"

    return {"puan": puan, "seviye": seviye}


def klinik_column_et(column, value):
    """
    value: numeric fetüs değeri
    column: sütun adı
    döner: {"durum": "Normal/Border/Abnormal", "aciklama": "..."}
    """
    durum = "Normal"
    aciklama = ""

    # Baseline value
    if column == "baseline value":
        if value < 110 or value > 160:
            if value < 100 or value > 160:
                durum = "Abnormal"
                aciklama = f"Baseline ({value}) çok anormal – riskli."
            else:
                durum = "Border"
                aciklama = f"Baseline ({value}) sınırda."
        else:
            aciklama = f"Baseline ({value}) normal aralıkta."

    # Accelerations
    elif column == "accelerations":
        if value == 0:
            durum = "Abnormal"
            aciklama = "Accelerations yok – fetal oksijenlenme açısından risk."
        elif value < 0.002:
            durum = "Border"
            aciklama = "Accelerations düşük – dikkat."
        else:
            aciklama = "Accelerations yeterli."

    # Severe / Prolongued Decelerations
    elif column in ["severe_decelerations", "prolongued_decelerations"]:
        if value > 0:
            durum = "Abnormal"
            aciklama = f"{column} ({value}) mevcut – ciddi yavaşlama."
        else:
            aciklama = f"{column} yok."

    # Histogram Width
    elif column == "histogram_width":
        if value < 30:
            durum = "Abnormal"
            aciklama = "Histogram genişliği ({value}) dar – riskli."
        elif value < 40:
            durum = "Border"
            aciklama = "Histogram genişliği sınırda."
        else:
            aciklama = "Histogram genişliği normal."

    # Diğer sütunlar için basit normal kabul
    else:
        aciklama = f"{column}: {value}"

    return {"durum": durum, "aciklama": aciklama}


def kiyaslama(figo, nichd, hipoksi):
    durum = ""
    aciklama = ""

    if figo == "Patolojik":
        if "III" in nichd:
            durum = "Tam Uyum (Yüksek Risk)"

            aciklama = ("FIGO ve NICHD değerlendirmeleri fetüste belirgin CTG bozulması olduğunu göstermektedir. "
            "Kalp atım paterni, variabilite ve deselerasyon bulguları fetal distress ile uyumludur.")

        elif hipoksi["seviye"] == "Yüksek":
            durum = "Uyumlu (Hipoksi ile artmış risk)"
            aciklama = ("FIGO değerlendirmesi CTG paterninde bozulmaya işaret etmektedir. "
            "Eşlik eden yüksek hipoksi riski fetüsün oksijenlenmesinde azalma olabileceğini düşündürür.")


        else:
            durum = "Kısmi Uyum"
            aciklama = ("FIGO kriterlerine göre CTG paterninde bozulma bulguları mevcuttur. "
            "Ancak NICHD henüz ileri risk göstermemektedir. Bulgular erken evre veya sınırda olabilir."
            )

    elif figo == "Normal":
        if "III" in nichd:
            durum = "Çelişki"
            aciklama = ("CTG bulguları kılavuzlara göre farklı yorumlanmaktadır. Bulgular sınırdadır ve tek başına kesin risk kararı vermek için yeterli değildir.")
        elif hipoksi["seviye"] == "Yüksek":
            durum = "Şüpheli"
            aciklama = ( "CTG paternleri FIGO’ya göre normal sınırlar içinde olsa da, "
            "hipoksi riskinin yüksek olması fetüsün oksijenlenmesi açısından gizli risk düşündürür."
            )
        else:
            durum = "Tam Uyum (Normal)"
            aciklama = "Tüm kılavuzlar normal seviyede."

    else:
        durum = "Ara Değerlendirme"
        aciklama = "Kesin tanı yok. Klinik yakın takip gerekebilir."

    return {"durum": durum, "aciklama": aciklama}
    
