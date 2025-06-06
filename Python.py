import serial
import time
import requests

# InfluxDB instellingen
ORG = "WIE"
BUCKET = "demo_data"
TOKEN = "oP5zoJmaCWPtz-DNZItqQO8V8DMdprtYLCT-63u0rEUQXOsnSdZ3veArE8HkIhg2yOw9-WETxhuZ8gYQtNq6nA=="
URL = f"https://eu-central-1-1.aws.cloud2.influxdata.com/api/v2/write?org={ORG}&bucket={BUCKET}&precision=s"

headers = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "text/plain; charset=utf-8"
}

# RS485 labels (32 velden van elk 2 bytes)
byte_labels = {
    0: "IDX_AVG_VIN2",
    2: "IDX_AVG_IDC",
    4: "IDX_AVG_VPH3",
    6: "IDX_AVG_VPH2",
    8: "IDX_AVG_VPH1",
    10: "IDX_AVG_IPH3",
    12: "IDX_AVG_IPH2",
    14: "IDX_AVG_IPH1",
    16: "IDX_INV_REG",
    18: "IDX_AVG_VBRIDGE1",
    20: "IDX_AVG_VBRIDGE2",
    22: "IDX_AVG_TMP_CONV",
    24: "IDX_AVG_TMP_INV",
    26: "IDX_AVG_TMP_TRAFO",
    28: "IDX_AVG_TMP_ROOM1",
    30: "IDX_AVG_TMP_ROOM2",
    32: "IDX_AVG_TMP_LPF1",
    34: "IDX_AVG_TMP_LPF2",
    36: "IDX_STATUS0",
    38: "IDX_STATUS1",
    40: "IDX_STATUS2",
    42: "IDX_STATUS3",
    44: "IDX_STATUS4",
    46: "IDX_GPIO_OUT",
    48: "IDX_GPIO_IN",
    50: "IDX_STATUS",
    52: "IDX_ERROR",
    54: "BYTE_27",
    56: "BYTE_28",
    58: "BYTE_29",
    60: "BYTE_30",
    62: "BYTE_31"
}

# Seriële poort instellen
ser = serial.Serial(
    port='/dev/ttyS0',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

print("Wachten op 64 bytes van de RS485...")

while True:
    if ser.in_waiting >= 64:
        raw_data = ser.read(64)
        if len(raw_data) < 64:
            print(f"⚠️ Slechts {len(raw_data)} bytes ontvangen.")
            continue

        print("\n📥 64 bytes ontvangen:")
        influx_lines = []

        for i in range(0, 64, 2):
            label = byte_labels.get(i, f"BYTE_{i:02}")
            msb = raw_data[i]
            lsb = raw_data[i+1]
            value = (msb << 8) | lsb  # MSB first

            # Voor debug
            bin_string = f"{value:016b}"
            hex_string = f"0x{value:04X}"
            print(f"{label:<20}: {bin_string}   {value:5d}   {hex_string}")

            # Influx line protocol
            influx_lines.append(f"{label} value={value}")

        # Combineer alle regels en stuur naar InfluxDB
        payload = "\n".join(influx_lines)
        response = requests.post(URL, headers=headers, data=payload)

        if response.status_code == 204:
            print("✅ Data succesvol naar InfluxDB verzonden.")
        else:
            print(f"❌ Fout bij verzenden naar InfluxDB: {response.status_code}")
            print(response.text)

        print("-" * 50)
        time.sleep(2)
