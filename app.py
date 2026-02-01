import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import scraper
import analysis

st.set_page_config(page_title="Indo Flood Watch", page_icon="🌧️", layout="wide")

st.title("Sistem Prediksi Cuaca Sebagai Panduan Aktivitas Masyarakat")
st.markdown("""
Menggunakan teknik *JSON API Scraping* di 50 Kota di Indonesia
""")

# --- SIDEBAR ---
st.sidebar.header("🕹️ Panel Kontrol")

# Koordinat Default: UNIKOM Bandung (Jl. Dipati Ukur)
# Lat: -6.8868, Lon: 107.6152
user_lat = st.sidebar.number_input("Latitude", value=-6.8868, format="%.4f")
user_lon = st.sidebar.number_input("Longitude", value=107.6152, format="%.4f")

hari_opsi = st.sidebar.selectbox("Pilih Hari Prediksi:", ["Hari Ini", "Besok", "Lusa"])

if st.sidebar.button("🔄 Scan Satelit Cuaca", type="primary"):
    st.cache_data.clear()
    st.rerun()

with st.spinner("Mengunduh data cuaca (JSON API)..."):
    raw_df = scraper.get_weather_data()
    
    if not raw_df.empty:
        processed_df = analysis.analisis_banjir(raw_df)
        final_df = analysis.hitung_jarak(processed_df, user_lat, user_lon)
        
        today = pd.Timestamp.now().normalize()
        if hari_opsi == "Besok": target_date = today + pd.Timedelta(days=1)
        elif hari_opsi == "Lusa": target_date = today + pd.Timedelta(days=2)
        else: target_date = today
            
        view_df = final_df[final_df['Waktu'].dt.date == target_date.date()].copy()
        
        def get_priority(status):
            if "BAHAYA" in status: return 3
            if "WASPADA" in status: return 2
            return 1
            
        view_df['Prioritas'] = view_df['Status_Risiko'].apply(get_priority)
        map_data = view_df.sort_values(['Prioritas', 'Curah_Hujan_mm'], ascending=[False, False]).drop_duplicates('Kota')
        
        # --- METRICS ---
        col1, col2, col3, col4 = st.columns(4)
        
        jml_merah = len(map_data[map_data['Status_Aktivitas'] == 3])
        jml_kuning = len(map_data[map_data['Status_Aktivitas'] == 2])
        jml_hijau = len(map_data[map_data['Status_Aktivitas'] == 1])
        
        col1.metric("Total Kota Terpantau", f"{len(map_data)} Kota", "Big Data Scope")
        
        if jml_merah > 0:
            col2.metric("Zona Tidak Kondusif 🌧️", f"{jml_merah} Kota", "Hindari Outdoor", delta_color="inverse")
        else:
            col2.metric("Cuaca Mendukung 🌤️", f"{jml_hijau} Kota", "Aman Beraktivitas")
            
        # --- PERBAIKAN ANTI-CRASH (SABUK PENGAMAN) ---
        if not view_df.empty:
            # Hanya hitung jika data TIDAK KOSONG
            terdekat = view_df.loc[view_df['Jarak_KM'].idxmin()]
            
            # Logic status user
            status_user = "Aman"
            if terdekat.get('Prioritas') == 3: status_user = "BAHAYA (Tunda Aktivitas)" # Pakai .get biar aman
            elif terdekat.get('Prioritas') == 2: status_user = "WASPADA (Sedia Payung)"
            else: status_user = "KONDUSIF"
            
            col3.metric(f"Kondisi {terdekat['Kota']}", f"{terdekat['Curah_Hujan_mm']} mm", status_user)
            
            max_rain = view_df.loc[view_df['Curah_Hujan_mm'].idxmax()]
            col4.metric("Pusat Hujan Tertinggi", f"{max_rain['Curah_Hujan_mm']} mm", max_rain['Kota'])
        else:
            # Jika data kosong (karena beda jam server), tampilkan strip "-"
            col3.metric("Lokasi Anda", "-", "Data Belum Tersedia")
            col4.metric("Pusat Hujan", "-", "Sedang Memuat...")

        tab1, tab2, tab3 = st.tabs(["🗺️ Peta Sebaran", "📊 Statistik Analisis", "📋 Database"])
        
        with tab1:
            st.caption(f"Visualisasi Peta Folium. Data: {target_date.date()}")
            col_peta, col_legenda = st.columns([3, 1])
            
            with col_peta:
                m = folium.Map(location=[-2.5, 118.0], zoom_start=4)
                
                folium.Marker(
                    [user_lat, user_lon], 
                    popup="Lokasi Anda", 
                    icon=folium.Icon(color="blue", icon="user")
                ).add_to(m)
                
                for index, row in map_data.iterrows():
                    if row['Prioritas'] == 3: warna = "red"
                    elif row['Prioritas'] == 2: warna = "orange"
                    else: warna = "green"
                    
                    folium.CircleMarker(
                        location=[row['Latitude'], row['Longitude']],
                        radius=5 + (row['Curah_Hujan_mm'] * 2),
                        popup=f"<b>{row['Kota']}</b><br>Hujan: {row['Curah_Hujan_mm']} mm<br>Status: {row['Status_Risiko']}",
                        color=warna,
                        fill=True,
                        fill_color=warna,
                        fill_opacity=0.8
                    ).add_to(m)
                
                st_folium(m, height=500, use_container_width=True)

            with col_legenda:
                st.write("### 📌 Indikator Warna")
                st.markdown("""
                <div style="background-color: #262730; padding: 15px; border-radius: 10px; border: 1px solid #444;">
                    <div style="margin-bottom: 10px;">
                        <span style='color: red; font-size: 20px;'>⬤</span> 
                        <span style="font-weight:bold; color: #ffcccc;">BAHAYA</span><br>
                        <span style="font-size: 12px; color: #ccc;">Hujan Lebat (>5mm) ATAU Badai Petir</span>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <span style='color: orange; font-size: 20px;'>⬤</span> 
                        <span style="font-weight:bold; color: #ffeebb;">WASPADA</span><br>
                        <span style="font-size: 12px; color: #ccc;">Hujan Sedang (1-5mm)</span>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <span style='color: green; font-size: 20px;'>⬤</span> 
                        <span style="font-weight:bold; color: #ccffcc;">AMAN</span><br>
                        <span style="font-size: 12px; color: #ccc;">Berawan / Cerah / Gerimis Halus</span>
                    </div>
                    <hr style="border-top: 1px solid #555; margin: 10px 0;">
                    <div>
                        <span style='font-size: 20px;'>🔵</span> 
                        <span style="font-weight:bold; color: #ccccff;">LOKASI ANDA</span><br>
                        <span style="font-size: 12px; color: #ccc;">(Ubah koordinat di Sidebar kiri)</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with tab2:
            st.subheader(f"Analisis Statistik Cuaca ({hari_opsi})")
            col_stat1, col_stat2 = st.columns(2)
            
            with col_stat1:
                st.markdown("**1. Proporsi Tingkat Risiko Wilayah**")
                status_counts = map_data['Status_Risiko'].value_counts()
                
                color_map = {

                    "BAHAYA (Potensi Banjir/ Hujan Badai)": "#ff4b4b",  
                    "WASPADA (Hujan)": "#ffa500",                       
                    "AMAN (Berawan/Cerah)": "#4caf50"                   
                }
                
                actual_colors = [color_map.get(x, '#999999') for x in status_counts.index]
                
                fig1, ax1 = plt.subplots(figsize=(6, 4))
                wedges, texts, autotexts = ax1.pie(status_counts, autopct='%1.1f%%', startangle=90, colors=actual_colors, textprops=dict(color="white", weight='bold'))
                ax1.legend(wedges, status_counts.index, title="Keterangan", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
                st.pyplot(fig1)
                
            with col_stat2:
                st.markdown("**2. Ranking Intensitas Hujan (Top 10)**")
                top_rain = map_data[map_data['Curah_Hujan_mm'] > 0].sort_values('Curah_Hujan_mm', ascending=True).tail(10)
                
                if not top_rain.empty:
                    fig2, ax2 = plt.subplots(figsize=(8, 5))
                    bars = ax2.barh(top_rain['Kota'], top_rain['Curah_Hujan_mm'], color='#2c3e50')
                    ax2.bar_label(bars, fmt='%.1f mm', padding=3)
                    ax2.spines['top'].set_visible(False)
                    ax2.spines['right'].set_visible(False)
                    st.pyplot(fig2)
                else:
                    st.info("Tidak ada hujan terukur (>0mm) saat ini.")

        with tab3:
            st.caption("Data mentah JSON.")
            st.dataframe(final_df)
            
    else:
        st.error("Gagal koneksi API.")