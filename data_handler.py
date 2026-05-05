import pandas as pd
import requests

class DataHandler:
    def __init__(self, tarlalar_path="data/tarlalar.xlsx", urunler_path="data/urunler.xlsx"):
        self.tarlalar_path = tarlalar_path
        self.urunler_path = urunler_path
        self.tarlalar_df = None
        self.urunler_df = None

    def load_internal_data(self):
        # Tanımlanan Excel dosyalarını okuyarak pandas DataFrame formatında sınıf değişkenlerine yükler.
        try:
            self.tarlalar_df = pd.read_excel(self.tarlalar_path)
            self.urunler_df = pd.read_excel(self.urunler_path)
            print("İç veriler başarıyla yüklendi!")
            return self.tarlalar_df, self.urunler_df
        except Exception as e:
            print(f"Veri yüklenirken bir hata oluştu: {e}")
            return None, None

    def fetch_climate_data_from_api(self, lat, lon, target_month):
        # Open-Meteo tarihi iklim API'sine istek atarak koordinatlara göre belirlenen geçmiş yılların hava durumunu analiz eder.
        import datetime
        import requests
        
        # İçinde bulunulan yıldan geriye dönük 4 yıllık dönemin başlangıç ve bitiş tarihlerini dinamik olarak hesaplar.
        current_year = datetime.datetime.now().year
        start_date = f"{current_year-4}-01-01"
        end_date = f"{current_year-1}-12-31"
        
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&daily=temperature_2m_mean,temperature_2m_min&timezone=auto"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            # API'den alınan günlük ortalama ve minimum sıcaklıkları yapılandırılmış veri çerçevesine dönüştürür.
            df = pd.DataFrame({
                'date': pd.to_datetime(data['daily']['time']),
                'mean_temp': data['daily']['temperature_2m_mean'],
                'min_temp': data['daily']['temperature_2m_min']
            })
            
            # Tüm veri setini sadece ilgili hedef ay bazında filtreden geçirir.
            df_month = df[df['date'].dt.month == target_month]
            
            # İlgili ayın son 4 yıldaki genel ortalama sıcaklık değerini çıkarır.
            ortalama_sicaklik = df_month['mean_temp'].mean()
            
            # İlgili ayda minimum sıcaklığın sıfırın altına düştüğü gün sayısını toplam güne bölerek don oranını hesaplar.
            don_gun_sayisi = len(df_month[df_month['min_temp'] < 0])
            don_olasiligi = don_gun_sayisi / len(df_month)
            
            return ortalama_sicaklik, don_olasiligi
            
        except Exception as e:
            print(f"API Hatası: {e}")
            # Ağ ya da API çökmesi durumlarında sistemin durmaması için sabit varsayılan değerler döndürülür.
            return 15.0, 0.20

    def prepare_optimization_data(self):
        # Optimizasyon algoritması öncesi eksik verileri yükler; bu metot verileri PuLP modeline uygun formata sokmak için ayrılmıştır.
        if self.tarlalar_df is None or self.urunler_df is None:
            self.load_internal_data()
            
        pass

# Bağımsız bir test işlemi için sınıf başlatılır ve ilk satırlar ekrana yazdırılarak doğrulama yapılır.
if __name__ == "__main__":
    veri_yoneticisi = DataHandler()
    tarlalar, urunler = veri_yoneticisi.load_internal_data()
    if tarlalar is not None:
        print("Tarlalar Verisi İlk 3 Satır:\n", tarlalar.head(3))