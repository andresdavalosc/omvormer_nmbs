import serial
import struct
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

# InfluxDB config
INFLUX_URL = "https://eu-central-1-1.aws.cloud2.influxdata.com"
INFLUX_TOKEN = "2hMjwsBQ8KZFOJhswwCkY3y4sGWyiJLpZSMWNgO07MJ-pU5sljMBLqsLKZM8WQVrfYizasKpNtZHUJ1I-nq9tA=="
INFLUX_ORG = "WIE"
INFLUX_BUCKET = "omvormer_bucket"

# Seriële poort config
SERIAL_PORT = "/dev/ttyS0"
BAUD_RATE = 9600

# Mapping: index (start byte) → naam
measurement_map = {
    0: "AVG_VIN2",
    2: "AVG_IDC",
    4: "AVG_VPH3",
    6: "AVG_VPH2",
    8: "AVG_VPH1",
    10: "AVG_IPH3",
    12: "AVG_IPH2",
    14: "AVG_IPH1",
    16: "INV_REG",
    18: "AVG_VBRIDGE1",
    20: "AVG_VBRIDGE2",
    22: "AVG_TMP_CONV",
    24: "AVG_TMP_INV",
    26: "AVG_TMP_TRAFO",
    28: "AVG_TMP_ROOM1",
    30: "AVG_TMP_ROOM2",
    32: "AVG_TMP_LPF1",
    34: "AVG_TMP_LPF2",
    36: "STATUS0",
    38: "STATUS1",
    40: "STATUS2",
    42: "STATUS3",
    44: "STATUS4",
    46: "GPIO_OUT",
    48: "GPIO_IN",
    50: "STATUS",
    52: "ERROR",
    54: "BYTE_27",
    56: "BYTE_28",
    58: "BYTE_29",
    60: "BYTE_30",
    62: "BYTE_31"
}

# Connectie met InfluxDB
client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Open seriële poort
ser = serial.Serial(SERIAL_PORT, BAUD_RATE)

def parse_bytes(data_bytes):
    parsed = {}
    for i in range(0, 64, 2):
        name = measurement_map.get(i, f"BYTE_{i}")
        value = struct.unpack('>H', data_bytes[i:i+2])[0]  # big-endian 2 bytes
        parsed[name] = value
    return parsed

def send_to_influx(parsed_data):
    timestamp = datetime.utcnow()
    for name, value in parsed_data.items():
        point = Point(name).field("value", value).time(timestamp)
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

print("🟢 Luisteren op seriële poort...")

while True:
    if ser.in_waiting >= 64:
        raw_data = ser.read(64)
        parsed = parse_bytes(raw_data)
        send_to_influx(parsed)
        print(f"[{datetime.now()}] ✅ Gegevens verzonden naar InfluxDB: {parsed}")
