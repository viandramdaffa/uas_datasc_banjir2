import pandas as pd
import requests
import streamlit as st
import datetime

# DAFTAR 50 KOTA (Sama seperti sebelumnya)
KOTA_PILIHAN = [
    {"nama": "Jakarta Pusat", "lat": -6.1805, "lon": 106.8284},
    {"nama": "Jakarta Selatan", "lat": -6.2615, "lon": 106.8106},
    {"nama": "Bandung", "lat": -6.9175, "lon": 107.6191},
    {"nama": "Semarang", "lat": -6.9667, "lon": 110.4167},
    {"nama": "Surabaya", "lat": -7.2575, "lon": 112.7521},
    {"nama": "Yogyakarta", "lat": -7.7956, "lon": 110.3695},
    {"nama": "Serang", "lat": -6.1200, "lon": 106.1503},
    {"nama": "Cirebon", "lat": -6.7320, "lon": 108.5523},
    {"nama": "Malang", "lat": -7.9666, "lon": 112.6326},
    {"nama": "Banyuwangi", "lat": -8.2192, "lon": 114.3691},
    {"nama": "Bogor", "lat": -6.5971, "lon": 106.8060},
    {"nama": "Solo", "lat": -7.5755, "lon": 110.8243},
    {"nama": "Tegal", "lat": -6.8694, "lon": 109.1402},
    {"nama": "Kediri", "lat": -7.8485, "lon": 112.0178},
    {"nama": "Banda Aceh", "lat": 5.5483, "lon": 95.3238},
    {"nama": "Medan", "lat": 3.5952, "lon": 98.6722},
    {"nama": "Padang", "lat": -0.9492, "lon": 100.4172},
    {"nama": "Pekanbaru", "lat": 0.5071, "lon": 101.4478},
    {"nama": "Batam", "lat": 1.0456, "lon": 104.0305},
    {"nama": "Jambi", "lat": -1.6101, "lon": 103.6131},
    {"nama": "Palembang", "lat": -2.9909, "lon": 104.7567},
    {"nama": "Bengkulu", "lat": -3.8004, "lon": 102.2655},
    {"nama": "Bandar Lampung", "lat": -5.3971, "lon": 105.2668},
    {"nama": "Pangkal Pinang", "lat": -2.1386, "lon": 106.1183},
    {"nama": "Sabang", "lat": 5.8942, "lon": 95.3192},
    {"nama": "Pontianak", "lat": -0.0263, "lon": 109.3425},
    {"nama": "Samarinda", "lat": -0.5017, "lon": 117.1571},
    {"nama": "Banjarmasin", "lat": -3.3167, "lon": 114.5928},
    {"nama": "Balikpapan", "lat": -1.2379, "lon": 116.8529},
    {"nama": "Palangkaraya", "lat": -2.2106, "lon": 113.9145},
    {"nama": "Tarakan", "lat": 3.3000, "lon": 117.6333},
    {"nama": "Makassar", "lat": -5.1477, "lon": 119.4328},
    {"nama": "Manado", "lat": 1.4748, "lon": 124.8421},
    {"nama": "Palu", "lat": -0.9011, "lon": 119.8707},
    {"nama": "Kendari", "lat": -3.9972, "lon": 122.5121},
    {"nama": "Gorontalo", "lat": 0.5435, "lon": 123.0668},
    {"nama": "Mamuju", "lat": -2.6778, "lon": 118.8841},
    {"nama": "Denpasar", "lat": -8.6705, "lon": 115.2126},
    {"nama": "Mataram", "lat": -8.5815, "lon": 116.1166},
    {"nama": "Kupang", "lat": -10.1772, "lon": 123.6070},
    {"nama": "Labuan Bajo", "lat": -8.4907, "lon": 119.8824},
    {"nama": "Ambon", "lat": -3.6536, "lon": 128.1906},
    {"nama": "Ternate", "lat": 0.7843, "lon": 127.3757},
    {"nama": "Jayapura", "lat": -2.5000, "lon": 140.7167},
    {"nama": "Manokwari", "lat": -0.8615, "lon": 134.0625},
    {"nama": "Sorong", "lat": -0.8797, "lon": 131.2461},
    {"nama": "Merauke", "lat": -8.4991, "lon": 140.4049},
    {"nama": "Timika", "lat": -4.5468, "lon": 136.8837}
]

@st.cache_data(ttl=3600)
def get_weather_data():
    all_data = []
    bar = st.progress(0, text="Menghubungkan ke satelit Open-Meteo...")
    
    for i, kota in enumerate(KOTA_PILIHAN):
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={kota['lat']}&longitude={kota['lon']}&hourly=precipitation,weathercode&timezone=auto"
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            hourly = data['hourly']
            times = hourly['time']
            rains = hourly['precipitation'] 
            codes = hourly['weathercode']
            
            for j in range(len(times)):
                all_data.append({
                    'Kota': kota['nama'],
                    'Latitude': kota['lat'],
                    'Longitude': kota['lon'],
                    'Waktu_Str': times[j],
                    'Curah_Hujan_mm': float(rains[j]),
                    'Kode_Cuaca': codes[j]
                })
                
            bar.progress((i + 1) / len(KOTA_PILIHAN), text=f"Mengambil data: {kota['nama']}")
            
        except Exception as e:
            continue
            
    bar.empty()
    return pd.DataFrame(all_data)