import serial
import time
import requests

# 🌐 InfluxDB-configuratie
ORG = "WIE"
BUCKET = "demo_data"
TOKEN = "EY-7AoVga8YlHwtphYvVWOEiwZmq7BABTGXeOrU-GxnZRA2TOWwMBRj2oWGz29kYyYpLHOUMYBuNMQShVF0Hkg=="
URL = f"https://eu-central-1-1.aws.cloud2.influxdata.com/api/v2/write?org={ORG}&bucket={BUCKET}&precision=s"

# 🔌 RS485-instellingen (omvormer)
SERIAL_PORT = "/dev/ttyS0"
BAUDRATE = 9600
TIMEOUT = 1

# 📡 4G-modem instellingen
MODEM_PORT = "/dev/ttyUSB2"
MODEM_BAUDRATE = 115200

# 📊 Metingen
measurement_names = [
    "IDX_AVG_VIN2", "IDX_AVG_IDC", "IDX_AVG_VPH3", "IDX_AVG_VPH2", "IDX_AVG_VPH1",
    "IDX_AVG_IPH3", "IDX_AVG_IPH2", "IDX_AVG_IPH1", "IDX_INV_REG", "IDX_AVG_VBRIDGE1",
    "IDX_AVG_VBRIDGE2", "BYTE_11", "BYTE_12", "BYTE_13", "BYTE_14", "BYTE_15",
    "IDX_AVG_TMP_CONV", "IDX_AVG_TMP_INV", "IDX_AVG_TMP_TRAFO", "IDX_AVG_TMP_ROOM1",
    "IDX_AVG_TMP_ROOM2", "IDX_AVG_TMP_LPF1", "IDX_AVG_TMP_LPF2",
    "IDX_STATUS0", "IDX_STATUS1", "IDX_STATUS2", "IDX_STATUS3", "IDX_STATUS4",
    "IDX_GPIO_OUT", "IDX_GPIO_IN", "IDX_STATUS", "IDX_ERROR"
]

# 🔁 Initieer 4G-modem met AT-commando's
def init_modem():
    while True:
        try:
            ser = serial.Serial(MODEM_PORT, baudrate=MODEM_BAUDRATE, timeout=1)
            print("📶 4G-modem verbonden. Verstuur AT-commando's...")
            ser.write(b'AT+CPIN?\r\n')
            time.sleep(1)
            ser.write(b'AT+CPIN=2713\r\n')  # ⚠️ PIN-code indien vereist
            time.sleep(1)
            ser.close()
            break
        except serial.SerialException:
            print("📡 4G-modem niet gevonden. Opnieuw proberen in 3 seconden...")
            time.sleep(3)

# 📄 Format helpers
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

# ⬆️ Stuur data naar InfluxDB
def send_to_influx(vals, timestamp):
    lines = []
    for i, val in enumerate(vals):
        measurement = measurement_names[i] if i < len(measurement_names) else f"BYTE_{i}"
        lines.append(f"{measurement} value={val} {timestamp}")
    lines.append(f"RPi_ON value=1 {timestamp}")
    payload = "\\n".join(lines)

    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "text/plain; charset=utf-8"
    }

    while True:
        try:
            resp = requests.post(URL, headers=headers, data=payload)
            if resp.status_code == 204:
                print(f"✅ Data verzonden naar InfluxDB @ {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}")
                break
            else:
                print(f"⚠️ Fout bij InfluxDB: {resp.status_code} {resp.text}. Proberen opnieuw in 3s...")
        except Exception as e:
            print(f"❌ Verbindingsfout met InfluxDB: {e}. Proberen opnieuw in 3s...")
        time.sleep(3)

# 📟 RS485-poort openen met retries
def open_serial():
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, baudrate=BAUDRATE, timeout=TIMEOUT)
            print("🔌 Verbonden met omvormer via RS485.")
            return ser
        except Exception as e:
            print(f"⚠️ Kan RS485-poort niet openen: {e}")
            print("🔁 Opnieuw proberen in 3 seconden...")
            time.sleep(3)

# 🚀 Main loop
def main():
    init_modem()
    ser = open_serial()

    while True:
        try:
            raw = ser.read(64)
            if len(raw) != 64:
                print("⚠️ Data niet beschikbaar of onvolledig.")
                time.sleep(3)
                continue

            values = []
            for i in range(0, 64, 2):
                val = (raw[i] << 8) + raw[i + 1]
                values.append(val)

            print("\\n📥 Ontvangen data:")
            print_values(values)

            ts = int(time.time())
            send_to_influx(values, ts)

        except serial.SerialException as e:
            print(f"🚫 Serial fout: {e}")
            ser.close()
            ser = open_serial()

        except Exception as e:
            print(f"❌ Onbekende fout: {e}")
            time.sleep(3)

        time.sleep(6)

if __name__ == "__main__":
    main()
