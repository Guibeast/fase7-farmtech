/*
 * FarmTech Solutions - Fase 2 (ESP32)
 * Estacao de monitoramento agricola com acionamento automatico da bomba.
 *
 * Sensores:
 *   - DHT22  : temperatura e umidade
 *   - LDR    : luminosidade usada como proxy do pH do solo (4.5 a 8.5)
 *   - Pot.   : nivel de nitrogenio N (40 a 300 ppm)
 *   - Botoes : presenca de fosforo (P) e potassio (K)
 * Atuador:
 *   - Rele   : bomba de irrigacao
 *
 * Logica da bomba (identica a src/fase2_iot.py -> deve_ligar_bomba):
 *   liga se umidade < 40%  OU  (N < 80 ppm E pH fora da faixa 5.5-7.5)
 *
 * O dashboard Streamlit da Fase 7 simula esta mesma logica em Python.
 */
#include <DHT.h>

#define DHTPIN    4
#define DHTTYPE   DHT22
#define LDR_PIN   34   // ADC1 - pH proxy
#define POT_N_PIN 35   // ADC1 - nivel de nitrogenio
#define BTN_P_PIN 18   // fosforo
#define BTN_K_PIN 19   // potassio
#define RELE_PIN  23   // bomba

// Thresholds (espelham THRESHOLDS em fase2_iot.py)
const float PH_MIN      = 5.5;
const float PH_MAX      = 7.5;
const float UMIDADE_MIN = 40.0;
const float N_MIN       = 80.0;

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  dht.begin();
  pinMode(BTN_P_PIN, INPUT_PULLUP);
  pinMode(BTN_K_PIN, INPUT_PULLUP);
  pinMode(RELE_PIN, OUTPUT);
  digitalWrite(RELE_PIN, LOW);
}

float lerPh() {
  int leitura = analogRead(LDR_PIN);            // 0 - 4095
  return 4.5 + (leitura / 4095.0) * (8.5 - 4.5);
}

float lerNitrogenio() {
  int leitura = analogRead(POT_N_PIN);          // 0 - 4095
  return 40.0 + (leitura / 4095.0) * (300.0 - 40.0);
}

bool deveLigarBomba(float umidade, float ph, float nivelN) {
  bool umidadeCritica = umidade < UMIDADE_MIN;
  bool phFora = ph < PH_MIN || ph > PH_MAX;
  bool nBaixo = nivelN < N_MIN;
  return umidadeCritica || (nBaixo && phFora);
}

void loop() {
  float umidade = dht.readHumidity();
  float temperatura = dht.readTemperature();
  float ph = lerPh();
  float nivelN = lerNitrogenio();
  bool nivelP = digitalRead(BTN_P_PIN) == LOW;
  bool nivelK = digitalRead(BTN_K_PIN) == LOW;

  if (isnan(umidade) || isnan(temperatura)) {
    Serial.println("Falha na leitura do DHT22");
    delay(2000);
    return;
  }

  bool bomba = deveLigarBomba(umidade, ph, nivelN);
  digitalWrite(RELE_PIN, bomba ? HIGH : LOW);

  // Formato amigavel ao Serial Plotter
  Serial.print("Umidade:");     Serial.print(umidade);
  Serial.print(" Temp:");       Serial.print(temperatura);
  Serial.print(" pH:");         Serial.print(ph);
  Serial.print(" N:");          Serial.print(nivelN);
  Serial.print(" P:");          Serial.print(nivelP);
  Serial.print(" K:");          Serial.print(nivelK);
  Serial.print(" Bomba:");      Serial.println(bomba);

  delay(2000);
}
