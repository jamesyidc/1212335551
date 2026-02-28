# 完整项目部署指南

## 📋 文档版本

- **版本**: v2.0
- **日期**: 2026-02-27
- **适用于**: 完整项目备份恢复

---

## 📦 备份内容清单

### 1. 源代码文件 (~5MB)

#### 主应用
- `app.py` - Flask主应用（1.06MB，包含所有路由和API）
- 根目录所有Python文件（88个）
- 根目录所有Shell脚本（.sh文件）

#### 重要目录
- `source_code/` - Python API文件（采集器、管理器等）
  - `coin_change_tracker_collector.py` - 27币涨跌幅采集器
  - `bottom_signal_long_monitor.py` - 底部信号监控器
  - `data_backup_service.py` - 数据备份服务
  - 等30+个文件
  
- `panic_paged_v2/` - 恐慌指数系统v2
  - `api_routes.py` - API路由
  - `collector_1h.py` - 1小时数据采集
  - `collector_24h.py` - 24小时数据采集
  - `data_manager.py` - 数据管理器
  
- `panic_v3/` - 恐慌指数系统v3
  - `app.py` - 主应用
  - `collector.py` - 数据采集器
  - `migrate.py` - 数据迁移脚本

- `monitors/` - 监控脚本
  - `coin_change_prediction_monitor.py` - 预测监控
  - `intraday_pattern_monitor.py` - 日内模式监控
  
- `scripts/` - 工具脚本

### 2. HTML模板 (~2MB)
- `templates/` - 88个HTML文件
  - `coin_change_tracker.html` - 27币追踪页面
  - `liquidation_monthly.html` - 爆仓月线图
  - `okx_trading.html` - OKX交易页面
  - 等

### 3. 静态文件
- `static/` - CSS、JS、图片等静态资源
  - `data/daily_predictions/` - 每日预测数据（静态JSON）

### 4. 配置文件 (~1MB)
- `config/` - 配置目录
  - `configs/telegram_config.json` - Telegram通知配置
  - `configs/okx_config.json` - OKX API配置
  - 等
  
- `ecosystem.config.js` - PM2进程管理配置
- `pm2/` - PM2相关配置
- `.env` - 环境变量
- `requirements.txt` - Python依赖
- `*.json` - 各种JSON配置文件

### 5. 数据文件 (~800MB)
- `data/` - 所有JSONL数据文件（**全部数据，非7天**）
  - `coin_change_tracker/` - 27币涨跌幅数据
  - `daily_predictions/` - 每日预测数据
  - `crash_warning_notifications/` - 暴跌预警通知记录
  - `wave_peaks/` - 波峰数据
  - `market_sentiment/` - 市场情绪数据
  - `panic_1h_history/` - 1小时爆仓历史
  - `okx_trading/` - OKX交易记录
  - 等60+个子目录

### 6. 文档文件 (~15MB)
- `docs/` - 440+个Markdown文档
  - 系统文档
  - 修复报告
  - 使用指南
  - API文档
  
- 根目录Markdown文件（140+个）

### 7. 排除的内容
- ❌ `logs/` - 日志文件（65MB，运行时自动生成）
- ❌ `node_modules/` - Node.js依赖（34MB，可重新安装）
- ❌ `backups/` - 旧备份目录
- ❌ `__pycache__/` - Python缓存（自动生成）

---

## 🚀 完整部署步骤

### 前置准备

#### 1. 系统要求
```bash
# 操作系统
Ubuntu 20.04+ 或 Debian 10+

# Python
Python 3.8+

# Node.js（可选，用于某些功能）
Node.js 14+

# 其他
Git、PM2、数据库（如使用）
```

#### 2. 必需软件安装

```bash
# 更新系统
sudo apt update
sudo apt upgrade -y

# 安装Python3和pip
sudo apt install python3 python3-pip -y

# 安装Node.js和npm（可选）
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install nodejs -y

# 安装PM2
sudo npm install -g pm2

# 安装其他依赖
sudo apt install git curl wget tree -y
```

### 步骤1: 解压备份文件

```bash
# 进入备份目录
cd /tmp

# 解压备份（假设备份文件名为 webapp_complete_backup_YYYYMMDD_HHMMSS.tar.gz）
tar -xzf webapp_complete_backup_YYYYMMDD_HHMMSS.tar.gz

# 进入解压后的目录
cd webapp_complete_backup_YYYYMMDD_HHMMSS

# 查看部署信息
cat DEPLOYMENT_INFO.txt
```

### 步骤2: 移动到目标位置

```bash
# 创建应用目录（如果不存在）
sudo mkdir -p /home/user/webapp

# 移动所有文件
sudo mv * /home/user/webapp/
sudo mv .env /home/user/webapp/ 2>/dev/null || true
sudo mv .gitignore /home/user/webapp/ 2>/dev/null || true

# 设置权限
sudo chown -R user:user /home/user/webapp
cd /home/user/webapp
```

### 步骤3: 安装Python依赖

```bash
# 进入项目目录
cd /home/user/webapp

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 或直接安装到系统（不推荐）
pip3 install -r requirements.txt

# 主要依赖包括：
# - Flask==2.3.3
# - requests==2.31.0
# - pytz==2023.3
# - python-okx==1.3.0
# - ccxt==4.0.0
# - pandas
# - numpy
# 等
```

### 步骤4: 配置环境变量

```bash
# 编辑 .env 文件
nano .env

# 必需配置项：
# FLASK_ENV=production
# FLASK_DEBUG=False
# SECRET_KEY=your-secret-key-here

# OKX API配置（如果使用交易功能）
# 编辑 config/configs/okx_config.json
nano config/configs/okx_config.json

# Telegram通知配置
# 编辑 config/configs/telegram_config.json
nano config/configs/telegram_config.json
```

### 步骤5: 初始化数据目录

```bash
# 数据目录已包含在备份中，无需初始化
# 验证数据目录结构
tree -L 2 data/

# 确保权限正确
chmod -R 755 data/
```

### 步骤6: 启动PM2进程

```bash
# 进入项目目录
cd /home/user/webapp

# 使用ecosystem.config.js启动所有进程
pm2 start ecosystem.config.js

# 或手动启动关键进程
pm2 start app.py --name flask-app --interpreter python3
pm2 start source_code/coin_change_tracker_collector.py --name coin-change-tracker --interpreter python3
pm2 start monitors/coin_change_prediction_monitor.py --name coin-change-predictor --interpreter python3

# 查看进程状态
pm2 list

# 保存PM2配置
pm2 save

# 设置PM2开机自启
pm2 startup
# 按提示执行命令
```

### 步骤7: 验证部署

```bash
# 检查Flask应用
curl http://localhost:9002/

# 检查API
curl http://localhost:9002/api/coin-change-tracker/latest

# 查看日志
pm2 logs flask-app --lines 50

# 查看所有进程
pm2 status
```

---

## 🔧 PM2进程管理

### 核心进程列表

| 进程名 | 脚本路径 | 端口 | 描述 |
|--------|----------|------|------|
| flask-app | app.py | 9002 | Flask主应用（Web服务） |
| coin-change-tracker | source_code/coin_change_tracker_collector.py | - | 27币涨跌幅采集器 |
| coin-change-predictor | monitors/coin_change_prediction_monitor.py | - | 预测监控器 |
| intraday-pattern-monitor | monitors/intraday_pattern_monitor.py | - | 日内模式监控 |
| bottom-signal-long-monitor | source_code/bottom_signal_long_monitor.py | - | 底部信号监控 |
| signal-collector | source_code/signal_collector.py | - | 信号采集器 |
| liquidation-1h-collector | source_code/liquidation_1h_collector.py | - | 1小时爆仓采集 |
| panic-wash-collector | source_code/panic_wash_collector.py | - | 恐慌洗盘采集 |
| market-sentiment-collector | source_code/market_sentiment_collector.py | - | 市场情绪采集 |

### PM2常用命令

```bash
# 启动所有进程
pm2 start ecosystem.config.js

# 重启所有进程
pm2 restart all

# 停止所有进程
pm2 stop all

# 删除所有进程
pm2 delete all

# 查看特定进程日志
pm2 logs flask-app

# 查看进程详情
pm2 show flask-app

# 监控进程
pm2 monit

# 重载配置
pm2 reload ecosystem.config.js
```

---

## 🌐 Flask路由对应关系

### 页面路由

| 路由 | 模板文件 | 描述 |
|------|----------|------|
| `/` | `templates/index.html` | 首页 |
| `/coin-change-tracker` | `templates/coin_change_tracker.html` | 27币涨跌幅追踪 |
| `/liquidation-monthly` | `templates/liquidation_monthly.html` | 爆仓月线图 |
| `/okx-trading` | `templates/okx_trading.html` | OKX交易页面 |
| `/panic-paged-v2` | `templates/panic_paged_v2.html` | 恐慌指数v2 |
| `/price-position-v2` | `templates/price_position_v2.html` | 价格位置v2 |

### API路由

#### 27币涨跌幅API
- `GET /api/coin-change-tracker/latest` - 最新数据
- `GET /api/coin-change-tracker/history` - 历史数据
- `GET /api/coin-change-tracker/wave-peaks` - 波峰数据
- `GET /api/coin-change-tracker/daily-prediction` - 每日预判

#### 爆仓API
- `GET /api/liquidation-1h/latest` - 最新1小时爆仓
- `GET /api/liquidation-1h/history` - 历史数据
- `POST /api/liquidation/mark-notify` - 标记通知

#### OKX交易API
- `GET /api/okx-trading/accounts` - 账户列表
- `POST /api/okx-trading/place-order` - 下单
- `GET /api/okx-trading/positions` - 持仓查询

---

## 🔐 安全配置

### 1. 敏感文件权限

```bash
# 限制敏感配置文件权限
chmod 600 .env
chmod 600 config/configs/okx_config.json
chmod 600 config/configs/telegram_config.json
```

### 2. Firewall配置

```bash
# 仅允许本地访问Flask（9002端口）
sudo ufw allow from 127.0.0.1 to any port 9002

# 或允许特定IP
sudo ufw allow from YOUR_IP to any port 9002

# 启用防火墙
sudo ufw enable
```

### 3. Nginx反向代理（可选）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:9002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🐛 故障排查

### 问题1: Flask应用无法启动

```bash
# 检查日志
pm2 logs flask-app --lines 100

# 常见原因：
# 1. 端口被占用
lsof -i:9002

# 2. Python依赖缺失
pip3 list | grep Flask

# 3. 数据目录权限
ls -la data/
```

### 问题2: 采集器无法运行

```bash
# 检查采集器日志
pm2 logs coin-change-tracker --lines 50

# 常见原因：
# 1. API配置错误
cat config/configs/okx_config.json

# 2. 网络问题
ping api.okx.com

# 3. 数据目录不可写
touch data/test.txt
```

### 问题3: 数据不更新

```bash
# 检查进程状态
pm2 status

# 重启相关进程
pm2 restart coin-change-tracker
pm2 restart coin-change-predictor

# 查看最新数据
ls -lht data/coin_change_tracker/ | head -5
```

---

## 📊 数据管理

### 数据目录结构

```
data/
├── coin_change_tracker/          # 27币涨跌幅数据
│   ├── coin_change_20260224.jsonl
│   ├── coin_change_20260225.jsonl
│   └── ...
├── daily_predictions/            # 每日预测
│   ├── prediction_20260224.jsonl
│   └── ...
├── crash_warning_notifications/  # 暴跌预警
├── wave_peaks/                   # 波峰数据
├── market_sentiment/             # 市场情绪
├── panic_1h_history/             # 1小时爆仓
├── liquidation_monthly/          # 月度爆仓
└── okx_trading/                  # 交易记录
```

### 数据清理脚本

```bash
# 清理7天前的数据（保留最近7天）
./manage_data.sh clean 7

# 备份数据
./manage_data.sh backup

# 恢复数据
./manage_data.sh restore backup_file.tar.gz
```

---

## 🔄 更新与维护

### 代码更新

```bash
# 如果使用Git
cd /home/user/webapp
git pull origin main

# 重启应用
pm2 restart all
```

### 依赖更新

```bash
# 更新Python依赖
pip3 install -r requirements.txt --upgrade

# 更新PM2
sudo npm install -g pm2@latest
pm2 update
```

### 定期维护

```bash
# 每周清理日志
pm2 flush

# 每月数据备份
./backup_complete_project_v2.sh

# 检查磁盘空间
df -h
du -sh data/
```

---

## 📞 技术支持

如遇到问题，请检查：
1. `docs/` 目录下的相关文档
2. PM2日志：`pm2 logs`
3. Flask日志：`logs/` 目录
4. 数据文件完整性

---

## 📝 变更日志

### v2.0 (2026-02-27)
- 添加完整备份脚本
- 包含所有数据（非7天）
- 补充source_code、panic_paged_v2、panic_v3目录
- 添加详细部署步骤

### v1.0 (2026-02-26)
- 初始版本
- 基础备份功能

---

**部署指南结束**
