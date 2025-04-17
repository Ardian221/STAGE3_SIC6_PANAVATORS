import streamlit as st
import pandas as pd
import joblib
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import base64
import io

# Koneksi ke MongoDB
@st.cache_resource
def load_mongodb():
    uri = "mongodb+srv://sejatipanca8:B9rUXblCpH129ugQ@cluster1.fcj1t1l.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
    client = MongoClient(uri, server_api=ServerApi("1"))
    db = client["MyDatabase"]
    collection = db["MyDht"]
    return collection

# Load Model
@st.cache_resource
def load_model():
    model = joblib.load("models/air_quality_model.pkl")
    encoder = joblib.load("models/label_encoder.pkl")
    return model, encoder

# Konversi gas_value ke kualitas udara
def gas_to_quality(gas):
    if gas < 400:
        return "Baik"
    elif gas < 500:
        return "Sedang"
    else:
        return "Buruk"

# Load Data dari MongoDB
def load_data(collection):
    data = list(collection.find())
    for item in data:
        item.pop('_id', None)
    df = pd.DataFrame(data)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
        df = df.dropna(subset=["timestamp", "temperature", "humidity", "gas_value"])
        df["temperature"] = pd.to_numeric(df["temperature"])
        df["humidity"] = pd.to_numeric(df["humidity"])
        df["gas_value"] = pd.to_numeric(df["gas_value"])
        df["air_quality"] = df["gas_value"].apply(gas_to_quality)
    return df

# Streamlit Config
st.set_page_config(page_title="SMAPPA", layout="wide")
st.title("🌬️ _SMAPPA_")
st.subheader("_Smart Air Purifier by Panavators_")
st.markdown("""
<div style='display: flex; justify-content: flex-start; font-size: 0.8rem; color: gray; gap: 10px; margin-top: 10px;'>
    <div>Created by Panavators</div>
    <div>|</div>
    <div>Supported by MAN 1 KOTA SUKABUMI</div>
    <div>|</div>
    <div>Powered by HuggingFace</div>
</div>
""", unsafe_allow_html=True)

st.divider()

# Menu & Refresh
menu = st.sidebar.selectbox("Pilih Menu", ["📈 Monitoring Data", "🔮 Prediksi AI"])
refresh = st.sidebar.checkbox("🔄 Auto-refresh data (30 detik)", value=True)

model, encoder = load_model()
collection = load_mongodb()

if refresh:
    st.experimental_rerun_delay = 30  # Auto Refresh

# Monitoring Page
if menu == "📈 Monitoring Data":
    st.subheader("📊 Grafik Monitoring Kualitas Udara")

    df = load_data(collection)

    if df.empty:
        st.warning("Data dari MongoDB masih kosong.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 🍃Grafik Kualitas Udara")
            st.line_chart(df.set_index("timestamp")[["gas_value"]])
        with col2:
            st.markdown("##### 🌡️Temperatur & 💧Kelembaban")
            st.line_chart(df.set_index("timestamp")[["temperature", "humidity"]])

        st.markdown("---")
        st.markdown("### 🗒️Tabel Data Terbaru")
        st.dataframe(df.sort_values("timestamp", ascending=False).head(20), use_container_width=True)

        # 🔊 Pilih Audio dari Data Terakhir
        if "audio_file" in df.columns:
            df_audio = df.dropna(subset=["audio_file"]).sort_values("timestamp", ascending=False)
            if not df_audio.empty:
                df_audio = df_audio.head(10)  # Ambil hingga 10 data terakhir
                df_audio["air_quality"] = df_audio["gas_value"].apply(gas_to_quality)
                df_audio["display"] = df_audio.apply(
                    lambda row: f"{row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {row['air_quality']}", axis=1
                )

                selected_display = st.selectbox(
                    "🎧 Pilih Waktu & Kualitas Udara Audio",
                    options=df_audio["display"],
                    help="Audio dari data dengan kualitas udara yang direkam"
                )

                selected_row = df_audio[df_audio["display"] == selected_display].iloc[0]
                try:
                    audio_base64 = selected_row["audio_file"]
                    audio_bytes = base64.b64decode(audio_base64)
                    audio_buffer = io.BytesIO(audio_bytes)
                    st.audio(audio_buffer, format="audio/wav")
                except Exception as e:
                    st.error(f"Gagal memutar audio: {e}")
            else:
                st.info("Tidak ada data dengan audio.")
            st.write(f"Ukuran audio: {len(audio_bytes)} bytes")
            st.caption("_*Klik tombol Play secara manual. Streamlit tidak mendukung autoplay audio._")


# Prediksi Page
elif menu == "🔮 Prediksi AI":
    st.subheader("🔮 Prediksi Kualitas Udara Berdasarkan Input")

    temperature = st.number_input("🌡️ Temperatur (°C)", min_value=-10.0, max_value=60.0, value=30.0, step=0.1)
    humidity = st.number_input("💧 Kelembaban (%)", min_value=0.0, max_value=100.0, value=75.0, step=0.1)

    if st.button("Prediksi Sekarang"):
        input_df = pd.DataFrame([[temperature, humidity]], columns=["temperature", "humidity"])
        pred_encoded = model.predict(input_df)[0]
        pred_label = encoder.inverse_transform([pred_encoded])[0]

        st.success(f"Prediksi kualitas udara: **{pred_label}**")
        st.dataframe(input_df)

# Footer
st.markdown("---")
st.caption("🔗 Terhubung ke MongoDB | Panavators SIC6")