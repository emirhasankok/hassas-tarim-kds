import streamlit as st
import pandas as pd
import plotly.express as px
from data_handler import DataHandler
from optimization_engine import OptimizationEngine
from ai_inference import AIInference
import datetime
from state_manager import get_occupied_fields, save_active_plans

st.set_page_config(page_title="Hassas Tarım KDS", layout="wide")
st.title("🌾 Hassas Tarım Karar Destek Sistemi (KDS)")
st.markdown("Bu sistem; kısıtlar altında riski minimize edip kârı maksimize eden optimal ürün dağılımını bulur ve yapay zeka ile size **neden** bu kararın alındığını açıklar.")

@st.cache_data
def load_data():
    # Veri sınıfı örneği oluşturulup kaynak veri setlerinin bir kez yüklenmesi ve uygulamanın yeniden yüklemelerinde önbellekten çağrılması sağlanır.
    veri_yoneticisi = DataHandler()
    return veri_yoneticisi.load_internal_data()

tarlalar_df, urunler_df = load_data()

if tarlalar_df is None or urunler_df is None:
    st.error("Veri dosyaları (tarlalar.csv, urunler.csv) bulunamadı veya okunamadı!")
    st.stop()

# --- SENARYO KARŞILAŞTIRMA İÇİN HAFIZA TANIMLAMASI ---
if "saved_scenarios" not in st.session_state:
    st.session_state["saved_scenarios"] = {}
if "son_sonuclar" not in st.session_state:
    st.session_state["son_sonuclar"] = None
# Sol taraftaki menü üzerinden kullanıcıdan optimizasyon senaryosunu yönetecek genel ayarlar alınır.

with st.sidebar:
    st.header("⚙️ Senaryo Parametreleri")

    planlama_modu = st.radio("Planlama Modu Seçin:", ("Aylık Tekil Planlama", "Yıllık Dinamik Planlama (12 Ay)"))
    
    # ✅ YIL VE AY SEÇİMİ YAN YANA
    col_yil, col_ay = st.columns(2)
    import datetime
    suanki_yil = datetime.datetime.now().year
    with col_yil:
        mevcut_yil = st.selectbox("Başlangıç Yılı", options=list(range(suanki_yil, suanki_yil + 5)))
    with col_ay:
        mevcut_ay = st.selectbox("Başlangıç Ayı", options=list(range(1, 13)), format_func=lambda x: [
            "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
            "Temmuz", "Agustos", "Eylül", "Ekim", "Kasım", "Aralık"
        ][x-1])

    # ✅ HAFIZAYI SİL BUTONU
    st.divider()
    st.header("💾 Sistem Hafızası")
    if st.button("🗑️ Kayıtlı Planları Temizle", help="Sisteme kaydedilmiş tüm aktif ekimleri siler. Tarlaları boşaltır."):
        from state_manager import clear_active_plans
        clear_active_plans()
        st.success(f"Hafıza temizlendi! Tüm tarlalar {mevcut_yil} için boş statüsüne alındı.")

    # Değişen dış faktörlerin sisteme etkisini ölçmek amacıyla farklı değişkenler için kaydırıcı barlar oluşturulur.
    st.divider()
    st.header("📉 What-If Analizi")
    
    bütce_input = st.slider("Toplam Bütçe (TL)", min_value=100000, max_value=50000000, value=150000, step=10000)

    don_olasiligi_input = st.slider("Beklenen Don Olasılığı (%)", min_value=0, max_value=100, value=20, step=5) / 100.0
    
    su_krizi_etkisi = st.slider("💧 Su Krizi / Kuraklık Etkisi (%)", min_value=0, max_value=100, value=0, step=5, help="Kuraklık arttıkça tarlaların suya erişim limiti daralır ve bitkilerin suya duyarlılığı artar.") / 100.0
    
    maliyet_degisimi = st.slider("🌱 Tohum Maliyeti Değişimi (%)", min_value=-50, max_value=150, value=0, step=5, help="Genel tohum girdi maliyetlerindeki artış veya azalış.") / 100.0
    
    isgucu_maliyet_degisimi = st.slider("👷 İş Gücü Maliyeti Değişimi (%)", min_value=-50, max_value=150, value=0, step=5, help="İşçi yevmiyelerindeki / asgari ücretteki artış veya azalış.") / 100.0
    
    satis_fiyati_degisimi = st.slider("📈 Ürün Satış Fiyatı Değişimi (%)", min_value=-50, max_value=150, value=0, step=5, help="Piyasadaki ürün satış fiyatlarındaki enflasyon veya düşüş.") / 100.0

    st.divider()
    hesapla_btn = st.button("🚀 Sistemi Çalıştır", type="primary")

# Kullanıcının belirlediği verilerle ana algoritmanın ve AI yorumlayıcısının tetiklendiği bölüm.
if hesapla_btn:
    with st.spinner(f"Model ({planlama_modu}) hesaplanıyor ve yapay zeka analiz ediyor..."):
        
        # Sistemin hafızasındaki dolu tarlaları kontrol et
        dolu_tarlalar = get_occupied_fields(mevcut_yil, mevcut_ay)
        
        if dolu_tarlalar:
            st.warning(f"Sistem hafızasında halihazırda dolu olan {len(dolu_tarlalar)} tarla tespit edildi. Bu tarlalar hasat tarihlerine kadar plandan muaf tutulacaktır.")

        opt_engine = OptimizationEngine(
            tarlalar_df, urunler_df, bütce_input,mevcut_yil, mevcut_ay, don_olasiligi_input,
            su_krizi_etkisi=su_krizi_etkisi,
            maliyet_degisimi=maliyet_degisimi,
            satis_fiyati_degisimi=satis_fiyati_degisimi,
            isgucu_maliyet_degisimi=isgucu_maliyet_degisimi,
            occupied_fields=dolu_tarlalar # YENİ: Dolu tarlaları motora gönderiyoruz
        )

        # Seçilen moda göre spesifik aylık ya da yıllık çözümleme metodu çağrılır.
        if planlama_modu == "Aylık Tekil Planlama":
            sonuclar = opt_engine.run_optimization()
        else:
            sonuclar = opt_engine.run_yearly_optimization()
        
        # ✅ YENİ EKLENEN: Hesaplanan sonuçları "kaydedilebilir" olarak hafızaya al
        st.session_state["son_sonuclar"] = {
            "Net Kâr": sonuclar['Beklenen_Kar'],
            "Kullanılan Bütçe": sonuclar['Kullanilan_Butce'],
            "Don Olasılığı": don_olasiligi_input,
            "Su Krizi Etkisi": su_krizi_etkisi,
            "Maliyet Değişimi": maliyet_degisimi,
            "Satış Fiyatı Değişimi": satis_fiyati_degisimi
        }

        col1, col2, col3 = st.columns(3)
        col1.metric("Beklenen Net Kâr", f"{sonuclar['Beklenen_Kar']:,.2f} TL")
        col2.metric("Kullanılan Bütçe", f"{sonuclar['Kullanilan_Butce']:,.2f} TL")
        col3.metric("Optimizasyon Durumu", "Başarılı" if sonuclar['Durum'] == 'Optimal' else "Çözüm Bulunamadı")

        st.divider()
        
        # ✅ GANTT ŞEMASI BURAYA (TAM GENİŞLİKTE - SÜTUNLARDAN ÖNCE)
        if planlama_modu == "Yıllık Dinamik Planlama (12 Ay)" and sonuclar['Ekim_Plani']:
            st.subheader("📅 Yıllık Ekim Takvimi (Gantt Şeması)")
            
            import datetime
            df_plan = pd.DataFrame(sonuclar['Ekim_Plani'])
            df_gantt = pd.merge(df_plan, urunler_df[['Urun_Adi', 'Yetisme_Suresi']], on='Urun_Adi', how='left')
            df_gantt['Yetisme_Suresi'] = df_gantt['Yetisme_Suresi'].fillna(120) 
            
            ay_sozlugu = {
                "Ocak": 1, "Şubat": 2, "Mart": 3, "Nisan": 4, "Mayıs": 5, "Haziran": 6,
                "Temmuz": 7, "Ağustos": 8, "Eylül": 9, "Ekim": 10, "Kasım": 11, "Aralık": 12
            }
            
            
            df_gantt['Ay_No'] = df_gantt['Ekim_Ayi'].map(ay_sozlugu)
            # Seçilen aydan daha küçük bir aya denk gelindiyse (örneğin başlangıç Ekim, ürün hasadı Şubat ise) yıl 1 artmıştır.
            def yil_hesapla(ay_no, baslangic_ayi, baslangic_yili):
                if ay_no < baslangic_ayi:
                    return baslangic_yili + 1
                return baslangic_yili
                
            df_gantt['Islem_Yili'] = df_gantt['Ay_No'].apply(lambda x: yil_hesapla(x, mevcut_ay, mevcut_yil))
            df_gantt['Baslangic_Tarihi'] = pd.to_datetime(df_gantt['Islem_Yili'].astype(str) + "-" + df_gantt['Ay_No'].astype(str) + "-01", format="%Y-%m-%d")
            df_gantt['Bitis_Tarihi'] = df_gantt['Baslangic_Tarihi'] + pd.to_timedelta(df_gantt['Yetisme_Suresi'], unit='D')
            
            # Dinamik Yükseklik: Tarla sayısına göre grafiğin boyunu uzatıyoruz ki dikeyde sıkışmasın
            tarla_sayisi = len(df_gantt['Tarla_ID'].unique())
            grafik_yuksekligi = max(400, tarla_sayisi * 30 + 150)
            
            gantt_fig = px.timeline(
                df_gantt, 
                x_start="Baslangic_Tarihi", 
                x_end="Bitis_Tarihi", 
                y="Tarla_ID", 
                color="Urun_Adi",
                hover_data={"Ekilecek_Alan_Donum": True, "Yetisme_Suresi": True},
                height=grafik_yuksekligi # Sıkışıklığı önleyen parametre
            )
            
            gantt_fig.update_yaxes(autorange="reversed", title="Lokasyon (Tarla_ID)")
            gantt_fig.update_layout(
                xaxis=dict(title="Operasyon Ayları", tickformat="%B", dtick="M1"),
                margin=dict(l=20, r=20, t=20, b=20)
            )
            
            st.plotly_chart(gantt_fig, use_container_width=True)
            kayit_listesi = df_gantt[['Tarla_ID', 'Urun_Adi', 'Ekilecek_Alan_Donum', 'Baslangic_Tarihi', 'Bitis_Tarihi']].copy()
            kayit_listesi['Baslangic_Tarihi'] = kayit_listesi['Baslangic_Tarihi'].dt.strftime('%Y-%m-%d')
            kayit_listesi['Bitis_Tarihi'] = kayit_listesi['Bitis_Tarihi'].dt.strftime('%Y-%m-%d')
            st.session_state["onay_bekleyen_plan"] = kayit_listesi.to_dict('records')
            st.divider()
            

        col_grafik, col_ai = st.columns([1, 1.5])
        
        st.divider()
 
        with col_grafik:
            st.subheader("📊 Ekim Planı Dağılımı")
            if sonuclar['Ekim_Plani']:
                df_plan = pd.DataFrame(sonuclar['Ekim_Plani'])
        
                if planlama_modu == "Yıllık Dinamik Planlama (12 Ay)" and 'Ekim_Ayi' in df_plan.columns:
                    df_plan['Gosterim_Ismi'] = df_plan['Urun_Adi'] + " (" + df_plan['Ekim_Ayi'] + ")"
                else:
                    df_plan['Gosterim_Ismi'] = df_plan['Urun_Adi']
        
                # Görselleştirmede karmaşıklığı önlemek adına aynı isme sahip ekim kayıtları toplanarak gruplanır.
                df_plot = df_plan.groupby('Gosterim_Ismi', as_index=False)['Ekilecek_Alan_Donum'].sum()
            
                fig = px.pie(df_plot, values='Ekilecek_Alan_Donum', names='Gosterim_Ismi', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
        
                with st.expander("Detaylı Tabloyu Gör"):
                    st.dataframe(df_plan)
            
        with col_ai:
            st.subheader("🤖 Yöneticiye AI Önerisi ve Gerekçeler")
            ai_bridge = AIInference()
            # Çözümlenen model sonuçları ve güncel UI parametreleri AI sınıfına iletilerek analitik metin üretilir.
            ai_yorumu = ai_bridge.generate_explanation(
                sonuclar, 
                don_olasiligi_input, 
                bütce_input,
                su_krizi_etkisi,
                maliyet_degisimi,
                satis_fiyati_degisimi
            )
            st.info(ai_yorumu)
# app.py dosyanızın EN ALTINA eklenecek kod:

# ✅ BAĞIMSIZ KAYIT BLOĞU: Buton içinde buton sorununu çözer
if st.session_state.get("onay_bekleyen_plan"):
    st.divider()
    st.subheader("💾 Planı Onayla ve Sahaya Aktar")
    st.markdown("Bu planı onayladığınızda, sistem ekilen ürünleri ve hasat tarihlerini hafızasına alacaktır.")
    
    if st.button("✅ Bu Ekim Planını Sisteme Kaydet", type="primary", use_container_width=True):
        save_active_plans(st.session_state["onay_bekleyen_plan"])
        st.success("Plan başarıyla sisteme kaydedildi! Tarlalarınız artık takip altında.")
        st.balloons()
        # Kayıt yapıldıktan sonra hafızayı temizle ki buton ekrandan kalksın
        st.session_state["onay_bekleyen_plan"] = None

# ==========================================
# 📊 SENARYO KARŞILAŞTIRMA MODÜLÜ (YENİ EKLENDİ)
# ==========================================
if st.session_state.get("son_sonuclar") is not None:
    st.divider()
    st.subheader("📥 Güncel Sonucu Senaryo Olarak Kaydet")
    
    col_isim, col_kaydet = st.columns([3, 1])
    with col_isim:
        senaryo_ismi = st.selectbox(
            "Bu hesaplamayı hangi senaryo olarak kaydetmek istiyorsunuz?", 
            ["Beklenen Senaryo", "İyimser Senaryo", "Kötümser Senaryo", "Alternatif Senaryo A", "Alternatif Senaryo B"]
        )
    with col_kaydet:
        st.write("") # Butonu selectbox ile aynı hizaya getirmek için boşluk
        if st.button("💾 Senaryoyu Kaydet", use_container_width=True):
            st.session_state["saved_scenarios"][senaryo_ismi] = st.session_state["son_sonuclar"]
            st.success(f"**{senaryo_ismi}** başarıyla eklendi!")

# Eğer hafızada kaydedilmiş senaryo varsa tabloyu ve grafiği göster
if st.session_state["saved_scenarios"]:
    st.divider()
    st.subheader("⚖️ Çoklu Senaryo Karşılaştırma Analizi")
    st.markdown("Farklı risk ve maliyet durumlarına göre sistemin ürettiği optimizasyon sonuçları:")
    
    # Sözlüğü pandas DataFrame'e çevirip devrik (transpose) alıyoruz
    df_senaryolar = pd.DataFrame.from_dict(st.session_state["saved_scenarios"], orient="index")
    
    # 1. TABLO GÖSTERİMİ
    df_gosterim = df_senaryolar.copy()
    df_gosterim["Net Kâr"] = df_gosterim["Net Kâr"].apply(lambda x: f"{x:,.2f} TL")
    df_gosterim["Kullanılan Bütçe"] = df_gosterim["Kullanılan Bütçe"].apply(lambda x: f"{x:,.2f} TL")
    df_gosterim["Don Olasılığı"] = df_gosterim["Don Olasılığı"].apply(lambda x: f"%{int(x*100)}")
    df_gosterim["Su Krizi Etkisi"] = df_gosterim["Su Krizi Etkisi"].apply(lambda x: f"%{int(x*100)}")
    df_gosterim["Maliyet Değişimi"] = df_gosterim["Maliyet Değişimi"].apply(lambda x: f"%{int(x*100)}")
    df_gosterim["Satış Fiyatı Değişimi"] = df_gosterim["Satış Fiyatı Değişimi"].apply(lambda x: f"%{int(x*100)}")
    
    st.dataframe(df_gosterim, use_container_width=True)
    
    # ==========================================
    # 📊 YENİ EKLENEN: ÇUBUK GRAFİK (BAR CHART) GÖRSELLEŞTİRMESİ
    # ==========================================
    
    # Index'teki senaryo isimlerini bir sütuna çekiyoruz
    df_grafik = df_senaryolar.reset_index().rename(columns={"index": "Senaryo"})
    
    # Plotly ile Yan Yana (Grouped) Çubuk Grafik Çizimi
    fig_senaryo = px.bar(
        df_grafik, 
        x="Senaryo", 
        y=["Net Kâr", "Kullanılan Bütçe"],
        barmode="group", # Kâr ve Bütçe çubuklarını yan yana koyar
        title="Senaryolara Göre Finansal Değişim",
        labels={"value": "Tutar (TL)", "variable": "Finansal Metrik", "Senaryo": ""},
        text_auto='.2s', # Çubukların üzerine değerleri okunaklı kısaltmalarla (Örn: 1.5M, 850k) yazar
        color_discrete_sequence=["#2ecc71", "#3498db"] # Net kâr için yeşil, Bütçe için mavi renk
    )
    
    # Grafik arka planını ve eksenlerini daha profesyonel göstermek için ince ayar
    fig_senaryo.update_layout(
        yaxis_title="Tutar (TL)",
        legend_title_text="Gösterge",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig_senaryo, use_container_width=True)
    
    # Karşılaştırma tablosunu temizleme butonu
    if st.button("🗑️ Karşılaştırma Verilerini Temizle"):
        st.session_state["saved_scenarios"] = {}
        st.rerun()