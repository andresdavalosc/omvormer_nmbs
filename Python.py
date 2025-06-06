import serial
import time
import requests

# InfluxDB configuratie
INFLUX_URL = "https://eu-central-1-1.aws.cloud2.influxdata.com/api/v2/write"
ORG = "WIE"
BUCKET = "demo_data"   # <-- aangepaste bucketnaam
TOKEN = "qERdzyL-L614vuyteUK8ZviPFRS69Ja4mkj_tkVI5UyBXgXCWMvN3Xpjp8YrJPJ8XofYiLDh6ghuTbMuiy1qXQ=="

measurement_names = [
    "AVG_VIN2", "AVG_IDC", "AVG_VPH3", "AVG_VPH2", "AVG_VPH1",
    "AVG_IPH3", "AVG_IPH2", "AVG_IPH1", "INV_REG", "AVG_VBRIDGE1",
    "AVG_VBRIDGE2", "UNUSED_1", "UNUSED_2", "UNUSED_3", "UNUSED_4",
    "UNUSED_5", "AVG_TMP_CONV", "AVG_TMP_INV", "AVG_TMP_TRAFO",
    "AVG_TMP_ROOM1", "AVG_TMP_ROOM2", "AVG_TMP_LPF1", "AVG_TMP_LPF2",
    "STATUS0", "STATUS1", "STATUS2", "STATUS3", "STATUS4",
    "GPIO_OUT", "GPIO_IN", "STATUS", "ERROR"
]

ser = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=1)

def send_to_influx(pairs):
    timestamp = int(time.time())
    lines = []

    for name, val in pairs.items():
        lines.append(f'omvormer,name={name} value={val} {timestamp}')

    full_hex = ''.join(f"{(val >> 8) & 0xFF:02X}{val & 0xFF:02X}" for val in pairs.values())
    lines.append(f'omvormer,name=full_hex value="{full_hex}" {timestamp}')

    payload = "\n".join(lines)
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "text/plain; charset=utf-8"
    }

    response = requests.post(
        f"{INFLUX_URL}?org={ORG}&bucket={BUCKET}&precision=s",
        headers=headers,
        data=payload
    )

    if response.status_code != 204:
        print(f"⚠️ Fout bij versturen: {response.status_code} → {response.text}")
    else:
        print(f"✅ Data verstuurd @ {timestamp}")

while True:
    raw = ser.read(64)
    if len(raw) == 64:
        pairs = {}
        for i in range(32):
            hi = raw[i*2]
            lo = raw[i*2 + 1]
            val = (hi << 8) + lo
            pairs[measurement_names[i]] = val
        send_to_influx(pairs)
    else:
        print("⏳ Wacht op volledige 64-byte frame...")

    time.sleep(5)
