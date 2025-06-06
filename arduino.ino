#include <SoftwareSerial.h>
 
#define RS485_TX 9              // Arduino pin connected to MAX485 DI
#define RS485_RX 8              // Arduino pin connected to MAX485 RO
#define RS485_CONTROL_PIN 10    // Arduino pin connected to MAX485 DE and RE (tied together)
 
// Create RS485 serial object
SoftwareSerial rs485(RS485_RX, RS485_TX);  // RX, TX
 
uint8_t txBuffer[64];  // 64-byte buffer
 
void setup() {
  // Initialize pins
  pinMode(RS485_CONTROL_PIN, OUTPUT);
  pinMode(RS485_RX, INPUT_PULLUP);
  digitalWrite(RS485_CONTROL_PIN, LOW); // Start in receive mode
 
  // Start serials
  Serial.begin(9600);      // USB serial for debug
  rs485.begin(9600);       // RS485 serial
 
  // Fill buffer with example data
  for (uint8_t i = 0; i < 64; i++) {
    txBuffer[i] = i;
  }
 
  Serial.println("RS485 Ready to send 64 bytes every 5s.");
}
 
void loop() {
  // Enable transmit mode
  digitalWrite(RS485_CONTROL_PIN, HIGH);
  delay(1);  // Stabilize before sending
 
  // Ingangspanning -->3000V
  txBuffer[0] = 0x0B;  
  txBuffer[1] = 0xB8;
 
  // ingangstroom --> 10A
  txBuffer[2] = 0x00;
  txBuffer[3] = 0x10;
 
  // Lijn spanningen --> 400V
  txBuffer[4] = 0x01;
  txBuffer[5] = 0x90;
 
  txBuffer[6] = 0x01;
  txBuffer[7] = 0x90;
 
  txBuffer[8] = 0x01;
  txBuffer[9] = 0x90;
 
  // Lijn stromen --> 100A
  txBuffer[10] = 0x00;
  txBuffer[11] = 0x64;
 
  txBuffer[12] = 0x00;
  txBuffer[13] = 0x64;
 
  txBuffer[14] = 0x00;
  txBuffer[15] = 0x64;

  // Fill the rest of the buffer with 1,2,3,... up to 48 bytes (indices 16 to 63)
  for (uint8_t i = 16; i < 64; i++) {
    txBuffer[i] = i - 15;  // Starts at 1 for index 16
  }
 
  // Send the 64-byte buffer
  rs485.write(txBuffer, 64);
  rs485.flush();          // Wait for all data to send
 
  // Back to receive mode
  digitalWrite(RS485_CONTROL_PIN, LOW);
 
  // Optional debug
  Serial.println("Sent 64 bytes over RS485.");
 
  delay(5000); // Wait 5 seconds before next send
}
