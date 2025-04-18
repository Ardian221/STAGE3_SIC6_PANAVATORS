#Menambahkan library
import network
import time
import dht
from machine import ADC, Pin, PWM
from time import sleep
import urequests

#Menghubungkan ke WiFi
SSID = "Galaxy M15"
PASSWORD = "machobay"
#URL MongoDB dan Ubidots
API_URL = "http://192.168.253.148:5000/api/dht"

#Definisi untuk terhubungan ke Wifi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    while not wlan.isconnected():
        pass

    print("terhubung wipi:", wlan.ifconfig())


connect_wifi()

#input pin sensor
sensor = dht.DHT11(Pin(14))          # DHT11 di GPIO34
mq135 = ADC(Pin(35))                 # MQ135 di GPIO35
mq135.atten(ADC.ATTN_11DB)           # Rentang 0 - 3.3V
mq135.width(ADC.WIDTH_12BIT)         # Resolusi 12-bit (0 - 4095)

servo = PWM(Pin(13), freq=50)

#def atur posisi servo
def set_servo(angle):
    duty = int((angle / 180) * 102 + 26)  # hitung duty cycle: 26-128
    servo.duty(duty)


#Definisi untuk data sensor
def send_data():
    try:
        sleep(2)
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()
        gas_value = mq135.read()

        year, month, mday, hour, minute, second, _, _ = time.localtime()
        timestamp = f"{mday:02d}-{month:02d}-{year} {hour:02d}:{minute:02d}:{second:02d}"
        
        
        data = {
            "temperature": temp,
            "humidity": hum,
            "gas_value": gas_value,
            "timestamp": timestamp
        }

      
        print("Data:", data)

        response = urequests.post(API_URL, json=data)
        print("Status:", response.status_code)
        print("Respon:", response.text)
        response.close()
        
        
        if gas_value > 500:
            print("Gas tinggi! Menyalakan servo.")
            set_servo(170)  # servo buka (misalnya)
        else:
            print("Gas normal. Servo diam.")
            set_servo(0)  # servo tutup (misalnya)
            
            
    except OSError as e:
        print('Gagal baca sensor:', e)
    except Exception as ex:
        print("Gagal kirim data:", ex)
        
        
while True:
    send_data()
    sleep(10)