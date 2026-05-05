# 🌾 Hassas Tarım Karar Destek Sistemi (KDS)

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red.svg)
![Optimization](https://img.shields.io/badge/Optimization-PuLP-green.svg)
![AI](https://img.shields.io/badge/AI-Qwen_2.5-orange.svg)

Bu proje, tarım yöneticilerinin kısıtlı bütçe, arazi kısıtları ve değişken iklim koşulları altında karşılaştığı karmaşık karar süreçlerini optimize etmek amacıyla geliştirilmiş bir **Yapay Zeka Destekli Karar Destek Sistemidir (KDS)**.

## 📌 Proje Özeti
Geleneksel tarımda kararlar genellikle sezgilere dayalı alınır. Bu sistem; Doğrusal Programlama (Linear Programming) mantığını kullanarak riski (don, kuraklık) minimize edip beklenen net kârı maksimize edecek en verimli ekim planını matematiksel olarak hesaplar[cite: 5, 6]. Ayrıca entegre **Qwen 2.5 AI** motoru ile bu sayısal sonuçları yöneticiye stratejik bir danışman diliyle açıklar[cite: 4, 5].

## 🚀 Temel Özellikler
*   **Dinamik Optimizasyon:** PuLP kütüphanesi kullanılarak bütçe, su kısıtı, toprak uyumu ve iklim limitlerine göre tarlalar için en kârlı ürün desenini bulur[cite: 7].
*   **What-If (Duyarlılık) Analizi:** Kullanıcı arayüzü üzerinden tohum maliyetlerindeki enflasyon, su krizi şiddeti ve don olasılığı gibi parametreler değiştirilerek farklı senaryolar anlık test edilebilir[cite: 2, 5].
*   **AI Destekli Karar Yorumlama:** Sayısal sonuçlar, yerel **Qwen 2.5** entegrasyonu sayesinde "Gölge Fiyat (Shadow Price)" analizi yapılarak finansal ve operasyonel önerilere dönüştürülür[cite: 4, 5].
*   **Çoklu Senaryo Kıyaslama:** "Kötümser, Beklenen, İyimser" gibi farklı senaryolar kaydedilerek yan yana finansal değişimler grafiklerle izlenebilir[cite: 2, 5].
*   **Gantt Şeması ve Sistem Hafızası:** Yıllık planlama modunda ürünlerin yetişme süreleri hesaplanır ve tarlaların zaman içindeki doluluk oranları interaktif olarak görselleştirilir[cite: 2, 8].

## 📂 Veri Mimarisi
Sistem iki temel veri kaynağı ile çalışır[cite: 5]:
1.  **İç Veriler:** `tarlalar.xlsx` (konum, toprak tipi, suya uzaklık) ve `urunler.xlsx` (maliyet, verim, tolerans limitleri)[cite: 3].
2.  **Dış Veriler:** Open-Meteo API kullanılarak tarlaların geçmiş iklim verileri analiz edilir ve dinamik don/kuraklık riskleri hesaplanır[cite: 3, 5].

## ⚙️ Kurulum ve Çalıştırma

**1. Gerekli Kütüphaneleri Yükleyin:**
```bash
pip install streamlit pandas plotly pulp openai requests openpyxl

**2. Gerekli Kütüphaneleri Yükleyin:**
```bash
pip install -r requirements.txt
**3.Uygulamayı Başlatın:**
```bash
streamlit run app.py