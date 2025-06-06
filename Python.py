import serial
import time
import requests

# InfluxDB configuratie
INFLUX_URL = "https://eu-central-1-1.aws.cloud2.influxdata.com/api/v2/write"
ORG = "WIE"
BUCKET = "omvormer_bucket"
TOKEN = "2hMjwsBQ8KZFOJhswwCkY3y4sGWyiJLpZSMWNgO07MJ-pU5sljMBLqsLKZM8WQVrfYizasKpNtZHUJ1I-nq9tA=="

# 64 byte-namen (aangepast aan jouw schema, rest opgevuld)
byte_names = [
    "AVG_VIN2", "AVG_IDC", "AVG_VPH3", "AVG_VPH2", "AVG_VPH1",
    "AVG_IPH3", "AVG_IPH2", "AVG_IPH1", "INV_REG", "AVG_VBRIDGE1",
    "AVG_VBRIDGE2", "UNUSED_1", "UNUSED_2", "UNUSED_3", "UNUSED_4",
    "UNUSED_5", "AVG_TMP_CONV", "AVG_TMP_INV", "AVG_TMP_TRAFO",
    "AVG_TMP_ROOM1", "AVG_TMP_ROOM2", "AVG_TMP_LPF1", "AVG_TMP_LPF2",
    "STATUS0", "STATUS1", "STATUS2", "STATUS3", "STATUS4",
    "GPIO_OUT", "GPIO_IN", "STATUS", "ERROR"
] + [f"BYTE_{i}" for i in range(32, 64)]

# Seriële poort
ser = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=1)

def send_to_influx(byte_values):
    timestamp = int(time.time())  # UNIX-tijd
    lines = []

    # 1. Elke byte apart versturen met naam
    for i, val in enumerate(byte_values):
        name = byte_names[i] if i < len(byte_names) else f"byte_{i}"
        lines.append(f"omvormer,name={name} value={val} {timestamp}")

    # 2. Volledige hexstring ook versturen
    hex_str = ''.join(f"{byte:02X}" for byte in byte_values)
    lines.append(f'omvormer,name=full_hex hex="{hex_str}" {timestamp}')


    # 3. Versturen naar Influx
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
        print(f"⚠️  Fout bij versturen: {response.status_code} → {response.text}")
    else:
        print(f"✅ {len(byte_values)} bytes & HEX verstuurd @ {timestamp}")

while True:
    raw = ser.read(64)
    if len(raw) == 64:
        byte_values = list(raw)
        send_to_influx(byte_values)
    else:
        print("⏳ Wacht op volledige 64-byte frame...")

    time.sleep(5)
