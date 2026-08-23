import pandas as pd
import requests

class DataHandler:
    def __init__(self, tarlalar_path="data/tarlalar.xlsx", urunler_path="data/urunler.xlsx"):
        self.tarlalar_path = tarlalar_path
        self.urunler_path = urunler_path
        self.tarlalar_df = None
        self.urunler_df = None

    def load_internal_data(self):
        try:
            self.tarlalar_df = pd.read_excel(self.tarlalar_path)
            self.urunler_df = pd.read_excel(self.urunler_path)
            print("İç veriler başarıyla yüklendi!")
            return self.tarlalar_df, self.urunler_df
        except Exception as e:
            print(f"Veri yüklenirken bir hata oluştu: {e}")
            return None, None

    def fetch_climate_data_from_api(self, lat, lon, target_month):
        import datetime
        import requests
        current_year = datetime.datetime.now().year
        start_date = f"{current_year-4}-01-01"
        end_date = f"{current_year-1}-12-31"
        
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&daily=temperature_2m_mean,temperature_2m_min&timezone=auto"
        
        try:
            response = requests.get(url)
            data = response.json()
            df = pd.DataFrame({
                'date': pd.to_datetime(data['daily']['time']),
                'mean_temp': data['daily']['temperature_2m_mean'],
                'min_temp': data['daily']['temperature_2m_min']
            })
            df_month = df[df['date'].dt.month == target_month]
            ortalama_sicaklik = df_month['mean_temp'].mean()
            don_gun_sayisi = len(df_month[df_month['min_temp'] < 0])
            don_olasiligi = don_gun_sayisi / len(df_month)
            
            return ortalama_sicaklik, don_olasiligi
            
        except Exception as e:
            print(f"API Hatası: {e}")
            return 15.0, 0.20

    def prepare_optimization_data(self):
        if self.tarlalar_df is None or self.urunler_df is None:
            self.load_internal_data()
            
        pass

if __name__ == "__main__":
    veri_yoneticisi = DataHandler()
    tarlalar, urunler = veri_yoneticisi.load_internal_data()
    if tarlalar is not None:
        print("Tarlalar Verisi İlk 3 Satır:\n", tarlalar.head(3))
