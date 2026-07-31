/*
 * Transmisor LoRa - Simulación de sensores de Paca Digestora
 * ESP32 + módulo LoRa transparente UART (ej. EBYTE E32-433T30D o similar)
 *
 * Envía cada 5 segundos un JSON con:
 *   t_int  -> temperatura interna de la paca (°C)
 *   t_ext  -> temperatura externa/ambiente (°C)
 *   h_int  -> humedad interna de la paca (%)
 *   h_ext  -> humedad externa/ambiente (%)
 *   estado -> NORMAL / OPTIMO / ALERTA_TEMP / ALERTA_HUMEDAD
 *
 * Librería requerida (Arduino Library Manager):
 *   - ArduinoJson (por Benoit Blanchon)
 *
 * CONEXIÓN (ajustar según tu módulo LoRa):
 *   ESP32 GPIO16 (RX2) <- TX del módulo LoRa
 *   ESP32 GPIO17 (TX2) -> RX del módulo LoRa
 *   Módulo LoRa VCC/GND según su datasheet (3.3V o 5V)
 */

#include <HardwareSerial.h>
#include <ArduinoJson.h>

HardwareSerial LoRaSerial(2);  // UART2

// --- Pines UART hacia el módulo LoRa (ajustar si tu wiring es distinto) ---
const int PIN_RX2 = 16;
const int PIN_TX2 = 17;
const int M0 = 18;
const int M1 = 5;


// --- Estado simulado de los sensores (arrancan en valores "normales") ---
float temp_int = 35.0;
float temp_ext = 28.0;
float hum_int  = 65.0;
float hum_ext  = 50.0;

const unsigned long INTERVALO_ENVIO_MS = 1000;
unsigned long ultimoEnvio = 0;

// Camina aleatoriamente el valor dentro de un rango, con paso máximo controlado
// (simula variación real de sensores en vez de saltos bruscos)
float randomWalk(float valor, float min_v, float max_v, float paso_max) {
  float delta = random(-100, 101) / 100.0 * paso_max;
  valor += delta;
  if (valor < min_v) valor = min_v;
  if (valor > max_v) valor = max_v;
  return valor;
}

// Lógica simple de estado (esto luego lo reemplazas por tu red neuronal)
String calcularEstado() {
  if (temp_int > 55.0) return "ALERTA_TEMP";
  if (hum_int < 40.0 || hum_int > 85.0) return "ALERTA_HUMEDAD";
  if (temp_int >= 45.0 && temp_int <= 55.0 && hum_int >= 55.0 && hum_int <= 75.0) {
    return "OPTIMO";
  }
  return "NORMAL";
}

void setup() {
  Serial.begin(115200);
  LoRaSerial.begin(9600, SERIAL_8N1, PIN_RX2, PIN_TX2);
  randomSeed(analogRead(0));
  pinMode(M0, OUTPUT);
  pinMode(M1, OUTPUT);
  digitalWrite(M0, LOW);
  digitalWrite(M1, LOW);
  
  Serial.println("=== Transmisor LoRa - Paca Digestora (simulacion) ===");
  Serial.printf("Enviando cada %lu ms\n", INTERVALO_ENVIO_MS);
  
}

void loop() {
  unsigned long ahora = millis();

  if (ahora - ultimoEnvio >= INTERVALO_ENVIO_MS) {
    ultimoEnvio = ahora;

    // Actualiza valores simulados
    temp_int = randomWalk(temp_int, 20.0, 65.0, 1.5);
    temp_ext = randomWalk(temp_ext, 10.0, 40.0, 1.0);
    hum_int  = randomWalk(hum_int, 30.0, 95.0, 2.0);
    hum_ext  = randomWalk(hum_ext, 20.0, 90.0, 2.0);

    StaticJsonDocument<256> doc;
    doc["t_int"]  = round(temp_int * 10) / 10.0;
    doc["t_ext"]  = round(temp_ext * 10) / 10.0;
    doc["h_int"]  = round(hum_int * 10) / 10.0;
    doc["h_ext"]  = round(hum_ext * 10) / 10.0;
    doc["estado"] = calcularEstado();
    doc["ts"]     = ahora;

    String payload;
    serializeJson(doc, payload);

    LoRaSerial.println(payload);   // esto es lo que recibe la BBB en /dev/ttyS1

    Serial.print("[TX] ");
    Serial.println(payload);
  }
}
