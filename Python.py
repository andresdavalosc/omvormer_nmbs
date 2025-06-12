import serial
import time
import requests

# Config InfluxDB
ORG = "WIE"
BUCKET = "demo_data"
TOKEN = "EY-7AoVga8YlHwtphYvVWOEiwZmq7BABTGXeOrU-GxnZRA2TOWwMBRj2oWGz29kYyYpLHOUMYBuNMQShVF0Hkg=="
URL = f"https://eu-central-1-1.aws.cloud2.influxdata.com/api/v2/write?org={ORG}&bucket={BUCKET}&precision=s"

# Serial instellingen
SERIAL_PORT = "/dev/ttyS0"
BAUDRATE = 9600
TIMEOUT = 1

# Metingen namen
measurement_names = [
    "IDX_AVG_VIN2", "IDX_AVG_IDC", "IDX_AVG_VPH3", "IDX_AVG_VPH2", "IDX_AVG_VPH1",
    "IDX_AVG_IPH3", "IDX_AVG_IPH2", "IDX_AVG_IPH1", "IDX_INV_REG", "IDX_AVG_VBRIDGE1",
    "IDX_AVG_VBRIDGE2", "BYTE_11", "BYTE_12", "BYTE_13", "BYTE_14", "BYTE_15",
    "IDX_AVG_TMP_CONV", "IDX_AVG_TMP_INV", "IDX_AVG_TMP_TRAFO", "IDX_AVG_TMP_ROOM1",
    "IDX_AVG_TMP_ROOM2", "IDX_AVG_TMP_LPF1", "IDX_AVG_TMP_LPF2",
    "IDX_STATUS0", "IDX_STATUS1", "IDX_STATUS2", "IDX_STATUS3", "IDX_STATUS4",
    "IDX_GPIO_OUT", "IDX_GPIO_IN", "IDX_STATUS", "IDX_ERROR"
]

def to_binary_str(val):
    return format(val, '016b')

def to_hex_str(val):
    return f"0x{val:04X}"

def print_values(vals):
    for i, val in enumerate(vals):
        name = measurement_names[i] if i < len(measurement_names) else f"BYTE_{i}"
        bin_str = to_binary_str(val)
        dec_str = f"{val:6d}"
        hex_str = to_hex_str(val)
        print(f"{name:<18}: {bin_str}  {dec_str}  {hex_str}")

def send_to_influx(vals, timestamp):
    lines = []
    for i, val in enumerate(vals):
        measurement = measurement_names[i] if i < len(measurement_names) else f"BYTE_{i}"
        lines.append(f"{measurement} value={val} {timestamp}")

    lines.append(f"RPi_ON value=1 {timestamp}")
    payload = "\n".join(lines)
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "text/plain; charset=utf-8"
    }

    try:
        resp = requests.post(URL, headers=headers, data=payload)
        if resp.status_code != 204:
            print(f"⚠️ Fout bij InfluxDB schrijven: {resp.status_code} {resp.text}")
        else:
            print(f"✅ Data verstuurd naar InfluxDB @ {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}")
    except Exception as e:
        print(f"❌ Verbindingsfout InfluxDB: {e}")

def open_serial_with_retry():
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, baudrate=BAUDRATE, timeout=TIMEOUT)
            print("🔌 Verbonden met serial poort.")
            return ser
        except Exception as e:
            print(f"⚠️ Kan serial poort niet openen: {e}")
            print("🔁 Probeer opnieuw over 6 seconden...")
            time.sleep(6)

def init_modem():
    MAX_RETRIES = 10
    RETRY_DELAY = 3
    device_available = False

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ser = serial.Serial('/dev/ttyUSB2', baudrate=115200, timeout=1)
        except serial.SerialException:
            print(f"📡 Modem niet gevonden op poging {attempt}/{MAX_RETRIES}. Wachten {RETRY_DELAY} seconden...")
            time.sleep(RETRY_DELAY)
        else:
            device_available = True
            break

    if device_available:
        print("📶 Modem gevonden. PIN code instellen...")
        try:
            ser.write(b'AT+CPIN?\r\n')
            time.sleep(1)
            ser.write(b'AT+CPIN=2713\r\n')
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Fout bij verzenden van PIN: {e}")
        finally:
            ser.close()
    else:
        print("❌ Modem niet beschikbaar. Ga verder zonder sim-initialisatie.")

def main():
    init_modem()  # Eerst modem init
    ser = open_serial_with_retry()

    while True:
        try:
            raw = ser.read(64)
            if len(raw) != 64:
                print("⏳ Geen volledige 64 bytes ontvangen... vul met nullen.")
                raw = bytes([0] * 64)

            values = []
            for i in range(0, 64, 2):
                val = (raw[i] << 8) + raw[i + 1]
                values.append(val)

            print("\n📥 Nieuwe data ontvangen:")
            print_values(values)

            ts = int(time.time())
            send_to_influx(values, ts)
        except serial.SerialException as e:
            print(f"🚫 Serial fout: {e}")
            print("🔁 Herstarten serial verbinding...")
            ser.close()
            time.sleep(6)
            ser = open_serial_with_retry()
        except KeyboardInterrupt:
            print("🛑 Script handmatig gestopt.")
            break
        except Exception as e:
            print(f"❌ Onbekende fout: {e}")
            print("⏱️ Wachten en doorgaan...")
            time.sleep(6)

        time.sleep(6)

if __name__ == "__main__":
    main()
