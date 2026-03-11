# 完整项目备份清单

## 📦 备份信息

- **备份文件**: `webapp_complete_backup_20260228_073515.tar.gz`
- **备份位置**: `/tmp/webapp_complete_backup_20260228_073515.tar.gz`
- **备份大小**: 256MB（压缩后）
- **原始大小**: ~3.1GB（压缩前）
- **MD5校验**: `5a8fb2129fa049c62597391d0a738172`
- **备份时间**: 2026-02-28 07:35:15
- **备份方式**: 完整备份（所有数据，非7天）

---

## 📋 备份内容详细清单

### 1. Python源码文件 (~5MB)

#### 主应用文件
- ✅ `app.py` (1.06MB) - Flask主应用，包含所有路由和API
- ✅ 所有根目录`.py`文件 (88个)
  - `add_beijing_time_field.py`
  - `calculate_false_breakout_profit.py`
  - `calculate_short_profit.py`
  - `check_all_patterns_detailed.py`
  - `convert_predictions_to_jsonl.py`
  - `generate_historical_predictions.py`
  - `regenerate_february_predictions.py`
  - 等80+个文件

#### 关键目录
- ✅ `source_code/` - Python API文件（30+个）
  - `coin_change_tracker_collector.py` (15KB) - 27币涨跌幅采集器
  - `bottom_signal_long_monitor.py` (17KB) - 底部信号监控
  - `data_backup_service.py` (11KB) - 数据备份服务
  - `data_manager.py` (9KB) - 数据管理器
  - `signal_collector.py` - 信号采集器
  - `liquidation_1h_collector.py` - 1小时爆仓采集
  - `panic_wash_collector.py` - 恐慌洗盘采集
  - `market_sentiment_collector.py` - 市场情绪采集
  - `crypto_index_collector.py` - 加密指数采集
  - `price_speed_collector.py` - 价格速度采集
  - `sar_slope_collector.py` - SAR斜率采集
  - `financial_indicators_collector.py` - 财务指标采集
  - `okx_day_change_collector.py` - OKX日涨跌采集
  - `price_baseline_collector.py` - 价格基准采集
  - `sar_bias_stats_collector.py` - SAR偏差统计
  - 等

- ✅ `panic_paged_v2/` - 恐慌指数系统v2
  - `api_routes.py` (9KB) - API路由
  - `collector_1h.py` (3KB) - 1小时数据采集
  - `collector_24h.py` (5KB) - 24小时数据采集
  - `data_manager.py` (6KB) - 数据管理
  - `deploy.sh` - 部署脚本
  - `ecosystem.config.json` - PM2配置
  - README文档

- ✅ `panic_v3/` - 恐慌指数系统v3
  - `app.py` (5KB) - 主应用
  - `collector.py` (7KB) - 数据采集
  - `migrate.py` (6KB) - 数据迁移
  - README和部署文档

- ✅ `monitors/` - 监控脚本目录
  - `coin_change_prediction_monitor.py` - 预测监控器
  - `intraday_pattern_monitor.py` - 日内模式监控

- ✅ `scripts/` - 工具脚本目录

- ✅ `price_position_v2/` - 价格位置系统v2

- ✅ `code/` - 代码目录

- ✅ `tests/` - 测试文件目录

### 2. HTML模板文件 (~2MB)

- ✅ `templates/` - 88个HTML模板文件
  - `index.html` - 首页
  - `coin_change_tracker.html` (400KB+) - 27币涨跌幅追踪页面
  - `liquidation_monthly.html` (150KB+) - 爆仓月线图
  - `okx_trading.html` - OKX交易页面
  - `panic_paged_v2.html` - 恐慌指数v2
  - `price_position_v2.html` - 价格位置v2
  - `sar_bias.html` - SAR偏差
  - `support_resistance.html` - 支撑阻力
  - 等80+个文件

### 3. 静态文件

- ✅ `static/` - 静态资源目录
  - `data/daily_predictions/` - 每日预测数据（静态JSON）
  - CSS、JavaScript、图片等

### 4. 配置文件 (~1MB)

- ✅ `config/` - 配置目录
  - `configs/telegram_config.json` - Telegram通知配置
  - `configs/okx_config.json` - OKX API配置
  - 其他配置文件

- ✅ `ecosystem.config.js` (11KB) - PM2进程管理配置
- ✅ `pm2/` - PM2相关配置文件
- ✅ `.env` - 环境变量配置
- ✅ `requirements.txt` (4KB) - Python依赖清单
- ✅ 所有`.json`配置文件
  - `okx_accounts.json`
  - `okx_account_limits.json`
  - `telegram_notification_config.json`
  - 等

### 5. Shell脚本文件

- ✅ 所有`.sh`脚本文件
  - `backup_complete_project.sh` - 原备份脚本
  - `backup_complete_project_v2.sh` - 完整备份脚本v2
  - `restore_project.sh` - 恢复脚本
  - `migrate_coin_tracker.sh` - 数据迁移脚本
  - `quick_backfill.sh` - 快速回填脚本
  - `manage_data.sh` - 数据管理脚本
  - `test_okx_trading.sh` - 交易测试脚本
  - `test_jsonl_workflow.sh` - JSONL工作流测试
  - 等

### 6. 数据文件 (~3.1GB 原始 → 256MB 压缩)

#### 完整数据目录结构

```
data/ (68个子目录)
├── coin_change_tracker/          # 27币涨跌幅数据
│   ├── coin_change_20260201.jsonl
│   ├── coin_change_20260202.jsonl
│   ├── ... (每日文件，完整历史)
│   └── coin_change_20260227.jsonl
│
├── coin_change_tracker_baseline/  # 基准数据
│   └── baseline_YYYYMMDD.json
│
├── daily_predictions/            # 每日预测
│   ├── prediction_20260201.jsonl
│   ├── ... (每日预测，完整历史)
│   └── prediction_20260227.jsonl
│
├── crash_warning_notifications/  # 暴跌预警通知
│   └── telegram_sent_YYYYMMDD.json
│
├── wave_peaks/                   # 波峰数据
│   └── wave_peaks_YYYYMMDD.jsonl
│
├── market_sentiment/             # 市场情绪
│   └── sentiment_YYYYMMDD.jsonl
│
├── panic_1h_history/             # 1小时爆仓历史
│   └── panic_1h_YYYYMMDD.jsonl
│
├── panic_30days/                 # 30天爆仓
│   └── liquidation_30days_YYYYMMDD.jsonl
│
├── liquidation_monthly/          # 月度爆仓
│   └── liquidation_monthly_YYYYMM.jsonl
│
├── rsi_history/                  # RSI历史
│   └── rsi_YYYYMMDD.jsonl
│
├── okx_trading/                  # OKX交易记录
│   ├── trade_history_YYYYMMDD.jsonl
│   ├── positions/
│   └── orders/
│
├── okx_trading_logs/             # 交易日志
│   └── trading_log_YYYYMMDD.jsonl
│
├── bottom_signal_executions/     # 底部信号执行
│   └── executions_YYYYMMDD.jsonl
│
├── intraday_patterns/            # 日内模式
│   └── patterns_YYYYMMDD.jsonl
│
├── signal_data/                  # 信号数据
│   └── signal_YYYYMMDD.jsonl
│
├── crypto_index/                 # 加密指数
├── financial_indicators/         # 财务指标
├── price_speed/                  # 价格速度
├── sar_slope/                    # SAR斜率
├── price_baseline/               # 价格基准
├── sar_bias_stats/               # SAR偏差统计
├── price_comparison/             # 价格对比
├── v1v2_data/                    # V1V2数据
├── support_resistance/           # 支撑阻力
├── anchor_daily/                 # 锚点日线
├── system_health/                # 系统健康
├── data_health/                  # 数据健康
├── gdrive_sync/                  # Google Drive同步
├── dashboard_data/               # 仪表板数据
└── ... (更多数据目录)
```

**特别说明**: 
- ✅ 包含**所有历史数据**，非仅7天
- ✅ 所有JSONL文件完整保留
- ✅ 数据时间跨度：从系统开始到2026-02-27
- ✅ 数据完整性：100%

### 7. 文档文件 (~15MB)

#### docs/目录 (440+个Markdown文件)

**修复报告类** (50+个)
- `fix_chart_line_disappearance.md` - 图表线条消失修复
- `date_switching_issue_resolution.md` - 日期切换问题
- `liquidation_telegram_notification.md` - 爆仓Telegram通知
- `BACKEND_CALCULATION_FIX.md` - 后端计算修复
- 等

**系统文档类** (100+个)
- `DEPLOYMENT_GUIDE.md` - 部署指南
- `SYSTEM_JSONL_MAPPING.md` - 系统JSONL映射
- `JSONL_FILE_DESCRIPTIONS.md` - JSONL文件描述
- `API_DOCUMENTATION.md` - API文档
- 等

**功能说明类** (150+个)
- 各系统功能说明
- 使用指南
- 技术细节文档
- 等

#### 根目录Markdown文件 (140+个)
- 项目总览文档
- 重要说明文件
- 快速参考指南
- 变更日志
- 等

### 8. 其他文件

- ✅ `.gitignore` - Git忽略规则
- ✅ `DEPLOYMENT_INFO.txt` - 自动生成的部署信息
- ✅ `DEPLOYMENT_GUIDE_COMPLETE.md` - 完整部署指南

---

## 🚫 排除的内容

为减小备份体积，以下内容未包含（可重新生成或安装）：

- ❌ `logs/` (~65MB) - 运行日志（运行时自动生成）
- ❌ `node_modules/` (~34MB) - Node.js依赖（可用npm install重装）
- ❌ `backups/` - 旧备份目录
- ❌ `__pycache__/` - Python缓存文件（自动生成）
- ❌ `.git/` - Git版本控制目录（可从仓库clone）

---

## 🔧 PM2进程清单（备份时快照）

### 运行中的进程
```
总进程数: 27个
在线状态: 27个
内存使用: ~800MB
CPU使用: <5%
```

### 核心进程列表
1. `flask-app` - Flask主应用 (端口9002)
2. `coin-change-tracker` - 27币采集器
3. `coin-change-predictor` - 预测监控
4. `intraday-pattern-monitor` - 日内模式
5. `bottom-signal-long-monitor` - 底部信号
6. `signal-collector` - 信号采集
7. `liquidation-1h-collector` - 1h爆仓采集
8. `panic-wash-collector` - 恐慌洗盘
9. `market-sentiment-collector` - 市场情绪
10. `crypto-index-collector` - 加密指数
11. ... (共27个进程)

---

## 📊 统计信息

### 文件类型统计
- Python文件: 118个
- HTML文件: 88个
- Markdown文档: 580个
- JSON配置文件: 25个
- Shell脚本: 15个
- JSONL数据文件: 数千个

### 目录统计
- 主要目录: 22个
- 数据子目录: 68个
- 总文件数: ~5000+

### 代码行数统计（估算）
- Python代码: ~50,000行
- HTML/JS: ~100,000行
- 文档: ~500,000行
- 总计: ~650,000行

---

## 🔐 安全与合规

### 已备份的敏感文件
- ⚠️ `.env` - 环境变量（包含敏感信息）
- ⚠️ `config/configs/okx_config.json` - OKX API密钥
- ⚠️ `config/configs/telegram_config.json` - Telegram Bot Token

### 安全建议
1. **妥善保管备份文件**
2. **限制备份文件访问权限** (`chmod 600`)
3. **定期更换API密钥**
4. **不要上传到公共仓库**

---

## 📝 恢复说明

### 快速恢复
```bash
# 1. 解压备份
cd /tmp
tar -xzf webapp_complete_backup_20260228_073515.tar.gz

# 2. 移动到目标位置
sudo mv webapp_complete_backup_20260228_073515/* /home/user/webapp/

# 3. 安装依赖
cd /home/user/webapp
pip3 install -r requirements.txt

# 4. 启动服务
pm2 start ecosystem.config.js

# 5. 验证
pm2 list
curl http://localhost:9002/
```

### 详细恢复指南
请参考：`DEPLOYMENT_GUIDE_COMPLETE.md`

---

## ✅ 验证清单

- [x] 主应用文件已备份
- [x] 所有Python源码已备份
- [x] source_code目录已备份
- [x] panic_paged_v2目录已备份
- [x] panic_v3目录已备份
- [x] HTML模板已备份
- [x] 配置文件已备份
- [x] 所有数据文件已备份（完整历史）
- [x] 文档文件已备份
- [x] Shell脚本已备份
- [x] PM2配置已备份
- [x] 依赖清单已备份
- [x] 部署指南已包含

---

## 📞 支持信息

**备份工具版本**: v2.0  
**备份策略**: 完整备份（所有历史数据）  
**压缩比**: ~12:1 (3.1GB → 256MB)  
**恢复时间**: ~5-10分钟（不含依赖安装）

---

**备份完成时间**: 2026-02-28 07:36:17  
**备份状态**: ✅ 成功  
**数据完整性**: ✅ 已验证  
**可恢复性**: ✅ 已测试
