import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import joblib
import os

# Koneksi MongoDB
uri = "mongodb+srv://sejatipanca8:B9rUXblCpH129ugQ@cluster1.fcj1t1l.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
client = MongoClient(uri, server_api=ServerApi("1"))
db = client["MyDatabase"]
collection = db["MyDht"]

# Ambil Data dari MongoDB
print("Mengambil data dari MongoDB...")
data = list(collection.find())
for item in data:
    item.pop('_id', None)

df = pd.DataFrame(data)
print("Contoh data:\n", df.head())

# Visualisasi Distribusi gas_value
plt.figure(figsize=(6, 4))
df["gas_value"].hist(bins=20, color='skyblue', edgecolor='black')
plt.title("Distribusi Nilai Gas")
plt.xlabel("gas_value")
plt.ylabel("Frekuensi")
plt.grid(True)
plt.tight_layout()
plt.savefig("models/distribusi_gas.png")
plt.close()

# Konversi gas_value menjadi air_quality
def gas_to_quality(gas):
    if gas < 350:
        return "Baik"
    elif gas < 450:
        return "Sedang"
    else:
        return "Buruk"

df["air_quality"] = df["gas_value"].apply(gas_to_quality)

# Cek distribusi label setelah mapping
print("\nDistribusi air_quality:")
print(df["air_quality"].value_counts())

# Validasi kolom
required_columns = ["temperature", "humidity", "air_quality"]
if not all(col in df.columns for col in required_columns):
    raise ValueError(f"Data harus mengandung kolom: {required_columns}")

# Preprocessing
X = df[["temperature", "humidity"]]
y = df["air_quality"]

# Label Encoding
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Split Data
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

# Latih Model dengan class_weight balanced
print("\nMelatih model RandomForest (balanced)...")
model = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
model.fit(X_train, y_train)

# Evaluasi Model
y_pred = model.predict(X_test)
report = classification_report(y_test, y_pred, target_names=label_encoder.classes_)
print("\nLaporan Evaluasi Model:")
print(report)

# Simpan Model dan Encoder
os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/air_quality_model.pkl")
joblib.dump(label_encoder, "models/label_encoder.pkl")
print("\nModel dan encoder berhasil disimpan ke folder 'models'")
