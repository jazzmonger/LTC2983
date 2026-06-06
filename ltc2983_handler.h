#pragma once
#include "esphome.h"
#include "esphome/core/log.h"
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include <cmath>

static const char *const TAG = "LTC2983";

// DC2213A R6 adjustable RTD simulator + daisy-chained RTD (shared CH2 RSENSE):
//   CH2 = 2 kΩ RSENSE; CH1 return (C1→GND)
//   R6: pins 1+3 → CH2+CH3, wiper pin 2 → CH4, C6→GND
//   External RTD: CH4 → CH5 (daisy chain)
//   K-type TC: TC+ → CH12, TC− → CH13 — assign/read CH13 (pair CH13−CH12)

#define LTC2983_COMMAND_STATUS_REG  0x0000
#define LTC2983_GLOBAL_CONFIG_REG   0x00F0
#define LTC2983_CH_ASSIGN_BASE      0x0200
#define LTC2983_DATA_BASE           0x0010
#define LTC2983_CONVERSION_CONTROL  0x80

#define STATUS_DONE_MASK    0x40
#define STATUS_START_MASK   0x80

#define LTC2983_CS_PIN      GPIO_NUM_2
#define LTC2983_SPI_HOST    SPI2_HOST
#define LTC2983_SPI_CLK     GPIO_NUM_9
#define LTC2983_SPI_MOSI    GPIO_NUM_5
#define LTC2983_SPI_MISO    GPIO_NUM_4

#define CH_RSENSE    2
#define CH_RTD_SIM   4   // R6 wiper; CH3 = pins 1+3 (tied to CH2); also CJC for TC
#define CH_RTD_CHAIN 5   // daisy-chained from CH4
#define CH_TC_K     13   // read CH13: diff pair CH13(−) vs CH12(+) per Figure 4

#define CFG_RSENSE ((uint32_t)0x1D << 27) | 0x001F4000UL
// PT1000 2-wire, 100 µA — daisy chain between adjacent channels
#define CFG_RTD_PT1000 ((uint32_t)0x0F << 27) | ((uint32_t)CH_RSENSE << 22) \
                       | (0x1UL << 18) | (0x5UL << 14)
// Type-K TC, differential CH12/CH13, CJC from CH4, 10 µA OCD
// bits 21:18 = 0100 (LTC2983 Table 14)
#define CFG_TC_K ((uint32_t)0x02 << 27) | ((uint32_t)CH_RTD_SIM << 22) \
                 | (0x1UL << 20)

static spi_device_handle_t ltc2983_spi_device  = nullptr;
static bool ltc2983_initialized                = false;
static bool ltc2983_spi_bus_ready              = false;

static void ltc2983_cs_low()  { gpio_set_level(LTC2983_CS_PIN, 0); }
static void ltc2983_cs_high() { gpio_set_level(LTC2983_CS_PIN, 1); }

static uint8_t ltc2983_spi_transfer(uint8_t data) {
  uint8_t rx = 0;
  spi_transaction_t t = {};
  t.length    = 8;
  t.tx_buffer = &data;
  t.rx_buffer = &rx;
  spi_device_polling_transmit(ltc2983_spi_device, &t);
  return rx;
}

static void write_byte(uint16_t reg, uint8_t data) {
  ltc2983_cs_low();
  ltc2983_spi_transfer(0x02);
  ltc2983_spi_transfer((reg >> 8) & 0xFF);
  ltc2983_spi_transfer( reg       & 0xFF);
  ltc2983_spi_transfer(data);
  ltc2983_cs_high();
}

static void write_dword(uint16_t reg, uint32_t data) {
  ltc2983_cs_low();
  ltc2983_spi_transfer(0x02);
  ltc2983_spi_transfer((reg >> 8) & 0xFF);
  ltc2983_spi_transfer( reg       & 0xFF);
  ltc2983_spi_transfer((data >> 24) & 0xFF);
  ltc2983_spi_transfer((data >> 16) & 0xFF);
  ltc2983_spi_transfer((data >>  8) & 0xFF);
  ltc2983_spi_transfer( data        & 0xFF);
  ltc2983_cs_high();
}

static uint8_t read_byte(uint16_t reg) {
  ltc2983_cs_low();
  ltc2983_spi_transfer(0x03);
  ltc2983_spi_transfer((reg >> 8) & 0xFF);
  ltc2983_spi_transfer( reg       & 0xFF);
  uint8_t val = ltc2983_spi_transfer(0x00);
  ltc2983_cs_high();
  return val;
}

static uint32_t read_dword(uint16_t reg) {
  ltc2983_cs_low();
  ltc2983_spi_transfer(0x03);
  ltc2983_spi_transfer((reg >> 8) & 0xFF);
  ltc2983_spi_transfer( reg       & 0xFF);
  uint32_t val = 0;
  val |= ((uint32_t)ltc2983_spi_transfer(0x00)) << 24;
  val |= ((uint32_t)ltc2983_spi_transfer(0x00)) << 16;
  val |= ((uint32_t)ltc2983_spi_transfer(0x00)) <<  8;
  val |= ((uint32_t)ltc2983_spi_transfer(0x00));
  ltc2983_cs_high();
  return val;
}

static inline uint16_t ch_assign_addr(uint8_t ch) {
  return LTC2983_CH_ASSIGN_BASE + (uint16_t)(ch - 1) * 4;
}

static inline uint16_t ch_data_addr(uint8_t ch) {
  return LTC2983_DATA_BASE + (uint16_t)(ch - 1) * 4;
}

static bool initialize_ltc2983() {
  if (ltc2983_initialized) return true;

  gpio_config_t cs_cfg = {};
  cs_cfg.pin_bit_mask  = (1ULL << LTC2983_CS_PIN);
  cs_cfg.mode          = GPIO_MODE_OUTPUT;
  cs_cfg.pull_up_en    = GPIO_PULLUP_DISABLE;
  cs_cfg.pull_down_en  = GPIO_PULLDOWN_DISABLE;
  cs_cfg.intr_type     = GPIO_INTR_DISABLE;
  gpio_config(&cs_cfg);
  ltc2983_cs_high();

  if (!ltc2983_spi_bus_ready) {
    spi_bus_config_t bus = {};
    bus.mosi_io_num   = LTC2983_SPI_MOSI;
    bus.miso_io_num   = LTC2983_SPI_MISO;
    bus.sclk_io_num   = LTC2983_SPI_CLK;
    bus.quadwp_io_num = -1;
    bus.quadhd_io_num = -1;
    bus.max_transfer_sz = 32;
    esp_err_t err = spi_bus_initialize(LTC2983_SPI_HOST, &bus, SPI_DMA_DISABLED);
    if (err != ESP_OK && err != ESP_ERR_INVALID_STATE) {
      ESP_LOGE(TAG, "SPI bus init failed: %s", esp_err_to_name(err));
      return false;
    }
    ltc2983_spi_bus_ready = true;
    ESP_LOGI(TAG, "SPI bus ready (CLK=%d MOSI=%d MISO=%d CS=%d)",
             LTC2983_SPI_CLK, LTC2983_SPI_MOSI, LTC2983_SPI_MISO, LTC2983_CS_PIN);
  }

  if (ltc2983_spi_device == nullptr) {
    spi_device_interface_config_t dev = {};
    dev.clock_speed_hz = 1000000;
    dev.mode           = 0;
    dev.spics_io_num   = -1;
    dev.queue_size     = 1;
    esp_err_t err = spi_bus_add_device(LTC2983_SPI_HOST, &dev, &ltc2983_spi_device);
    if (err != ESP_OK) {
      ESP_LOGE(TAG, "SPI device add failed: %s", esp_err_to_name(err));
      return false;
    }
    ESP_LOGI(TAG, "SPI device added");
  }

  uint32_t tries = 0;
  while (true) {
    uint8_t st = read_byte(LTC2983_COMMAND_STATUS_REG);
    if ((st & STATUS_START_MASK) == 0 && (st & STATUS_DONE_MASK) != 0) {
      ESP_LOGI(TAG, "Chip ready (status=0x%02x)", st);
      break;
    }
    delay(10);
    if (++tries > 300) {
      ESP_LOGE(TAG, "Chip not ready — status=0x%02x", st);
      return false;
    }
  }

  write_dword(ch_assign_addr(CH_RSENSE), CFG_RSENSE);
  write_dword(ch_assign_addr(CH_RTD_SIM), CFG_RTD_PT1000);
  write_dword(ch_assign_addr(CH_RTD_CHAIN), CFG_RTD_PT1000);
  write_dword(ch_assign_addr(CH_TC_K), CFG_TC_K);
  write_byte(LTC2983_GLOBAL_CONFIG_REG, 0x00);

  ltc2983_initialized = true;
  ESP_LOGI(TAG, "LTC2983 ready — CH%d RSENSE, CH%d/CH%d RTD, CH%d TC-K (CH13−CH12)",
           CH_RSENSE, CH_RTD_SIM, CH_RTD_CHAIN, CH_TC_K);
  return true;
}

static float parse_temperature(uint32_t raw) {
  if (!(raw & (1UL << 24))) return NAN;
  if (raw & 0xFE000000UL) return NAN;  // any fault bit D31..D25
  int32_t t = (int32_t)(raw & 0x00FFFFFFUL);
  if (t & 0x00800000L) t |= (int32_t)0xFF000000;
  return (float)t / 1024.0f;
}

static bool wait_conversion_done() {
  delay(20);
  for (uint32_t i = 0; i < 200; ++i) {
    uint8_t st = read_byte(LTC2983_COMMAND_STATUS_REG);
    if ((st & STATUS_START_MASK) == 0 && (st & STATUS_DONE_MASK) != 0) return true;
    delay(5);
  }
  return false;
}

static float read_channel(uint8_t ch) {
  write_byte(LTC2983_COMMAND_STATUS_REG, LTC2983_CONVERSION_CONTROL | ch);
  if (!wait_conversion_done()) {
    ESP_LOGE(TAG, "CH%d conversion timed out", ch);
    return NAN;
  }
  uint32_t raw = read_dword(ch_data_addr(ch));
  float temp = parse_temperature(raw);
  if (std::isnan(temp))
    ESP_LOGI(TAG, "CH%d: flt=0x%02X temp=nan (hard=%d cj=%d ocr=%d ucr=%d)",
             ch, (uint8_t)(raw >> 24),
             (raw >> 31) & 1, (raw >> 29) & 1, (raw >> 27) & 1, (raw >> 26) & 1);
  else
    ESP_LOGI(TAG, "CH%d: temp=%.2fC", ch, temp);
  return temp;
}

inline void read_ltc2983_sensors(
    esphome::template_::TemplateSensor *simulator,
    esphome::template_::TemplateSensor *chain,
    esphome::template_::TemplateSensor *tc_k) {

  if (!initialize_ltc2983()) return;

  float temp_sim = read_channel(CH_RTD_SIM);
  if (!std::isnan(temp_sim)) simulator->publish_state(temp_sim);

  float temp_chain = read_channel(CH_RTD_CHAIN);
  if (!std::isnan(temp_chain)) chain->publish_state(temp_chain);

  float temp_tc = read_channel(CH_TC_K);
  // CH13−CH12 diff vs TC+ on CH12 → invert slope; CJ from CH4 (temp_sim)
  if (!std::isnan(temp_tc) && !std::isnan(temp_sim))
    temp_tc = 2.0f * temp_sim - temp_tc;
  if (!std::isnan(temp_tc) && temp_tc > -200.0f && temp_tc < 500.0f)
    tc_k->publish_state(temp_tc);
}
