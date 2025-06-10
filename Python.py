import serial
import time
import requests

# Config InfluxDB
ORG = "WIE"
BUCKET = "demo_data"
TOKEN = "EY-7AoVga8YlHwtphYvVWOEiwZmq7BABTGXeOrU-GxnZRA2TOWwMBRj2oWGz29kYyYpLHOUMYBuNMQShVF0Hkg=="
URL = f"https://eu-central-1-1.aws.cloud2.influxdata.com/api/v2/write?org={ORG}&bucket={BUCKET}&precision=s"

# Serial poort config
SERIAL_PORT = "/dev/ttyS0"
BAUDRATE = 9600
TIMEOUT = 1

# 32 metingen, elk 2 bytes = 16 bit unsigned int
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
    
    # Voeg RPi_ON toe met waarde 1 (RPi aan)
    lines.append(f"RPi_ON value=1 {timestamp}")
    
    payload = "\n".join(lines)
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "text/plain; charset=utf-8"
    }
    resp = requests.post(URL, headers=headers, data=payload)
    if resp.status_code != 204:
        print(f"⚠️ Fout bij InfluxDB schrijven: {resp.status_code} {resp.text}")
    else:
        print(f"✅ Data verstuurd naar InfluxDB @ {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}")

def main():
    ser = serial.Serial(SERIAL_PORT, baudrate=BAUDRATE, timeout=TIMEOUT)
    print("🔌 Serial verbinding geopend, wacht op data...")
    while True:
        raw = ser.read(64)
        if len(raw) == 64:
            # Parse 32 x 2-byte unsigned integers (big endian)
            values = []
            for i in range(0, 64, 2):
                val = (raw[i] << 8) + raw[i+1]
                values.append(val)

            print("\n📥 Nieuwe data ontvangen:")
            print_values(values)

            ts = int(time.time())
            send_to_influx(values, ts)
        else:
            print("⏳ Wacht op volledige 64 bytes frame...")

        time.sleep(5)

if __name__ == "__main__":
    main()
