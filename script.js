//script.js
// Soru: Bu JavaScript dosyası ne yapacak?
// Cevap: Backend'deki Flask API'lerine ( /satirlar, /analiz, /kiyasla ) istek atacak,
// tabloyu oluşturacak, kullanıcı satır seçince analiz ve kıyaslama sonuçlarını gösterecek.

let seciliSatir1 = null;
let seciliSatir2 = null;

// Sayfa yüklendiğinde satırları çek
document.addEventListener("DOMContentLoaded", () => {
    satirlariGetir();
});

function satirlariGetir() {
    fetch("/satirlar?adet=300")
        .then(yanit => yanit.json())
        .then(veri => {
            tabloyuDoldur(veri.satirlar, veri.kolonlar);
        })
        .catch(hata => {
            console.error("Satırlar alınırken hata:", hata);
        });
}

function tabloyuDoldur(satirlar, kolonlar) {
    const govde = document.getElementById("tabloGovde");
    const baslik = document.getElementById("tabloBaslik");
    govde.innerHTML = "";
    baslik.innerHTML = "";

    if (satirlar.length === 0 || kolonlar.length===0) return;

    const idIndex = kolonlar.indexOf("satir_id");
    if (idIndex > -1) {
        kolonlar.splice(idIndex, 1);  
        kolonlar.unshift("satir_id"); 
    }
    
// İngilizce → Türkçe karşılık tablosu
    const ceviri = {
        "satir_id": "ID",
        "baseline value": "Bazal Değer",
        "accelerations": "Hızlanma",
        "fetal_movement": "Fetal Hareket",
        "uterine_contractions": "Uterin Kontraksiyon",
        "light_decelerations": "Hafif Deselerasyon",
        "severe_decelerations": "Şiddetli Deselerasyon",
        "prolongued_decelerations": "Uzamış Deselerasyon",
        "abnormal_short_term_variability": "Kısa Dönem Varyabilite",
        "mean_value_of_short_term_variability": "Ortalama Kısa Dönem Varyabilite",
        "percentage_of_time_with_abnormal_long_term_variability": "Uzun Dönem Varyabilite % Süresi",
        "mean_value_of_long_term_variability": "Ortalama Uzun Dönem Varyabilite",
        "histogram_width": "Histogram Genişliği",
        "histogram_min": "Histogram Min",
        "histogram_max": "Histogram Max",
        "histogram_number_of_peaks": "Histogram Tepe Sayısı",
        "histogram_number_of_zeroes": "Histogram Sıfır Sayısı",
        "histogram_mode": "Histogram Mod",
        "histogram_mean": "Histogram Ortalama",
        "histogram_median": "Histogram Medyan",
        "histogram_variance": "Histogram Varyans",
        "histogram_tendency": "Histogram Eğilim",
        "fetal_health": "Fetal Sağlık",
        
    };

// Başlıkları yaz
    let baslikHtml = "<tr>";
    kolonlar.forEach(k => {

        baslikHtml += `<th>${ceviri[k]|| k}</th>`;
    });
    baslikHtml += `<th>Analiz</th></tr>`;
    baslik.innerHTML = baslikHtml;


    // --- ROWS ---
    satirlar.forEach(satir => {
        const tr = document.createElement("tr");

        kolonlar.forEach(k => {
            let deger = satir[k];
            if (typeof deger === "number")
                deger = Number.isInteger(deger) ? deger : deger.toFixed(3);
            ekleHucre(tr, deger);
        });
        // Analiz butonu
        const tdAnaliz = document.createElement("td");
        const btnAnaliz = document.createElement("button");
        btnAnaliz.textContent = "Analiz";
        btnAnaliz.className = "btn btn-analiz";
        btnAnaliz.onclick = () => analizIste(satir.satir_id);
        tdAnaliz.appendChild(btnAnaliz);
        tr.appendChild(tdAnaliz);

        govde.appendChild(tr);
    });
    }


function ekleHucre(tr, icerik) {
    const td = document.createElement("td");
    td.textContent = icerik;
    tr.appendChild(td);
}

function analizIste(satirId) {
    fetch(`/analiz?satir_id=${satirId}`)
        .then(yanit => yanit.json())
        .then(veri => {
            if (veri.hata) {
                analizYaz(`<p class="hata">${veri.hata}</p>`);
                return;
            }
            analizSonucGoster(veri);
        })
        .catch(hata => {
            console.error("Analiz hatası:", hata);
        });
}

function analizYaz(htmlMetin) {
    const kutu = document.getElementById("analizSonuc");
    kutu.innerHTML = htmlMetin;
}

function analizSonucGoster(veri) {
    const kutu = document.getElementById("analizSonuc");

    const gercek = veri.gercek_sinif;
    const tahmin = veri.tahmin_sinif;
    const olas = veri.tahmin_olasiliklari;
    const yorum = veri.yorum;

    let renkSinif = "roz";
    if (tahmin === 1) renkSinif = "yesil";
    else if (tahmin === 2) renkSinif = "turuncu";
    else if (tahmin === 3) renkSinif = "kirmizi";

    let html = `
        <h3>Satır ID: ${veri.satir_id}</h3>
        <p><strong>Gerçek Sınıf:</strong> ${gercek}</p>
        <p><strong>Model Tahmini:</strong> 
            <span class="rozet ${renkSinif}">Sınıf ${tahmin}</span>
        </p>

        <div class="klinik-skorlar">
            <p><strong>FIGO:</strong> ${veri.figo}</p>
            <p><strong>NICHD:</strong> ${veri.nichd}</p>
            <p><strong>Hipoksi Riski:</strong> ${veri.hipoksi.puan}/12 → ${veri.hipoksi.seviye}</p>
        </div>

        <h4>Tahmin Olasılıkları</h4>
        <ul>
            <li>Normal (1): ${(olas.sinif_1_normal * 100).toFixed(1)}%</li>
            <li>Şüpheli (2): ${(olas.sinif_2_supheli * 100).toFixed(1)}%</li>
            <li>Patolojik (3): ${(olas.sinif_3_patolojik * 100).toFixed(1)}%</li>
        </ul>

        <h4>Genel Risk Değerlendirmesi</h4>
        <p><strong>${yorum.risk_seviyesi}</strong></p>
        <p>${yorum.kisa_ozet}</p>
        <h4>Klinik Notlar</h4>
        <ul>
    `;

    yorum.klinik_notlar.forEach(not => {
        html += `<li>${not}</li>`;
    });

    if (yorum.grup_karsilastirma && yorum.grup_karsilastirma.yorum) {
        html += `
            </ul>
            <h4>Normal / Patolojik Profile Yakınlık</h4>
            <p>Normal'e mesafe: ${yorum.grup_karsilastirma.mesafe_normal}</p>
            <p>Patolojik'e mesafe: ${yorum.grup_karsilastirma.mesafe_patolojik}</p>
            <p><em>${yorum.grup_karsilastirma.yorum}</em></p>
        `;
    } 
    else {
        html += `</ul>`;
    }

    if (yorum.klinik_profil) {
    html += `
        <h4>Klinik Öneri</h4>
        <p><em>${yorum.klinik_profil}</em></p>
        `;
    }


    html += `
    <h4>Kılavuzlar Arası Uyum</h4>
    <p><strong>${veri.kiyaslama.durum}</strong></p>
    <p>${veri.kiyaslama.aciklama}</p>
    `;

    html += `
    <button class="btn detay-btn" onclick="sutunAlarmlariniGoster()">📊 Klinik Alarm Tablosu</button>
    <button class="btn detay-btn" onclick="neuroRiskGoster()">🧠 Nörolojik Risk Skoru</button>
    
    `;


    window.sonAnaliz = veri;
    kutu.innerHTML = html;
    document.querySelector(".ana-icerik")
    .scrollIntoView({ behavior: "smooth", block: "start" })
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function sutunAlarmlariniGoster() {
    pencereTemizle();
    const pencere = document.getElementById("klinikPencere");
    const kolonlar = window.sonAnaliz.kolon_analizi;

    let html = `
        <span class="kapat" onclick="pencereKapat('klinikPencere')">✖</span>
        <h3>📊 Klinik Alarm Tablosu</h3>
        <table class="kiyas-tablo">
            <thead>
                <tr>
                    <th>Parametre</th>
                    <th>Değer</th>
                    <th>Durum</th>
                    <th>Açıklama</th>
                </tr>
            </thead>
            <tbody>
    `;

    Object.entries(kolonlar).forEach(([col, obj]) => {
        html += `
            <tr>
                <td>${col}</td>
                <td>${obj.deger}</td>
                <td>${obj.durum}</td>
                <td>${obj.aciklama}</td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;
    pencere.innerHTML = html;
    pencere.style.display = "block";
}



function neuroRiskGoster() {

    pencereTemizle();
    const pencere = document.getElementById("neuroPencere");
    const nr = window.sonAnaliz.neuro_risk;

    let aciklama = "";
    let oneri = "";

    if (nr.seviye === "Düşük") {
        aciklama = `
            Bu skor, fetüsün nörolojik açıdan fizyolojik sınırlar içinde olduğunu gösterir.
            Kalp atım hızı varyabilitesi, hızlanmalar ve yavaşlamalar sinir sistemi tarafından uygun şekilde kontrol edilmektedir.
            Oksijenlenme ile ilgili belirgin bir stres bulgusu yoktur.

            Bu durum, fetüsün otonom sinir sistemi yanıtlarının sağlıklı olduğunu düşündürür.
        `;
        oneri = ` Rutin gebelik takibine devam edilir
                    Ek acil müdahale gerekmez
                    Anne günlük yaşamına normal şekilde devam edebilir
                    Kontroller standart gebelik takvimine uygun yapılır
                    Not: Klinik tablo değişirse yeniden değerlendirme yapılmalıdır.`;
    }
    else if (nr.seviye === "Orta") {
        aciklama = `
            Bu skor, fetüste hafif–orta düzeyde nörolojik stres olabileceğini düşündürür.
            Kalp atım paternlerinde varyabilite azalması, sınırlı hızlanmalar veya hafif yavaşlamalar görülebilir.
            Bu durum kesin bir patoloji anlamına gelmez, ancak fetüsün rezerv kapasitesinin azalmaya başladığını gösterebilir.
        `;
        oneri = `Yakın izlem önerilir
            CTG değerlendirmeleri daha sık yapılmalıdır
            Anne:
            Aşırı fiziksel efordan kaçınmalıdır
            Uzun süre ayakta kalmamalıdır
            Düzenli dinlenmelidir
            Klinik tablo kötüleşirse ileri değerlendirme planlanır`;
    }
    else if (nr.seviye === "Yüksek") {
        aciklama = `
        Bu skor, fetüsün nörolojik açıdan belirgin stres altında olabileceğini düşündürür.
        Kalp atım paternleri oksijenlenmeye yeterli yanıt vermeyebilir ve sinir sistemi regülasyonu bozulmuş olabilir.
        Bu durum, uzamış hipoksi riskine bağlı nörolojik etkilenme ihtimalini artırır.
        `;
        oneri = `Tıbbi değerlendirme gereklidir
                Perinatoloji / kadın-doğum uzmanı değerlendirmesi önerilir
                Sürekli veya sık CTG izlemi yapılmalıdır
                Anne:
                Fiziksel aktivitesini sınırlandırmalıdır
                Stres faktörlerinden uzak durmalıdır
                Klinik duruma göre ileri tanısal yöntemler planlanabilir`;
    }

    let html = `
        <span class="kapat" onclick="pencereKapat('neuroPencere')">✖</span>
        <h3>🧠 Nörolojik Risk Skoru</h3>

        <p><strong>Puan:</strong> ${nr.puan}/12</p>
        <p><strong>Seviye:</strong> ${nr.seviye}</p>

        <hr>

        <h4>Nörolojik Risk Değerlendirmesi</h4>
        <p>${aciklama}</p>

        <h4>Öneri</h4>
        <p><strong>${oneri}</strong></p>
    `;

    pencere.innerHTML = html;
    pencere.style.display = "block";


}

function pencereKapat(id) {
document.getElementById(id).style.display = "none"
}

function pencereTemizle() {
    document.getElementById("klinikPencere").style.display = "none";
    document.getElementById("neuroPencere").style.display = "none";
}



document.addEventListener("DOMContentLoaded", () => {
    fetch("/model_grafik_veri")
        .then(res => res.json())
        .then(veri => grafikCiz(veri));
});

function grafikCiz(veri) {
    const ctx = document.getElementById("featureChart");
    if (!ctx) return;

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: veri.labels,
            datasets: [{
                label: "Özellik Önemi",
                data: veri.values,
                backgroundColor: "#2563eb"
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => `Önem Skoru: ${ctx.raw.toFixed(3)}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: "Göreceli Önem" }
                }
            }
        }
    });
}

