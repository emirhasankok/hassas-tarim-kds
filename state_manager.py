import json
import os
import datetime
import pandas as pd

STATE_FILE = "aktif_ekimler.json"

def load_active_plans():
    """Kayıtlı aktif ekim planlarını yükler."""
    if not os.path.exists(STATE_FILE):
        return []
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_active_plans(plans):
    """Yeni ekim planlarını JSON dosyasına kaydeder."""
    current_plans = load_active_plans()
    current_plans.extend(plans)
    
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(current_plans, f, ensure_ascii=False, indent=4)
    return True

def get_occupied_fields(mevcut_yil, mevcut_ay):
    active_plans = load_active_plans()
    occupied_fields = {} 
    
    current_date = pd.to_datetime(f"{mevcut_yil}-{mevcut_ay:02d}-01")
    
    for plan in active_plans:
        baslangic_tarihi = pd.to_datetime(plan['Baslangic_Tarihi'])
        bitis_tarihi = pd.to_datetime(plan['Bitis_Tarihi'])
        
        if current_date < bitis_tarihi:
            occupied_fields[plan['Tarla_ID']] = bitis_tarihi

    return occupied_fields
def clear_active_plans():
    """Kayıtlı hafızayı (aktif ekimleri) tamamen siler."""
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    return True
