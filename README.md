# Hassas Tarım Karar Destek Sistemi (KDS)

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red.svg)
![Optimization](https://img.shields.io/badge/Optimization-PuLP-green.svg)
![AI](https://img.shields.io/badge/AI-Qwen_2.5-orange.svg)

Bu proje, tarım yöneticilerinin kısıtlı bütçe, arazi kısıtları ve değişken iklim koşulları altında karşılaştığı karmaşık karar süreçlerini optimize etmek amacıyla geliştirilmiş bir **Yapay Zeka Destekli Karar Destek Sistemidir (KDS)**.

## Proje Özeti
Geleneksel tarımda kararlar genellikle sezgilere dayalı alınır. Bu sistem; Doğrusal Programlama (Linear Programming) mantığını kullanarak riski (don, kuraklık) minimize edip beklenen net kârı maksimize edecek en verimli ekim planını matematiksel olarak hesaplar. Ayrıca entegre **Qwen 2.5 AI** motoru ile bu sayısal sonuçları yöneticiye stratejik bir danışman diliyle açıklar.

## Geliştirme Metodolojisi: Architectural "Vibe Coding"
Bu proje geleneksel yöntemlerle satır satır kodlanmamış, **AI-Assisted Architecture (Yapay Zeka Destekli Mimari)** ve **Vibe Coding** prensipleriyle hayata geçirilmiştir. 
Süreç boyunca bir Yönetim Bilişim Sistemleri (YBS) vizyonuyla; teknik kod yazımından (syntax) ziyade **sistemin mantığına, kısıtların tasarımına ve kullanıcı deneyimine (UX)** odaklanılmıştır.

## Temel Özellikler
*   **Dinamik Optimizasyon:** PuLP kütüphanesi kullanılarak bütçe, su kısıtı, toprak uyumu ve iklim limitlerine göre tarlalar için en kârlı ürün desenini bulur.
*   **What-If (Duyarlılık) Analizi:** Kullanıcı arayüzü üzerinden tohum maliyetlerindeki enflasyon, su krizi şiddeti ve don olasılığı gibi parametreler değiştirilerek farklı senaryolar anlık test edilebilir.
*   **AI Destekli Karar Yorumlama:** Sayısal sonuçlar, yerel **Qwen 2.5** entegrasyonu sayesinde "Gölge Fiyat (Shadow Price)" analizi yapılarak finansal ve operasyonel önerilere dönüştürülür.
*   **Çoklu Senaryo Kıyaslama:** "Kötümser, Beklenen, İyimser" gibi farklı senaryolar kaydedilerek yan yana finansal değişimler grafiklerle izlenebilir.
*   **Gantt Şeması ve Sistem Hafızası:** Yıllık planlama modunda ürünlerin yetişme süreleri hesaplanır ve tarlaların zaman içindeki doluluk oranları interaktif olarak görselleştirilir.

## Veri Mimarisi
Sistem iki temel veri kaynağı ile çalışır:
1.  **İç Veriler:** `tarlalar.xlsx` (konum, toprak tipi, suya uzaklık) ve `urunler.xlsx` (maliyet, verim, tolerans limitleri).
2.  **Dış Veriler:** Open-Meteo API kullanılarak tarlaların geçmiş iklim verileri analiz edilir ve dinamik don/kuraklık riskleri hesaplanır.

## Kurulum ve Çalıştırma

Aşağıdaki komut satırını kopyalayıp terminale yapıştırarak projeyi klonlayabilir, gerekli kütüphaneleri yükleyebilir ve uygulamayı başlatabilirsiniz:
```bash
git clone [https://github.com/emirhasankok/hassas-tarim-kds.git](https://github.com/emirhasankok/hassas-tarim-kds.git)
cd hassas-tarim-kds
pip install -r requirements.txt
streamlit run app.py
