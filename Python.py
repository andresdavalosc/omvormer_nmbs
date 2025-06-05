import serial
import time

# Seriële poort setup
ser = serial.Serial(
    port='/dev/ttyS0',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

# Indexen en namen
byte_labels = {
    0: "IDX_AVG_VIN2",
    1: "IDX_AVG_IDC",
    2: "IDX_AVG_VPH3",
    3: "IDX_AVG_VPH2",
    4: "IDX_AVG_VPH1",
    5: "IDX_AVG_IPH3",
    6: "IDX_AVG_IPH2",
    7: "IDX_AVG_IPH1",
    8: "IDX_INV_REG",
    9: "IDX_AVG_VBRIDGE1",
    10: "IDX_AVG_VBRIDGE2",
    16: "IDX_AVG_TMP_CONV",
    17: "IDX_AVG_TMP_INV",
    18: "IDX_AVG_TMP_TRAFO",
    19: "IDX_AVG_TMP_ROOM1",
    20: "IDX_AVG_TMP_ROOM2",
    21: "IDX_AVG_TMP_LPF1",
    22: "IDX_AVG_TMP_LPF2",
    23: "IDX_STATUS0",
    24: "IDX_STATUS1",
    25: "IDX_STATUS2",
    26: "IDX_STATUS3",
    27: "IDX_STATUS4",
    28: "IDX_GPIO_OUT",
    29: "IDX_GPIO_IN",
    30: "IDX_STATUS",
    31: "IDX_ERROR"
}

print("Wachten op 64 bytes van de RS485...")

while True:
    if ser.in_waiting >= 64:
        ser.flushInput()
        raw_data = ser.read(64)

        print("\n📥 64 bytes ontvangen:")
        for idx, byte in enumerate(raw_data):
            label = byte_labels.get(idx, f"BYTE_{idx:02}")
            bit_string = f"{byte:08b}"         # binair
            dec_value = f"{byte:3d}"           # decimaal
            hex_value = f"0x{byte:02X}"         # hexadecimaal
            print(f"{label:<20}: {bit_string}   {dec_value}   {hex_value}")

        print("-" * 50)
        time.sleep(0.5)
