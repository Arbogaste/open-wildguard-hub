/*
 * WildGuard M3 — Acoustic listening node (ESP32 + I2S MEMS mic). SCAFFOLD.
 *
 * Logic: continuously sample the mic via I2S -> compute short-window energy -> when energy
 * crosses an adaptive threshold (candidate gunshot/chainsaw), record a GPS-synced timestamp and
 * a short clip -> send {node_id, timestamp, peak} over LoRa to the hub. Three+ such nodes feed
 * tdoa_locate.py to triangulate the source.
 *
 * Hardware (~$10/node):
 *   - ESP32 dev board
 *   - INMP441 I2S MEMS mic (SCK=GPIO14, WS=GPIO15, SD=GPIO32)
 *   - GPS module (for sub-ms time sync via PPS) -> critical for TDoA
 *   - SX1276 LoRa module for backhaul
 *
 * TODO before field use:
 *   - Replace energy gate with the TFLite classifier from train_audio_classifier.py (gunshot vs
 *     chainsaw vs ambient) to cut false positives.
 *   - Discipline the clock with GPS PPS so cross-node timestamps are comparable to <1 ms.
 *   - Add LoRa send of the event struct.
 */
#include <driver/i2s.h>

#define I2S_WS  15
#define I2S_SCK 14
#define I2S_SD  32
#define I2S_PORT I2S_NUM_0
#define SAMPLE_RATE 16000
#define BUF_LEN 1024

const char* NODE_ID = "audio_node_1";
float noiseFloor = 0.0;           // adaptive baseline
const float TRIGGER_MULT = 6.0;   // event if window energy > TRIGGER_MULT * noiseFloor

void initI2S() {
  i2s_config_t cfg = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4, .dma_buf_len = BUF_LEN,
    .use_apll = false
  };
  i2s_pin_config_t pins = { .bck_io_num = I2S_SCK, .ws_io_num = I2S_WS,
                            .data_out_num = I2S_PIN_NO_CHANGE, .data_in_num = I2S_SD };
  i2s_driver_install(I2S_PORT, &cfg, 0, NULL);
  i2s_set_pin(I2S_PORT, &pins);
}

float windowEnergy() {
  int32_t buf[BUF_LEN]; size_t n = 0;
  i2s_read(I2S_PORT, buf, sizeof(buf), &n, portMAX_DELAY);
  double acc = 0; int cnt = n / 4;
  for (int i = 0; i < cnt; i++) { float s = buf[i] / 2147483648.0f; acc += s * s; }
  return cnt ? sqrt(acc / cnt) : 0.0f;
}

void onEvent(float peak) {
  // TODO: read GPS-disciplined timestamp; classify with TFLite; LoRa-send {NODE_ID, ts, peak}.
  uint32_t ts = millis();   // placeholder — replace with GPS time for real TDoA
  Serial.printf("{\"node\":\"%s\",\"t_ms\":%lu,\"peak\":%.4f}\n", NODE_ID, ts, peak);
}

void setup() { Serial.begin(115200); initI2S(); }

void loop() {
  float e = windowEnergy();
  noiseFloor = (noiseFloor == 0.0) ? e : (0.99 * noiseFloor + 0.01 * e);  // slow adapt
  if (e > TRIGGER_MULT * noiseFloor && noiseFloor > 0) onEvent(e);
}
