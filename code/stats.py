import pandas as pd
import glob

# Tüm dosyaları okuyarak birleştirme işlemi
dosya_yolu = "excel/data/*.csv"  # Dosyaların bulunduğu dizin
dosyalar = glob.glob(dosya_yolu)

# Boş bir DataFrame oluştur
birlesik_veri = pd.DataFrame()

# Her bir dosyayı okuyup birleştirme işlemi
for dosya in dosyalar:
    veri = pd.read_csv(dosya)
    birlesik_veri = pd.concat([birlesik_veri, veri])

# Birleştirilmiş veriyi yeni bir CSV dosyasına yazma
birlesik_veri.to_csv('all_vehicle_stats.csv', index=False)
