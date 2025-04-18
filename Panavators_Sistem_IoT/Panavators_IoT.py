from flask import Flask, request, jsonify
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from huggingface_hub import snapshot_download
snapshot_download(repo_id="hexgrad/Kokoro-82M", local_dir="kokoro_model", ignore_patterns=["*.onnx", "*.tflite"])
from kokoro import KPipeline
from IPython.display import Audio, display
import soundfile as sf
from bson.binary import Binary
import threading
import time
import requests
import playsound
import simpleaudio as sa
import os
import uuid

app = Flask(__name__)

# Inisialisasi pipeline suara
pipeline = KPipeline(lang_code='a')

# Koneksi MongoDB
uri = "mongodb+srv://sejatipanca8:B9rUXblCpH129ugQ@cluster1.fcj1t1l.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
client = MongoClient(uri, server_api=ServerApi("1"))
db = client["MyDatabase"]
collection = db["MyDht"]

try:
    client.admin.command('ping')
    print("✅ Berhasil konek ke MongoDB!")
except Exception as e:
    print("❌ MongoDB Error:", e)

# Konfigurasi Ubidots
UBIDOTS_TOKEN = "BBUS-sDYUkgQctxYs76t50BtXzym28icGJU"
DEVICE_LABEL = "esp32-panavators"
UBIDOTS_URL = f"http://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}"
UBIDOTS_HEADERS = {
    'X-Auth-Token': UBIDOTS_TOKEN,
    'Content-Type': 'application/json'
}

# Endpoint menerima data dari ESP32
@app.route("/api/dht", methods=["POST"])
def receive_data():
    try:
        data = request.json
        print("📥 Data Diterima:", data)

        if not all(k in data for k in ("temperature", "humidity", "gas_value")):
            return jsonify({"error": "Missing data fields"}), 400

        collection.insert_one(data)
        print("✅ Data disimpan ke MongoDB!")

        ubidots_payload = {
            "temperature": data["temperature"],
            "humidity": data["humidity"],
            "gas_value": data["gas_value"]
        }

        ubidots_response = requests.post(UBIDOTS_URL, headers=UBIDOTS_HEADERS, json=ubidots_payload)
        ubidots_response.raise_for_status()

        return jsonify({
            "message": "Data saved",
            "ubidots_response": ubidots_response.json()
        }), 201

    except requests.exceptions.RequestException as e:
        return jsonify({"message": "Data saved to MongoDB", "ubidots_error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint mengambil semua data
@app.route("/api/dht", methods=["GET"])
def get_data():
    data = list(collection.find({}, {"_id": 0}))
    return jsonify(data), 200

# Pemantauan data & TTS
GAS_THRESHOLD = 350
last_id = None
last_gas_value = None

def monitor_gas():
    global last_id, last_gas_value
    print("⏳ Memulai pemantauan MongoDB...\n")
    while True:
        try:
            latest_data = collection.find_one(sort=[("timestamp", -1)])
            if latest_data:
                current_id = str(latest_data["_id"])
                gas = latest_data["gas_value"]

                if current_id != last_id or gas != last_gas_value:
                    if gas > GAS_THRESHOLD:
                        text = "Kualitas udara di dalam ruangan tidak sehat. Air purifier menyala dan buka jendela."
                    else:
                        text = "Kualitas udara di dalam ruangan sehat. Tidak perlu tindakan."

                    print(f"🎧 Suara (gas: {gas}): {text}")
                    generator = pipeline(text, voice='af_heart')
                    for i, (gs, ps, audio) in enumerate(generator):
                        filename = f'alert_{uuid.uuid4().hex}.wav'
                        sf.write(filename, audio, 24000)

                        with open(filename, 'rb') as f:
                            audio_binary = Binary(f.read())

                        collection.update_one(
                            {"_id": latest_data["_id"]},
                            {"$set": {"audio_file": audio_binary}}
                        )

                        playsound.playsound(filename)
                        os.remove(filename)

                    last_id = current_id
                    last_gas_value = gas
                else:
                    print(f"✅ Gas normal ({gas}) atau data sudah dibacakan.")
            else:
                print("⚠️ Tidak ada data ditemukan di MongoDB.")
        except Exception as e:
            print("❌ Error:", e)

        time.sleep(10)

# Endpoint memutar audio terakhir dari MongoDB
@app.route("/play-latest-audio", methods=["GET"])
def play_latest_audio():
    try:
        latest_audio = collection.find_one(
            {"audio_file": {"$exists": True}}, sort=[("timestamp", -1)]
        )
        if not latest_audio:
            return jsonify({"error": "No audio with audio_file found"}), 404

        audio_data = latest_audio["audio_file"]
        filename = f"audio_{uuid.uuid4().hex}.wav"

        with open(filename, "wb") as f:
            f.write(audio_data)

        wave_obj = sa.WaveObject.from_wave_file(filename)
        play_obj = wave_obj.play()
        play_obj.wait_done()

        os.remove(filename)

        return jsonify({"message": "Audio played successfully!"}), 200

    except Exception as e:
        print("❌ Error saat memutar audio:", e)
        return jsonify({"error": str(e)}), 500

# Jalankan Flask & TTS monitor bersamaan
if __name__ == "__main__":
    threading.Thread(target=monitor_gas, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True)
