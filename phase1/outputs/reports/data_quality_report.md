# Phase 1 数据质量报告

**生成时间**: 2026-06-16T11:14:43.243207

## 📊 数据概览

- **原始行数**: 1000
- **清洗后行数**: 1000（保留全部样本）
- **列数**: 33

## 🔧 处理过程

### 缺失值
- 处理前: 0
- 处理后: 0

### 重复值
- 移除行数: 0

### 极端值（分位裁剪，不删行）
- 裁剪数值点: 230

### 标签
- 正常样本: 900
- 失效样本: 100

## ✅ 验证结果

- **验证状态**: 通过

## 📈 列清单

| 列名 | 数据类型 |
|------|--------|
| chip_id | object |
| production_date | object |
| chip_model | object |
| pin_flatness_deviation_um | float64 |
| solder_pad_oxidation_percent | float64 |
| package_scratch_depth_um | float64 |
| warpage_um | float64 |
| pin_coplanarity_percent | float64 |
| package_size_deviation_percent | float64 |
| vdd_voltage | float64 |
| idd_static_ma | float64 |
| idd_dynamic_ma | float64 |
| voh_voltage | float64 |
| vol_voltage | float64 |
| vih_voltage | float64 |
| vil_voltage | float64 |
| iil_leakage_ua | float64 |
| iol_leakage_ua | float64 |
| setup_time_ns | float64 |
| hold_time_ns | float64 |
| propagation_delay_ns | float64 |
| rise_time_ns | float64 |
| fall_time_ns | float64 |
| fmax_mhz | float64 |
| jtag_scan_pass | int64 |
| boundary_scan_pass | int64 |
| functional_test_pass | int64 |
| aging_temperature_c | int64 |
| aging_voltage_v | float64 |
| aging_frequency_mhz | float64 |
| aging_duration_hours | int64 |
| failure_status | int64 |
| failure_mode | object |
