# Phase 1 数据质量报告

**生成时间**: 2026-05-29T12:11:08.686418

## 📊 数据概览

- **原始行数**: 554
- **清洗后行数**: 554
- **列数**: 39

## 🔧 数据处理过程

### 缺失值处理
- 处理前: 0 个
- 处理后: 0 个

### 重复值处理
- 处理前: 0 行
- 处理后: 0 行

### 异常值移除
- 移除行数: 446

## ✅ 验证结果

- **验证状态**: 通过

## 📈 列统计

| 列名 | 数据类型 |
|------|--------|
| chip_id | str |
| pin_flatness_deviation_um | float64 |
| solder_pad_oxidation_percent | float64 |
| package_scratch_depth_um | float64 |
| warpage_um | float64 |
| pin_coplanarity_percent | float64 |
| package_size_deviation_percent | float64 |
| appearance_test_pass | int64 |
| appearance_quality_score | float64 |
| vdd_voltage | float64 |
| idd_static_ma | float64 |
| idd_dynamic_ma | float64 |
| voh_voltage | float64 |
| vol_voltage | float64 |
| vih_voltage | float64 |
| vil_voltage | float64 |
| iil_leakage_ua | float64 |
| iol_leakage_ua | float64 |
| dc_test_pass | float64 |
| dc_electrical_quality_score | float64 |
| setup_time_ns | float64 |
| hold_time_ns | float64 |
| propagation_delay_ns | float64 |
| rise_time_ns | float64 |
| fall_time_ns | float64 |
| fmax_mhz | float64 |
| ac_test_pass | float64 |
| ac_electrical_quality_score | float64 |
| jtag_scan_pass | float64 |
| boundary_scan_pass | float64 |
| functional_test_pass | float64 |
| functional_quality_score | float64 |
| aging_temperature_c | int64 |
| aging_voltage_v | float64 |
| aging_frequency_mhz | float64 |
| aging_duration_hours | float64 |
| reliability_risk_level | str |
| production_date | str |
| chip_model | str |
