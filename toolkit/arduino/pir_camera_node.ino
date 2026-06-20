/*
 * WildGuard M2 — PIR-triggered camera node (ESP32-CAM).
 *
 * Logic: deep-sleep to save battery -> PIR motion wakes the board -> capture a JPEG ->
 * save to SD with timestamp -> (store-and-forward) try Wi-Fi upload, else keep on SD ->
 * back to deep-sleep. Built for off-grid trails with intermittent or no connectivity.
 *
 * Hardware (Essential/Intermediate tier, ~$12):
 *   - AI-Thinker ESP32-CAM
 *   - PIR HC-SR501 OUT -> GPIO13 (wake), VCC 5V, GND
 *   - MicroSD card (FAT32)
 *   - 18650 Li-ion + TP4056 + small solar panel
 *   - Bark-camo 3D-printed enclosure
 *
 * Wiring note: ESP32-CAM uses GPIO0/1/3 for flashing; keep PIR on RTC-capable GPIO (e.g. 13).
 *
 * This is field firmware scaffold. Set WIFI creds + UPLOAD_URL for your deployment. Upload via
 * Arduino IDE (board "AI Thinker ESP32-CAM") or PlatformIO.
 */
#include "esp_camera.h"
#include "FS.h"
#include "SD_MMC.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_sleep.h"
#include <time.h>

#define PIR_WAKE_GPIO 13

const char* WIFI_SSID = "";          // leave empty for SD-only store-and-forward
const char* WIFI_PASS = "";
const char* UPLOAD_URL = "";          // e.g. http://hub.local:8080/ingest  (optional)
const char* NODE_ID    = "node_edge_42";

// --- AI-Thinker ESP32-CAM pin map ---
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27
#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

bool initCamera() {
  camera_config_t c;
  c.ledc_channel = LEDC_CHANNEL_0; c.ledc_timer = LEDC_TIMER_0;
  c.pin_d0 = Y2_GPIO_NUM; c.pin_d1 = Y3_GPIO_NUM; c.pin_d2 = Y4_GPIO_NUM; c.pin_d3 = Y5_GPIO_NUM;
  c.pin_d4 = Y6_GPIO_NUM; c.pin_d5 = Y7_GPIO_NUM; c.pin_d6 = Y8_GPIO_NUM; c.pin_d7 = Y9_GPIO_NUM;
  c.pin_xclk = XCLK_GPIO_NUM; c.pin_pclk = PCLK_GPIO_NUM; c.pin_vsync = VSYNC_GPIO_NUM;
  c.pin_href = HREF_GPIO_NUM; c.pin_sscb_sda = SIOD_GPIO_NUM; c.pin_sscb_scl = SIOC_GPIO_NUM;
  c.pin_pwdn = PWDN_GPIO_NUM; c.pin_reset = RESET_GPIO_NUM;
  c.xclk_freq_hz = 20000000; c.pixel_format = PIXFORMAT_JPEG;
  c.frame_size = FRAMESIZE_SVGA; c.jpeg_quality = 12; c.fb_count = 1;
  return esp_camera_init(&c) == ESP_OK;
}

void tryUpload(const String& path) {
  if (strlen(WIFI_SSID) == 0 || strlen(UPLOAD_URL) == 0) return;  // SD-only mode
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  for (int i = 0; i < 20 && WiFi.status() != WL_CONNECTED; i++) delay(250);
  if (WiFi.status() != WL_CONNECTED) return;  // keep on SD, forward later
  File f = SD_MMC.open(path); if (!f) return;
  HTTPClient http; http.begin(UPLOAD_URL);
  http.addHeader("X-Node-Id", NODE_ID);
  http.addHeader("Content-Type", "image/jpeg");
  http.sendRequest("POST", &f, f.size());
  http.end(); f.close();
}

void captureAndStore() {
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) return;
  String path = "/" + String(NODE_ID) + "_" + String((uint32_t)time(nullptr)) + ".jpg";
  File file = SD_MMC.open(path, FILE_WRITE);
  if (file) { file.write(fb->buf, fb->len); file.close(); }
  esp_camera_fb_return(fb);
  tryUpload(path);
}

void setup() {
  Serial.begin(115200);
  if (!initCamera()) { Serial.println("camera init failed"); }
  if (!SD_MMC.begin()) { Serial.println("SD init failed"); }

  esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
  if (cause == ESP_SLEEP_WAKEUP_EXT0) {   // woke from PIR
    captureAndStore();
  }

  // Arm PIR as wake source, then deep-sleep (microamps).
  esp_sleep_enable_ext0_wakeup((gpio_num_t)PIR_WAKE_GPIO, 1);
  Serial.println("sleeping; PIR armed");
  esp_deep_sleep_start();
}

void loop() {}  // never runs; everything is in setup() + deep-sleep
