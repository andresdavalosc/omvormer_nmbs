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

# 32 namen voor elk 16-bits waarde (2 bytes per label)
word_labels = {
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
    11: "BYTE_11",
    12: "BYTE_12",
    13: "BYTE_13",
    14: "BYTE_14",
    15: "BYTE_15",
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
        raw_data = ser.read(64)
        if len(raw_data) < 64:
            print(f"⚠️ Slechts {len(raw_data)} bytes ontvangen.")
            continue

        print("\n📥 64 bytes ontvangen:")
        for i in range(0, 64, 2):
            index = i // 2
            label = word_labels.get(index, f"WORD_{index:02}")

            msb = raw_data[i]
            lsb = raw_data[i + 1]
            value = (msb << 8) | lsb  # MSB first

            bin_str = f"{value:016b}"
            dec_str = f"{value:5d}"
            hex_str = f"0x{value:04X}"

            print(f"{label:<20}: {bin_str}   {dec_str}   {hex_str}")

        print("-" * 60)
        time.sleep(0.5)
