# 27币涨跌幅追踪系统 - 完整部署指南

## 📦 项目概述

**版本**: v3.3.1 (2026-02-23)  
**项目大小**: ~2GB（包含全部历史数据）  
**备份位置**: `/tmp/webapp_full_backup_20260223.tar.gz`

---

## 📊 项目结构分析

### 文件类型统计

| 文件类型 | 数量 | 总大小 | 占比 | 说明 |
|---------|------|--------|------|------|
| Python 文件 | 88 | ~5MB | 0.25% | 主应用、采集器、管理器、工具等 |
| Markdown 文档 | 440 | ~15MB | 0.75% | 系统文档、修复报告、使用指南 |
| HTML 模板 | 88 | ~2MB | 0.1% | Web界面模板 |
| 配置文件 | 15+ | <1MB | <0.05% | JSON、JS配置文件 |
| 数据文件 (JSONL) | 数千 | ~800MB | 40% | 历史交易数据 |
| 静态资源 | 若干 | ~20MB | 1% | CSS、JS、图片等 |
| 依赖包 (node_modules) | ~1000+ | ~200MB | 10% | Node.js依赖 |
| 依赖包 (venv) | ~500+ | ~900MB | 45% | Python虚拟环境 |
| 其他 | 若干 | ~50MB | 2.5% | 日志、临时文件等 |
| **总计** | **2,616+** | **~2GB** | **100%** | 完整项目 |

---

## 🚀 快速部署（推荐方法）

### 步骤1: 下载并解压备份

```bash
# 从备份恢复
cd /home/user
tar -xzf /tmp/webapp_full_backup_20260223.tar.gz

# 进入项目目录
cd webapp
```

### 步骤2: 激活环境并启动

```bash
# 激活Python虚拟环境
source venv/bin/activate

# 启动Flask应用（PM2管理）
pm2 start ecosystem.config.js

# 查看状态
pm2 status
```

### 步骤3: 验证部署

```bash
# 测试首页
curl http://localhost:9002/

# 测试API
curl http://localhost:9002/api/coin-change-tracker/latest
```

---

## 📂 关键目录说明

```
/home/user/webapp/
├── app.py                  # Flask主应用
├── DEPLOYMENT_GUIDE.md     # 本部署指南
├── templates/              # HTML模板 (~2MB)
├── data/                   # 数据目录 (~800MB，全部历史数据)
├── venv/                   # Python虚拟环境 (~900MB)
├── node_modules/           # Node.js依赖 (~200MB)
├── logs/                   # 日志目录
└── ecosystem.config.js     # PM2配置
```

---

## 🔄 Flask路由清单

### 主要页面路由

- `/` - 首页
- `/coin-change-tracker` - 27币追踪系统
- `/okx-trading` - OKX交易界面
- `/control-center` - 控制中心

### 主要API路由

- `/api/coin-change-tracker/latest` - 最新数据
- `/api/coin-change-tracker/history` - 历史数据
- `/api/okx-trading/logs` - 交易日志
- `/api/market-sentiment/history` - 市场情绪
- `/api/intraday-patterns/detections/<date>` - 日内模式

---

## 🛠️ 常用命令

### PM2管理

```bash
pm2 list           # 查看进程
pm2 logs           # 查看日志
pm2 restart all    # 重启
pm2 stop all       # 停止
```

### 备份数据

```bash
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/
```

---

## 📋 版本信息

**当前版本**: v3.3.1 (2026-02-23)

**最新修复**:
- ✅ 修复页面加载卡在0%的JavaScript语法错误
- ✅ 修复交易日志date参数类型检查
- ✅ 修复"诱空试仓抄底"信号颜色识别
- ✅ 显示所有日内模式检测信号
- ✅ 优化图表标记加载同步

**Git提交记录**:
```
e501f1b - fix(coin-tracker): 修复loadTradingLogs date参数类型检查
aea4665 - fix(coin-tracker): 回退到工作版本 - 修复JavaScript语法错误
a29703a - fix(coin-tracker): 修复诱空试仓抄底信号颜色识别问题
a731689 - fix(coin-tracker): 显示所有日内模式检测信号
```

---

## 🆘 技术支持

**项目仓库**: https://github.com/jamesyidc/25669889956  
**分支**: `restored-from-backup`  
**备份文件**: `/tmp/webapp_full_backup_20260223.tar.gz`

---

**部署日期**: 2026-02-23  
**文档版本**: 1.0
