import pulp
import pandas as pd
import math

class OptimizationEngine:
    def __init__(self, tarlalar_df, urunler_df, toplam_butce,mevcut_yil, mevcut_ay, don_olasiligi=0.20,
                 su_krizi_etkisi=0.0, maliyet_degisimi=0.0, satis_fiyati_degisimi=0.0, isgucu_maliyet_degisimi=0.0, occupied_fields=None):
        self.tarlalar = tarlalar_df
        self.urunler = urunler_df
        self.toplam_butce = toplam_butce
        self.mevcut_yil = mevcut_yil
        self.mevcut_ay = mevcut_ay
        self.don_olasiligi = don_olasiligi
        self.su_krizi_etkisi = su_krizi_etkisi
        self.maliyet_carpani = 1.0 + maliyet_degisimi
        self.satis_fiyati_carpani = 1.0 + satis_fiyati_degisimi
        self.isgucu_maliyet_carpani = 1.0 + isgucu_maliyet_degisimi

        self.occupied_fields = occupied_fields if occupied_fields is not None else {}
    def get_ay_sayisal(self, deger, varsayilan):
        ay_sozlugu = {
            "Ocak": 1, "Şubat": 2, "Mart": 3, "Nisan": 4, "Mayıs": 5, "Haziran": 6,
            "Temmuz": 7, "Ağustos": 8, "Eylül": 9, "Ekim": 10, "Kasım": 11, "Aralık": 12
        }
        if isinstance(deger, str):
            ilk_ay = deger.split('-')[0].strip().capitalize()
            return ay_sozlugu.get(ilk_ay, varsayilan)
        return int(deger)

    def calculate_risk_score(self, don_hassasiyeti, suya_uzaklik):
        if isinstance(don_hassasiyeti, str):
            try:
                don_hassasiyeti = float(don_hassasiyeti.replace(',', '.'))
            except:
                don_hassasiyeti = 0.5 
                
        su_faktoru = 0.5 if suya_uzaklik < 100 else 1.0
        return self.don_olasiligi * don_hassasiyeti * su_faktoru
    def run_optimization(self):
        model = pulp.LpProblem("Aylik_Optimizasyon", pulp.LpMaximize)
        tarla_idx = self.tarlalar.index.tolist()
        urun_idx = self.urunler.index.tolist()

        x = pulp.LpVariable.dicts("Ekim_Alani",
                                  ((i, j) for i in tarla_idx for j in urun_idx),
                                  lowBound=0, cat='Continuous')
        obj_function = []
        for i in tarla_idx:
            tarla = self.tarlalar.iloc[i]
            for j in urun_idx:
                urun = self.urunler.iloc[j]
                hassasiyet = urun.get('Maliyet_Hassasiyeti', 1.0)
                etkili_artis_orani = (self.maliyet_carpani - 1.0) * hassasiyet
                dinamik_maliyet_carpani = 1.0 + etkili_artis_orani
                tohum_maliyeti = urun['Tohum_Maliyeti_TL'] * dinamik_maliyet_carpani
                is_gucu_maliyeti = urun['Is_Gucu_Maliyeti_TL'] * self.isgucu_maliyet_carpani
                kuraklik_kayip_orani = self.su_krizi_etkisi * (urun['Su_Ihtiyaci_Puani'] / 10.0)
                dinamik_verim = urun['Beklenen_Verim_KG'] * (1 - kuraklik_kayip_orani)
                satis_fiyati = urun['Satis_Fiyati_TL'] * self.satis_fiyati_carpani
                toplam_gelir = dinamik_verim * satis_fiyati
                birim_kar = toplam_gelir - (tohum_maliyeti + is_gucu_maliyeti)
            
                risk_skoru = self.calculate_risk_score(urun['Don_Hassasiyeti'], tarla['Suya_Uzaklik_m'])
                risk_ayarli_kar = birim_kar * (1 - risk_skoru)
            
                obj_function.append(risk_ayarli_kar * x[i, j])

        model += pulp.lpSum(obj_function), "Risk_Ayarli_Toplam_Kar"
        toplam_maliyet = []
        for i in tarla_idx:
            for j in urun_idx:
                urun = self.urunler.iloc[j]
                hassasiyet = urun.get('Maliyet_Hassasiyeti', 1.0)
                etkili_artis_orani = (self.maliyet_carpani - 1.0) * hassasiyet
                dinamik_maliyet_carpani = 1.0 + etkili_artis_orani
                
                tohum_maliyeti = urun['Tohum_Maliyeti_TL'] * dinamik_maliyet_carpani
                is_gucu_maliyeti = urun['Is_Gucu_Maliyeti_TL'] * self.isgucu_maliyet_carpani
                
                toplam_maliyet.append((tohum_maliyeti + is_gucu_maliyeti) * x[i, j])
        model += pulp.lpSum(toplam_maliyet) <= self.toplam_butce, "Toplam_Butce_Kisiti"

        for i in tarla_idx:
            tarla = self.tarlalar.iloc[i]
            model += pulp.lpSum([x[i, j] for j in urun_idx]) <= tarla['Alan_Donum'], f"Tarla_Kapasite_{i}"
        for i in tarla_idx:
            tarla = self.tarlalar.iloc[i]
            tarla_sicaklik = tarla.get('Ortalama_Sicaklik_C', 15.0)
            tarla_toprak = str(tarla.get('Toprak_Tipi', '')).strip()

            for j in urun_idx:
                urun = self.urunler.iloc[j]
                urun_toprak = str(urun.get('Toprak_Tercihi', '')).strip()
                baslangic = self.get_ay_sayisal(urun['Ekim_Baslangic_Ay'], 1)
                takvim_uygun = (self.mevcut_ay == baslangic)
                efektif_su_ihtiyaci = urun['Su_Ihtiyaci_Puani'] * (1 + self.su_krizi_etkisi)
                efektif_suya_uzaklik_limiti = 300 * (1 - self.su_krizi_etkisi)

                if tarla_toprak != urun_toprak:
                    model += x[i, j] == 0, f"Toprak_Uyumsuzlugu_{i}_{j}"
                elif tarla['Suya_Uzaklik_m'] > efektif_suya_uzaklik_limiti and efektif_su_ihtiyaci > 7:
                    model += x[i, j] == 0, f"Su_Kisiti_{i}_{j}"
                elif not takvim_uygun:
                    model += x[i, j] == 0, f"Takvim_Ihlali_{i}_{j}"
                elif tarla_sicaklik < urun['Min_Sicaklik_C'] or tarla_sicaklik > urun['Max_Sicaklik_C']:
                    model += x[i, j] == 0, f"Sicaklik_Ihlali_{i}_{j}"

        maksimum_ekim_orani = 0.40
        toplam_arazi = self.tarlalar['Alan_Donum'].sum() 

        for j in urun_idx:
            model += pulp.lpSum([x[i, j] for i in tarla_idx]) <= (toplam_arazi * maksimum_ekim_orani), f"Cesitlilik_Urun_{j}"
        model.solve(pulp.PULP_CBC_CMD(msg=False))
        butce_golge_fiyat = model.constraints["Toplam_Butce_Kisiti"].pi
        sonuclar = {
        "Durum": pulp.LpStatus[model.status],
        "Beklenen_Kar": pulp.value(model.objective) if pulp.value(model.objective) else 0.0,
        "Kullanilan_Butce": sum(
            x[i, j].varValue * (
                (self.urunler.iloc[j]['Tohum_Maliyeti_TL'] * self.maliyet_carpani) + 
                (self.urunler.iloc[j]['Is_Gucu_Maliyeti_TL'] * self.isgucu_maliyet_carpani)
            )
            for i in tarla_idx for j in urun_idx if x[i, j].varValue is not None and x[i, j].varValue > 0
        ),
        "Butce_Golge_Fiyati": butce_golge_fiyat,
        "Ekim_Plani": []
        }

        ay_isimleri = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        gercek_ay = self.mevcut_ay
        for i in tarla_idx:
            for j in urun_idx:
                if x[i, j].varValue is not None and x[i, j].varValue > 0:
                    tarla = self.tarlalar.iloc[i]
                    urun = self.urunler.iloc[j]
                    hassasiyet = urun.get('Maliyet_Hassasiyeti', 1.0)
                    etkili_artis_orani = (self.maliyet_carpani - 1.0) * hassasiyet
                    dinamik_maliyet_carpani = 1.0 + etkili_artis_orani
                    yeni_tohum_maliyeti = urun['Tohum_Maliyeti_TL'] * dinamik_maliyet_carpani
                    
                    yeni_satis_fiyati = urun['Satis_Fiyati_TL'] * self.satis_fiyati_carpani
                    alan = round(x[i, j].varValue, 2)
                    yeni_isgucu_maliyeti = urun['Is_Gucu_Maliyeti_TL'] * self.isgucu_maliyet_carpani
                    
                    sonuclar["Ekim_Plani"].append({
                                "Tarla_ID": tarla['Tarla_ID'],
                                "Konum": tarla['Konum'],
                                "Ekim_Ayi": ay_isimleri[gercek_ay],
                                "Suya_Uzaklik_m": tarla['Suya_Uzaklik_m'],
                                "Urun_Adi": urun['Urun_Adi'],
                                "Ekilecek_Alan_Donum": alan,
                                "Eski_Tohum_Maliyeti": urun['Tohum_Maliyeti_TL'],
                                "Yeni_Tohum_Maliyeti": round(yeni_tohum_maliyeti, 2),
                                "Eski_Satis_Fiyati": urun['Satis_Fiyati_TL'],
                                "Yeni_Satis_Fiyati": round(yeni_satis_fiyati, 2),
                                "Urun_Su_Ihtiyaci": urun['Su_Ihtiyaci_Puani'],
                                "Don_Hassasiyeti": urun.get('Don_Hassasiyeti', 0.5),
                                "Donum_Basi_Net_Kar": round((urun['Beklenen_Verim_KG'] * yeni_satis_fiyati) - (yeni_tohum_maliyeti + yeni_isgucu_maliyeti), 2)
                            })
        return sonuclar
    def run_yearly_optimization(self):
        model = pulp.LpProblem("Yillik_Dinamik_Tarim_Plani", pulp.LpMaximize)
        tarla_idx = self.tarlalar.index.tolist()
        urun_idx = self.urunler.index.tolist()
        zaman_ufku = list(range(12))
        gercek_aylar = [(self.mevcut_ay - 1 + t) % 12 + 1 for t in zaman_ufku]

        x = pulp.LpVariable.dicts("Ekim",
                                  ((i, j, t) for i in tarla_idx for j in urun_idx for t in zaman_ufku),
                                  lowBound=0, cat='Continuous')

        obj_function = []
        for i in tarla_idx:
            tarla = self.tarlalar.iloc[i]
            for j in urun_idx:
                urun = self.urunler.iloc[j]
                risk_skoru = self.calculate_risk_score(urun['Don_Hassasiyeti'], tarla['Suya_Uzaklik_m'])
                hassasiyet = urun.get('Maliyet_Hassasiyeti', 1.0)
                etkili_artis_orani = (self.maliyet_carpani - 1.0) * hassasiyet
                dinamik_maliyet_carpani = 1.0 + etkili_artis_orani
                
                satis_fiyati = urun['Satis_Fiyati_TL'] * self.satis_fiyati_carpani
                tohum_maliyeti = urun['Tohum_Maliyeti_TL'] * dinamik_maliyet_carpani
                is_gucu_maliyeti = urun['Is_Gucu_Maliyeti_TL'] * self.isgucu_maliyet_carpani
                kuraklik_kayip_orani = self.su_krizi_etkisi * (urun['Su_Ihtiyaci_Puani'] / 10.0)
                dinamik_verim = urun['Beklenen_Verim_KG'] * (1 - kuraklik_kayip_orani)
            
                birim_kar = (dinamik_verim * satis_fiyati) - (tohum_maliyeti + is_gucu_maliyeti)
                risk_ayarli_kar = birim_kar * (1 - risk_skoru)

                for t in zaman_ufku:
                    obj_function.append(risk_ayarli_kar * x[i, j, t])

        model += pulp.lpSum(obj_function), "Yillik_Toplam_Kar"

        toplam_maliyet = []
        for i in tarla_idx:
            for j in urun_idx:
                urun = self.urunler.iloc[j]
                hassasiyet = urun.get('Maliyet_Hassasiyeti', 1.0)
                etkili_artis_orani = (self.maliyet_carpani - 1.0) * hassasiyet
                dinamik_maliyet_carpani = 1.0 + etkili_artis_orani
                
                maliyet = (urun['Tohum_Maliyeti_TL'] * dinamik_maliyet_carpani) + (urun['Is_Gucu_Maliyeti_TL'] * self.isgucu_maliyet_carpani)
                for t in zaman_ufku:
                    toplam_maliyet.append(maliyet * x[i, j, t])
        model += pulp.lpSum(toplam_maliyet) <= self.toplam_butce, "Toplam_Butce"

        for i in tarla_idx:
            tarla = self.tarlalar.iloc[i]
            tarla_sicaklik = tarla.get('Ortalama_Sicaklik_C', 15.0)
            tarla_toprak = str(tarla.get('Toprak_Tipi', '')).strip()

            for j in urun_idx:
                urun = self.urunler.iloc[j]
                urun_toprak = str(urun.get('Toprak_Tercihi', '')).strip()
                
                yetisme_gun = urun.get('Yetisme_Suresi', 120)
                yetisme_suresi_ay = math.ceil(yetisme_gun / 30.0)
                baslangic = self.get_ay_sayisal(urun['Ekim_Baslangic_Ay'], 1)

                for t in zaman_ufku:
                    gercek_ay = gercek_aylar[t]
                    takvim_uygun = (gercek_ay == baslangic) 
                    efektif_su_ihtiyaci = urun['Su_Ihtiyaci_Puani'] * (1 + self.su_krizi_etkisi)
                    efektif_suya_uzaklik_limiti = 300 * (1 - self.su_krizi_etkisi)
                    if tarla_toprak != urun_toprak:
                        model += x[i, j, t] == 0, f"Toprak_Ihlali_{i}_{j}_{t}"
                        continue
                    if not takvim_uygun:
                        model += x[i, j, t] == 0, f"Yanlis_Ay_{i}_{j}_{t}"
                        continue
                    if (tarla['Suya_Uzaklik_m'] > efektif_suya_uzaklik_limiti and efektif_su_ihtiyaci > 7):
                        model += x[i, j, t] == 0, f"Su_Ihlal_{i}_{j}_{t}"
                        continue
                    if (tarla_sicaklik < urun['Min_Sicaklik_C'] or tarla_sicaklik > urun['Max_Sicaklik_C']):
                        model += x[i, j, t] == 0, f"Sicaklik_Ihlal_{i}_{j}_{t}"

        import datetime
        mevcut_yil = datetime.datetime.now().year
        
        for i in tarla_idx:
            tarla = self.tarlalar.iloc[i]
            tarla_id = tarla['Tarla_ID']
            if tarla_id in self.occupied_fields:
                bitis_tarihi = self.occupied_fields[tarla_id]
                
                for t in zaman_ufku:
                    gercek_ay = gercek_aylar[t]
                    islem_yili = self.mevcut_yil + ((self.mevcut_ay - 1 + t) // 12)
                        
                    islem_tarihi = pd.to_datetime(f"{islem_yili}-{gercek_ay:02d}-01")
                    
                    if islem_tarihi < bitis_tarihi:
                        for j in urun_idx:
                            model += x[i, j, t] == 0, f"Hafiza_Dolu_{i}_{j}_Ay{t}"
        for i in tarla_idx:
            tarla = self.tarlalar.iloc[i]
            for k_ay in zaman_ufku:
                aktif_ekimler = []
                for j in urun_idx:
                    urun = self.urunler.iloc[j]
                    yetisme_suresi_ay = math.ceil(urun.get('Yetisme_Suresi', 120) / 30.0)
                    for t in range(k_ay + 1):
                        if t + yetisme_suresi_ay > k_ay:
                            aktif_ekimler.append(x[i, j, t])
                if aktif_ekimler:
                    model += pulp.lpSum(aktif_ekimler) <= tarla['Alan_Donum'], f"Kapasite_Tarla{i}_Ay{k_ay}"
        toplam_arazi = self.tarlalar['Alan_Donum'].sum()
        maksimum_ekim_orani = 0.40 

        for j in urun_idx:
            for k_ay in zaman_ufku:
                aktif_j_ekimleri = []
                urun = self.urunler.iloc[j]
                yetisme_suresi_ay = math.ceil(urun.get('Yetisme_Suresi', 120) / 30.0)
                for i in tarla_idx:
                    for t in range(k_ay + 1):
                        if t + yetisme_suresi_ay > k_ay:
                            aktif_j_ekimleri.append(x[i, j, t])
                if aktif_j_ekimleri:
                    model += pulp.lpSum(aktif_j_ekimleri) <= (toplam_arazi * maksimum_ekim_orani), f"Cesitlilik_Urun_{j}_Ay{k_ay}"
        
        model.solve(pulp.PULP_CBC_CMD(msg=False))

        butce_golge_fiyat = 0.0
        if model.status == pulp.LpStatusOptimal:
            butce_golge_fiyat = model.constraints["Toplam_Butce"].pi

        sonuclar = {
            "Durum": pulp.LpStatus[model.status],
            "Beklenen_Kar": pulp.value(model.objective) if pulp.value(model.objective) else 0.0,
            "Kullanilan_Butce": 0.0,
            "Butce_Golge_Fiyati": butce_golge_fiyat,
            "Ekim_Plani": []
        }

        ay_isimleri = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        zaman_ufku = list(range(12))
        gercek_aylar = [(self.mevcut_ay - 1 + t) % 12 + 1 for t in zaman_ufku]
        tarla_idx = self.tarlalar.index.tolist()
        urun_idx = self.urunler.index.tolist()

        if sonuclar["Durum"] == 'Optimal':
            for i in tarla_idx:
                for j in urun_idx:
                    for t in zaman_ufku:
                        if x[i, j, t].varValue is not None and x[i, j, t].varValue > 0.1:
                            alan = round(x[i, j, t].varValue, 2)
                            urun = self.urunler.iloc[j]
                            tarla = self.tarlalar.iloc[i]
                            gercek_ay = gercek_aylar[t]
                            hassasiyet = urun.get('Maliyet_Hassasiyeti', 1.0)
                            etkili_artis_orani = (self.maliyet_carpani - 1.0) * hassasiyet
                            dinamik_maliyet_carpani = 1.0 + etkili_artis_orani
                            yeni_tohum_maliyeti = urun['Tohum_Maliyeti_TL'] * dinamik_maliyet_carpani
                            yeni_satis_fiyati = urun['Satis_Fiyati_TL'] * self.satis_fiyati_carpani
                            yeni_isgucu_maliyeti = urun['Is_Gucu_Maliyeti_TL'] * self.isgucu_maliyet_carpani
                            maliyet_toplami = (yeni_tohum_maliyeti + yeni_isgucu_maliyeti) * alan
                            sonuclar["Kullanilan_Butce"] += maliyet_toplami
                            donum_basi_net_kar = (urun['Beklenen_Verim_KG'] * yeni_satis_fiyati) - (yeni_tohum_maliyeti + yeni_isgucu_maliyeti)
                            sonuclar["Ekim_Plani"].append({
                                "Tarla_ID": tarla['Tarla_ID'],
                                "Konum": tarla['Konum'],
                                "Ekim_Ayi": ay_isimleri[gercek_ay],
                                "Suya_Uzaklik_m": tarla['Suya_Uzaklik_m'],
                                "Urun_Adi": urun['Urun_Adi'],
                                "Ekilecek_Alan_Donum": alan,
                                "Eski_Tohum_Maliyeti": urun['Tohum_Maliyeti_TL'],
                                "Yeni_Tohum_Maliyeti": round(yeni_tohum_maliyeti, 2),
                                "Eski_Satis_Fiyati": urun['Satis_Fiyati_TL'],
                                "Yeni_Satis_Fiyati": round(yeni_satis_fiyati, 2),
                                "Urun_Su_Ihtiyaci": urun['Su_Ihtiyaci_Puani'],
                                "Don_Hassasiyeti": urun.get('Don_Hassasiyeti', 0.5),
                                "Donum_Basi_Net_Kar": round(donum_basi_net_kar, 2)  
                            })
        return sonuclar
