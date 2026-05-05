from openai import OpenAI

class AIInference:
    def __init__(self, api_base="http://localhost:1234/v1", api_key="lm-studio"):
        # API anahtarı ve taban URL'si ile OpenAI istemcisini yapılandırarak yerel dil modeli sunucusuna bağlantı sağlar.
        self.client = OpenAI(base_url=api_base, api_key=api_key)

    def generate_explanation(self, optimizasyon_sonucu, don_olasiligi, bütce, su_krizi, maliyet_degisimi, satis_fiyati_degisimi):
        if not optimizasyon_sonucu['Ekim_Plani']:
            return "Sistem Uyarı: Belirlediğiniz kısıtlar altında matematiksel olarak uygun bir ekim planı bulunamadı. Lütfen senaryo parametrelerini esnetin."

        golge_fiyat = optimizasyon_sonucu.get('Butce_Golge_Fiyati', 0)
        butce_analizi = "Bütçe kısıtı zorlanmıyor."
        if golge_fiyat > 0:
            butce_analizi = f"Bütçe kısıtı tam doldu. Bütçedeki her 1 TL artış, kârı {golge_fiyat:.2f} TL artırabilir."

        # ✅ 1. DÜZELTME: Toplam alanı hesaplayıp, ürünlerin "Yüzdelik" ağırlığını buluyoruz
        toplam_ekilen_alan = sum(plan['Ekilecek_Alan_Donum'] for plan in optimizasyon_sonucu['Ekim_Plani'])
        
        tarla_detaylari = "🌾 [ÜRÜN BAZINDA PORTFÖY AĞIRLIĞI]\n"
        ozet_sozluk = {}
        
        for plan in optimizasyon_sonucu['Ekim_Plani']:
            urun = plan['Urun_Adi']
            if urun not in ozet_sozluk:
                ozet_sozluk[urun] = {"alan": 0, "su_ihtiyaci": plan['Urun_Su_Ihtiyaci'], "toplam_kar": 0}
            
            ozet_sozluk[urun]["alan"] += plan['Ekilecek_Alan_Donum']
            birim_kar = plan.get('Donum_Basi_Net_Kar', 0)
            ozet_sozluk[urun]["toplam_kar"] += birim_kar * plan['Ekilecek_Alan_Donum']

        # Yüzdelik dilimleri hesaplayarak AI'a veriyoruz ki neyin "çok" neyin "az" ekildiğini anlasın
        for urun, detay in ozet_sozluk.items():
            yuzdelik_pay = (detay['alan'] / toplam_ekilen_alan) * 100 if toplam_ekilen_alan > 0 else 0
            tarla_detaylari += f"- {urun}: Toplam arazinin %{yuzdelik_pay:.1f}'ini kaplıyor ({detay['alan']:.1f} Dönüm). (Su İhtiyacı: {detay['su_ihtiyaci']}/10, Beklenen Toplam Kâr: {detay['toplam_kar']:,.2f} TL)\n"

        ozet_veri = f"""
        [SENARYO PARAMETRELERİ (GİRDİLER)]
        - Toplam Bütçe: {bütce:,.2f} TL
        - Gerçekleşen Don Riski Olasılığı: %{don_olasiligi * 100}
        - Kuraklık / Su Krizi Etkisi: %{su_krizi * 100} (Suya uzak tarlalar için ölümcül, su ihtiyacı yüksek ürünler için kâr düşürücü)
        - Tohum Maliyeti Değişimi: %{maliyet_degisimi * 100}
        - Ürün Satış Fiyatı Değişimi: %{satis_fiyati_degisimi * 100}

        [ÇIKTILAR VE KISIT ANALİZİ]
        - Kullanılan Bütçe: {optimizasyon_sonucu['Kullanilan_Butce']:,.2f} TL
        - Bütçe Gölge Fiyatı: {butce_analizi}
        
        {tarla_detaylari}
        """
        # ✅ YENİ: Hem şablonu koruyan hem de AI'a "Düşünme Payı" bırakan dinamik yapı
        system_prompt = """
        Sen uzman bir Tarım Karar Destek Sistemi (KDS) finans ve operasyon danışmanısın. Amacın bir CEO'ya veri odaklı, dinamik ve sadece o anki senaryoya uygun tavsiyeler vermektir.
        
        KESİN KURALLAR VE ZORUNLU FORMAT:
        1. BÖLÜM 2 İÇİN ZORUNLU ŞABLON: Ürün gerekçelerini listelerken BİREBİR aşağıdaki Markdown şablonunu kullan:
           **[Ürün Adı]:**
           * Su İhtiyacı: [X]/10
           * Beklenen Toplam Kâr: [Y] TL
           * Arazi Payı: %[Z] ([W] dönüm) - [Buraya o ürünün neden seçildiğine dair risk/getiri dengesini açıklayan tek bir profesyonel cümle yaz.]
           
        2. DİNAMİK VE MANTIKLI DANIŞMANLIK (BÖLÜM 3 İÇİN KATI KURAL): 
           - ASLA EZBERE TAVSİYE VERME! Önce sana verilen [SENARYO PARAMETRELERİ] verilerini oku.
           - Don Riski Yorumu: Eğer Don Riski %0 ise ASLA don sigortası, sera veya dondan korunma tavsiyesi VERME. Sadece don riski belirginse (örn: %20 ve üstü) buna yönelik tarımsal aksiyon öner.
           - Su Krizi Yorumu: Eğer Su Krizi %0 ise sulama altyapısı veya kuraklık önlemi ÖNERME.
           - Finansal Yorum: Bütçe Gölge Fiyatı'nı (Shadow Price) dinamik yorumla. Her senaryoda "dış yatırım al" deme. Gölge fiyat yüksekse "kredi maliyetleri bu oranın altındaysa borçlanmak kârlıdır" şeklinde çıkarım yap. Gölge fiyat düşük veya sıfırsa "mevcut bütçe yeterlidir, dış finansmana gerek yoktur" de.

        3. TİCARİ MANTIK KURALI: Düşük kârlı ürünlerin seçilme sebebi düşük kârı değil; arta kalan bütçeyi/araziyi değerlendirmek, riskleri dağıtmak veya takvim boşluklarını doldurmaktır.
        
        4. ASLA kopyala-yapıştır yapma ve "ekimi arttı/azaldı" gibi kıyaslamalar kullanma.
        """

        user_prompt = f"""
        Aşağıdaki Karar Destek Sistemi senaryosunu analiz et:
        {ozet_veri}

        Lütfen yöneticiye sunulmak üzere şu 3 başlıkta detaylı bir rapor yaz:

        📌 1. Senaryo Etkisi: Mevcut riskler ve maliyet/fiyat değişimleri karşısında optimizasyon motoru nasıl bir savunma veya saldırı stratejisi kurdu?
        
        ⚙️ 2. Ürün Bazlı Seçim Gerekçeleri: Listelenen ürünleri SADECE sana kural olarak verilen ZORUNLU ŞABLON formatında alt alta yazarak gerekçelendir.
        
        💡 3. Yönetimsel Aksiyon ve Bütçe Tavsiyesi: SADECE parametrelerdeki risk oranlarına (Don, Su) ve Gölge Fiyat değerine bakarak kendi mantıksal çıkarımını yap. (Risk yoksa o riske dair tavsiye verme).
        """
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"⚠️ Çıkarım motoruna ulaşılamadı. Hata: {str(e)}"