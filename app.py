import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import scraper
import analysis
import pytz 

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Indo Activity Weather", page_icon="is", layout="wide")

# --- HEADER ---
st.title("Sistem Prediksi Cuaca Sebagai Panduan Aktivitas Masyarakat")
st.markdown("""
Menggunakan teknik *JSON API Scraping* di 50 Kota di Indonesia
""")

# --- SIDEBAR ---
st.sidebar.header("Panel Kontrol")
user_lat = st.sidebar.number_input("Latitude", value=-6.8868, format="%.4f")
user_lon = st.sidebar.number_input("Longitude", value=107.6152, format="%.4f")
hari_opsi = st.sidebar.selectbox("Pilih Jadwal Kegiatan:", ["Hari Ini", "Besok", "Lusa"])

if st.sidebar.button("Refresh", type="primary"):
    st.cache_data.clear()
    st.rerun()

# --- MAIN LOGIC ---
with st.spinner("Menganalisis data aktivitas..."):
    raw_df = scraper.get_weather_data()
    
    if not raw_df.empty:
        processed_df = analysis.analisis_banjir(raw_df)
        final_df = analysis.hitung_jarak(processed_df, user_lat, user_lon)
        
        # FIX TIMEZONE: Force Jakarta Time
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        today = pd.Timestamp.now(jakarta_tz).normalize()
        target_date = today.tz_localize(None)
        
        if hari_opsi == "Besok": 
            target_date = target_date + pd.Timedelta(days=1)
        elif hari_opsi == "Lusa": 
            target_date = target_date + pd.Timedelta(days=2)
            
        view_df = final_df[final_df['Waktu'].dt.date == target_date.date()].copy()
        
        if not view_df.empty:
            def get_activity_status(row):
                hujan = row['Curah_Hujan_mm']
                kode = row['Kode_Cuaca']
                
                # Logic: 3 (Danger), 2 (Warning), 1 (Safe)
                if hujan > 5.0 or kode >= 95:
                    return 3
                elif hujan > 1.0 or (60 <= kode <= 85):
                    return 2
                return 1

            view_df['Status_Aktivitas'] = view_df.apply(get_activity_status, axis=1)
            map_data = view_df.sort_values(['Status_Aktivitas', 'Curah_Hujan_mm'], ascending=[False, False]).drop_duplicates('Kota')
        else:
            map_data = pd.DataFrame()

        # --- DASHBOARD METRICS (RESTORED STYLE) ---
        col1, col2, col3, col4 = st.columns(4)
        
        if not map_data.empty:
            jml_merah = len(map_data[map_data['Status_Aktivitas'] == 3])
            
            # Metric 1: Total Data Diolah (Using raw_df for big numbers like 8064 Rows)
            col1.metric("Total Data Diolah", f"{len(raw_df)} Rows", "JSON Source")
            
            # Metric 2: Status Bahaya
            if jml_merah > 0:
                col2.metric("Status Bahaya 🔴", f"{jml_merah} Kota", "Potensi Badai/Banjir", delta_color="inverse")
            else:
                col2.metric("Status Bahaya", "0 Kota", "Aman Terkendali")
            
            # Metric 3: Lokasi Anda
            terdekat = map_data.loc[map_data['Jarak_KM'].idxmin()]
            col3.metric("Lokasi Anda", terdekat['Kota'], f"Jarak: {terdekat['Jarak_KM']} KM")
            
            # Metric 4: Hujan Terderas
            max_rain = map_data.loc[map_data['Curah_Hujan_mm'].idxmax()]
            col4.metric("Hujan Terderas", f"{max_rain['Curah_Hujan_mm']} mm", max_rain['Kota'])

            # --- TABS ---
            tab1, tab2, tab3 = st.tabs(["Peta Sebaran", "Statistik Analisis", "Database"])
            
            # TAB 1: Map
            with tab1:
                st.caption(f"Visualisasi Peta Folium. Data: {target_date.date()}")
                col_peta, col_legenda = st.columns([3, 1])
                
                with col_peta:
                    m = folium.Map(location=[-2.5, 118.0], zoom_start=4)
                    folium.Marker([user_lat, user_lon], popup="Posisi Anda", icon=folium.Icon(color="blue", icon="user")).add_to(m)
                    
                    for index, row in map_data.iterrows():
                        if row['Status_Aktivitas'] == 3: 
                            warna, rek = "red", "BAHAYA"
                        elif row['Status_Aktivitas'] == 2: 
                            warna, rek = "orange", "WASPADA"
                        else: 
                            warna, rek = "green", "AMAN"
                        
                        folium.CircleMarker(
                            location=[row['Latitude'], row['Longitude']],
                            radius=4 + (row['Curah_Hujan_mm'] * 1.5),
                            popup=f"<b>{row['Kota']}</b><br>{rek}<br>Hujan: {row['Curah_Hujan_mm']} mm",
                            color=warna, fill=True, fill_color=warna, fill_opacity=0.7
                        ).add_to(m)
                    
                    st_folium(m, height=500, use_container_width=True)

                with col_legenda:
                    st.write("### Indikator Warna")
                    st.markdown("""
                    <div style="background-color: #262730; padding: 15px; border-radius: 10px; border: 1px solid #444;">
                        <div style="margin-bottom: 10px;"><span style='color: red; font-size: 20px;'>⬤</span> <b>BAHAYA</b><br><span style="font-size: 11px;">Hujan Lebat (>5mm) / Badai.</span></div>
                        <div style="margin-bottom: 10px;"><span style='color: orange; font-size: 20px;'>⬤</span> <b>WASPADA</b><br><span style="font-size: 11px;">Hujan Sedang (1-5mm).</span></div>
                        <div style="margin-bottom: 10px;"><span style='color: green; font-size: 20px;'>⬤</span> <b>AMAN</b><br><span style="font-size: 11px;">Berawan / Cerah / Gerimis.</span></div>
                    </div>
                    """, unsafe_allow_html=True)

            # TAB 2: Statistics
            with tab2:
                st.subheader("Analisis Statistik Cuaca")
                col_stat1, col_stat2 = st.columns(2)
                
                with col_stat1:
                    st.markdown("**1. Proporsi Tingkat Risiko Wilayah**")
                    
                    status_counts = map_data['Status_Aktivitas'].value_counts().rename({
                        3: "BAHAYA (Potensi Banjir/ Hujan Badai)", 
                        2: "WASPADA (Hujan)",
                        1: "AMAN (Berawan/Cerah)"
                    })
                    
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
                        bars = ax2.barh(top_rain['Kota'], top_rain['Curah_Hujan_mm'], color='#34495e')
                        ax2.bar_label(bars, fmt='%.1f mm', padding=3)
                        ax2.spines['top'].set_visible(False)
                        ax2.spines['right'].set_visible(False)
                        st.pyplot(fig2)
                    else:
                        st.info("Tidak ada hujan terukur (>0mm) saat ini.")

            # TAB 3: Data
            with tab3:
                st.dataframe(final_df)
                
        else:
            # Fallback jika data kosong (tapi harusnya sudah aman karena Timezone fix)
            st.warning("⚠️ Data cuaca belum tersedia. Mencoba sinkronisasi ulang...")
            col1.metric("Status Data", "0 Rows", "Empty")
            
    else:
        st.error("Gagal terhubung ke API Server.")