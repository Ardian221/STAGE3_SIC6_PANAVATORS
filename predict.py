import pandas as pd
import joblib

# Load Model & Encoder
model = joblib.load("models/air_quality_model.pkl")
encoder = joblib.load("models/label_encoder.pkl")

# Input Data ( bisa diganti )
temperature = 28.6
humidity = 90.0

# Buat Dataframe
input_df = pd.DataFrame([[temperature, humidity]], columns=["temperature", "humidity"])

# Prediksi
pred_encoded = model.predict(input_df)[0]
pred_label = encoder.inverse_transform([pred_encoded])[0]

# Hasil
print("Temperatur:", temperature)
print("Kelembaban:", humidity)
print("Prediksi kualitas udara:", pred_label)
