import numpy as np
import pandas as pd
import joblib

# Load model dan encoder
model = joblib.load("models/air_quality_model.pkl")
encoder = joblib.load("models/label_encoder.pkl")

# Buat grid kombinasi suhu dan kelembaban
temps = np.arange(20, 41, 1)          # 20°C - 40°C
humidities = np.arange(40, 91, 5)     # 40% - 90%

candidates = []

for temp in temps:
    for hum in humidities:
        df = pd.DataFrame([[temp, hum]], columns=["temperature", "humidity"])
        pred_encoded = model.predict(df)[0]
        label = encoder.inverse_transform([pred_encoded])[0]
        if label == "Sedang":
            candidates.append((temp, hum))

# Tampilkan hasil
if candidates:
    print("Kombinasi temperatur & kelembaban yang menghasilkan 'Sedang':")
    for t, h in candidates:
        print(f"- Temperatur: {t}°C, Kelembaban: {h}%")
else:
    print("Tidak ada kombinasi yang memprediksi 'Sedang'")
