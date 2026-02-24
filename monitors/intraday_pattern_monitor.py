#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日内模式监控器 (2:00-23:59)
监控27币种10分钟上涨占比柱状图，识别特定模式并发送交易信号

⚠️ 重要：小周期服从大周期原则
- 0-2点预判信号为"做空"系列时，禁止触发所有"做多"信号
- 0-2点预判信号为"做多"系列时，禁止触发所有"做空"信号

模式1: 诱多等待新低
- 连续3根：红→黄→绿 或 绿→黄→红
- 连续4根：红→黄→黄→绿
- 动态阈值：
  * 预测"等待新低" → 触发后10分钟上涨占比平均 > 65%
  * 预测"做空"或"观望" → 触发后10分钟上涨占比平均 > 50%
- 操作：逢高做空 [做空信号]

模式2: 诱空试仓抄底  
- 红柱后连续3个空白柱子，空白占比≤25%
- 触发时机：在空白柱期间触发
- 操作：开多单试仓 [做多信号]

模式3: 筑底信号
- 连续3根：黄→绿→黄
- 触发条件：
  * 触发后10分钟上涨占比 < 10%
  * 涨跌幅总和 < -50%
- 操作：逢低做多 [做多信号]

模式4: 诱空信号
- 连续4根：绿→红→红→绿
- 或连续3根：绿→红→绿
- 触发条件：中间柱上涨占比 < 10%
- 操作：逢低做多 [做多信号]

颜色定义:
- 绿色: 上涨占比 > 55%
- 黄色: 上涨占比 45%-55%
- 红色: 上涨占比 < 45%
- 空白: 上涨占比 = 0%
"""

import json
import os
import sys
import time
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import deque

# 项目根目录
BASE_DIR = Path('/home/user/webapp')
sys.path.insert(0, str(BASE_DIR))

# 数据目录
DATA_DIR = BASE_DIR / 'data' / 'intraday_patterns'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# API基础URL
API_BASE = 'http://localhost:9002'

# 配置
CHECK_INTERVAL = 600  # 检查间隔（秒）= 10分钟
MONITOR_START_HOUR = 2  # 监控开始时间（北京时间）
MONITOR_END_HOUR = 23  # 监控结束时间（北京时间）
BLANK_RATIO_THRESHOLD = 0.25  # 空白占比阈值（25%）

# Telegram配置
TELEGRAM_BOT_TOKEN = "8437045462:AAFePnwdC21cqeWhZISMQHGGgjmroVqE2H0"
TELEGRAM_CHAT_ID = "-1003227444260"


def log(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)


def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.now(timezone.utc)
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time


def get_daily_prediction():
    """获取今日0-2点预判信号"""
    try:
        beijing_time = get_beijing_time()
        date_str = beijing_time.strftime('%Y-%m-%d')
        
        # 调用API获取预判数据
        url = f'{API_BASE}/api/coin-change-tracker/daily-prediction'
        response = requests.get(url, timeout=10)
        result = response.json()
        
        if result.get('success') and result.get('data'):
            signal = result['data'].get('signal', '')
            description = result['data'].get('description', '')
            log(f"✅ 获取到今日预判: {signal}")
            return {
                'signal': signal,
                'description': description,
                'date': date_str
            }
        else:
            log(f"⚠️ 无法获取今日预判，允许所有信号")
            return None
            
    except Exception as e:
        log(f"❌ 获取预判失败: {e}")
        return None


def is_signal_allowed(pattern_signal, daily_prediction, total_change=None):
    """检查信号是否允许执行（小周期服从大周期）
    
    Args:
        pattern_signal: 模式信号类型 ('long' 做多 或 'short' 做空)
        daily_prediction: 今日预判数据
        total_change: 当前27币总涨跌幅
        
    Returns:
        tuple: (allowed, reason)
    """
    if not daily_prediction:
        # 没有预判数据，允许所有信号
        return True, "无大周期预判，允许执行"
    
    signal = daily_prediction.get('signal', '')
    
    # 定义明确的做空信号
    short_signals = ['做空', '等待新低']
    # 定义明确的做多信号
    long_signals = ['低吸', '诱空试盘抄底']
    # 中性信号（多空对决未分胜负）
    neutral_signals = ['观望']
    # 禁止所有操作的信号
    no_trade_signals = ['诱多不参与', '单边诱多行情不参与']
    
    # 判断大周期方向
    is_daily_short = any(s in signal for s in short_signals)
    is_daily_long = any(s in signal for s in long_signals)
    is_daily_neutral = any(s in signal for s in neutral_signals)
    is_no_trade = any(s in signal for s in no_trade_signals)
    
    # 如果是禁止交易信号，禁止所有操作
    if is_no_trade:
        return False, f"大周期为不参与信号({signal})，禁止所有操作"
    
    # 如果是中性信号（观望），需要根据总涨跌幅判断
    if is_daily_neutral:
        if total_change is None:
            # 没有涨跌幅数据，允许操作
            return True, f"大周期为中性信号({signal})，允许多空操作"
        
        # 观望信号的涨跌幅条件判断
        if pattern_signal == 'short':
            # 做空信号：总涨跌幅 > -15 (在-15以上)
            if total_change > -15:
                return True, f"观望且涨跌幅{total_change:.2f}% > -15，允许做空"
            else:
                return False, f"观望但涨跌幅{total_change:.2f}% ≤ -15，禁止做空"
        
        elif pattern_signal == 'long':
            # 做多信号：总涨跌幅 < -90 (在-90以下)
            if total_change < -90:
                return True, f"观望且涨跌幅{total_change:.2f}% < -90，允许做多"
            else:
                return False, f"观望但涨跌幅{total_change:.2f}% ≥ -90，禁止做多"
    
    if pattern_signal == 'short':
        # 小周期做空信号
        if is_daily_long:
            return False, f"大周期为做多信号({signal})，禁止做空"
        return True, "与大周期一致，允许执行"
    
    elif pattern_signal == 'long':
        # 小周期做多信号
        if is_daily_short:
            return False, f"大周期为做空信号({signal})，禁止做多"
        return True, "与大周期一致，允许执行"
    
    return True, "信号类型未知，允许执行"


def send_telegram_message(message):
    """发送Telegram消息"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            log("✅ Telegram消息发送成功")
            return True
        else:
            log(f"⚠️ Telegram消息发送失败: {response.status_code}")
            return False
    except Exception as e:
        log(f"❌ Telegram消息发送异常: {e}")
        return False


def determine_bar_color(up_ratio):
    """判断柱子颜色
    
    Args:
        up_ratio: 上涨占比（0-100）
        
    Returns:
        str: 'green', 'yellow', 'red', 'blank'
    """
    if up_ratio == 0:
        return 'blank'
    elif up_ratio > 55:
        return 'green'
    elif 45 <= up_ratio <= 55:
        return 'yellow'
    else:  # up_ratio < 45
        return 'red'


def fetch_today_data():
    """获取今天的10分钟上涨占比数据"""
    try:
        beijing_time = get_beijing_time()
        today_str = beijing_time.strftime('%Y-%m-%d')
        
        # 调用API获取历史数据
        url = f'{API_BASE}/api/coin-change-tracker/history?date={today_str}&limit=1440'
        response = requests.get(url, timeout=30)
        result = response.json()
        
        if not result.get('success') or not result.get('data'):
            log(f"⚠️ 获取数据失败或数据为空")
            return None
        
        data = result['data']
        log(f"✅ 获取到 {len(data)} 条数据记录")
        
        # 按10分钟分组并计算上涨占比
        grouped = {}
        for record in data:
            time_str = record.get('beijing_time', '')
            if not time_str:
                continue
            
            # 提取小时和分钟
            try:
                time_part = time_str.split(' ')[1] if ' ' in time_str else time_str
                hour, minute, _ = time_part.split(':')
                hour, minute = int(hour), int(minute)
                
                # 计算10分钟区间索引
                group_index = hour * 6 + minute // 10
                
                if group_index not in grouped:
                    grouped[group_index] = []
                
                # 计算上涨币种占比
                changes = record.get('changes', {})
                if changes:
                    total_coins = len(changes)
                    # changes是字典，值也是字典，包含change_pct字段
                    up_coins = sum(1 for coin_data in changes.values() 
                                   if isinstance(coin_data, dict) and coin_data.get('change_pct', 0) > 0)
                    up_ratio = (up_coins / total_coins * 100) if total_coins > 0 else 0
                    grouped[group_index].append(up_ratio)
                    
            except Exception as e:
                continue
        
        # 计算每个区间的平均上涨占比和颜色
        bars = []
        for group_index in sorted(grouped.keys()):
            ratios = grouped[group_index]
            if ratios:
                avg_ratio = sum(ratios) / len(ratios)
                color = determine_bar_color(avg_ratio)
                
                hour = group_index // 6
                minute = (group_index % 6) * 10
                time_label = f"{hour:02d}:{minute:02d}"
                
                bars.append({
                    'time': time_label,
                    'hour': hour,
                    'up_ratio': round(avg_ratio, 2),
                    'color': color
                })
        
        return bars
        
    except Exception as e:
        log(f"❌ 获取数据异常: {e}")
        import traceback
        traceback.print_exc()
        return None


def check_pattern_1(bars, daily_prediction=None):
    """检查模式1：诱多等待新低
    
    连续3根：红→黄→绿 或 绿→黄→红
    连续4根：红→黄→黄→绿
    
    动态阈值（根据预测信号）：
    - "等待新低" → 触发后10分钟上涨占比平均 > 65%
    - "做空"或"观望" → 触发后10分钟上涨占比平均 > 50%
    
    Returns:
        dict or None: 如果检测到模式，返回详情
    """
    if len(bars) < 3:
        return None
    
    # 确定阈值
    signal = daily_prediction.get('signal', '') if daily_prediction else ''
    threshold = 65 if '等待新低' in signal else 50
    
    # 先检查4根柱子模式：红→黄→黄→绿
    if len(bars) >= 4:
        for i in range(len(bars) - 3):
            colors = [bars[i]['color'], bars[i+1]['color'], bars[i+2]['color'], bars[i+3]['color']]
            
            if colors == ['red', 'yellow', 'yellow', 'green']:
                # 检查触发后的上涨占比（最后一根柱子）
                trigger_bar_ratio = bars[i+3]['up_ratio']
                
                if trigger_bar_ratio > threshold:
                    return {
                        'pattern': 'pattern_1',
                        'pattern_name': '诱多等待新低',
                        'pattern_type': '红→黄→黄→绿',
                        'signal': '逢高做空',
                        'signal_type': 'short',
                        'time_range': f"{bars[i]['time']} - {bars[i+3]['time']}",
                        'bars': [
                            f"{bars[i]['time']} {bars[i]['up_ratio']:.1f}%",
                            f"{bars[i+1]['time']} {bars[i+1]['up_ratio']:.1f}%",
                            f"{bars[i+2]['time']} {bars[i+2]['up_ratio']:.1f}%",
                            f"{bars[i+3]['time']} {bars[i+3]['up_ratio']:.1f}%"
                        ],
                        'detected_at': bars[i+3]['time'],
                        'threshold': threshold,
                        'trigger_ratio': trigger_bar_ratio
                    }
    
    # 检查3根柱子模式
    for i in range(len(bars) - 2):
        colors = [bars[i]['color'], bars[i+1]['color'], bars[i+2]['color']]
        
        # 检查是否匹配模式
        is_red_yellow_green = (colors == ['red', 'yellow', 'green'])
        is_green_yellow_red = (colors == ['green', 'yellow', 'red'])
        
        if is_red_yellow_green or is_green_yellow_red:
            pattern_type = "红→黄→绿" if is_red_yellow_green else "绿→黄→红"
            
            # 检查触发后的上涨占比（最后一根柱子）
            trigger_bar_ratio = bars[i+2]['up_ratio']
            
            if trigger_bar_ratio > threshold:
                return {
                    'pattern': 'pattern_1',
                    'pattern_name': '诱多等待新低',
                    'pattern_type': pattern_type,
                    'signal': '逢高做空',
                    'signal_type': 'short',
                    'time_range': f"{bars[i]['time']} - {bars[i+2]['time']}",
                    'bars': [
                        f"{bars[i]['time']} {bars[i]['up_ratio']:.1f}%",
                        f"{bars[i+1]['time']} {bars[i+1]['up_ratio']:.1f}%",
                        f"{bars[i+2]['time']} {bars[i+2]['up_ratio']:.1f}%"
                    ],
                    'detected_at': bars[i+2]['time'],
                    'threshold': threshold,
                    'trigger_ratio': trigger_bar_ratio
                }
    
    return None


def check_pattern_3(bars, total_change=None):
    """检查模式3：筑底信号
    
    连续3根：黄→绿→黄
    触发条件：
    1. 触发后10分钟上涨占比 < 10%
    2. 涨跌幅总和 < -50%
    
    Returns:
        dict or None: 如果检测到模式，返回详情
    """
    if len(bars) < 3:
        return None
    
    # 检查涨跌幅总和条件
    if total_change is not None and total_change >= -50:
        return None
    
    # 检查连续3根柱子
    for i in range(len(bars) - 2):
        colors = [bars[i]['color'], bars[i+1]['color'], bars[i+2]['color']]
        
        # 检查是否匹配模式：黄→绿→黄
        if colors == ['yellow', 'green', 'yellow']:
            # 检查触发后的上涨占比（最后一根柱子）
            trigger_bar_ratio = bars[i+2]['up_ratio']
            
            if trigger_bar_ratio < 10:
                return {
                    'pattern': 'pattern_3',
                    'pattern_name': '筑底信号',
                    'pattern_type': '黄→绿→黄',
                    'signal': '逢低做多',
                    'signal_type': 'long',
                    'time_range': f"{bars[i]['time']} - {bars[i+2]['time']}",
                    'bars': [
                        f"{bars[i]['time']} {bars[i]['up_ratio']:.1f}%",
                        f"{bars[i+1]['time']} {bars[i+1]['up_ratio']:.1f}%",
                        f"{bars[i+2]['time']} {bars[i+2]['up_ratio']:.1f}%"
                    ],
                    'detected_at': bars[i+2]['time'],
                    'trigger_ratio': trigger_bar_ratio,
                    'total_change': total_change
                }
    
    return None


def check_pattern_4(bars):
    """检查模式4：诱空信号
    
    连续4根：绿→红→红→绿
    或连续3根：绿→红→绿
    触发条件：中间柱上涨占比 < 10%
    
    Returns:
        dict or None: 如果检测到模式，返回详情
    """
    if len(bars) < 3:
        return None
    
    # 先检查连续4根：绿→红→红→绿
    for i in range(len(bars) - 3):
        colors = [bars[i]['color'], bars[i+1]['color'], bars[i+2]['color'], bars[i+3]['color']]
        
        if colors == ['green', 'red', 'red', 'green']:
            # 检查中间两根红柱的上涨占比
            middle_ratio_1 = bars[i+1]['up_ratio']
            middle_ratio_2 = bars[i+2]['up_ratio']
            
            if middle_ratio_1 < 10 and middle_ratio_2 < 10:
                return {
                    'pattern': 'pattern_4',
                    'pattern_name': '诱空信号',
                    'pattern_type': '绿→红→红→绿 (4根)',
                    'signal': '逢低做多',
                    'signal_type': 'long',
                    'time_range': f"{bars[i]['time']} - {bars[i+3]['time']}",
                    'bars': [
                        f"{bars[i]['time']} {bars[i]['up_ratio']:.1f}%",
                        f"{bars[i+1]['time']} {bars[i+1]['up_ratio']:.1f}%",
                        f"{bars[i+2]['time']} {bars[i+2]['up_ratio']:.1f}%",
                        f"{bars[i+3]['time']} {bars[i+3]['up_ratio']:.1f}%"
                    ],
                    'detected_at': bars[i+3]['time'],
                    'middle_ratios': [middle_ratio_1, middle_ratio_2]
                }
    
    # 再检查连续3根：绿→红→绿
    for i in range(len(bars) - 2):
        colors = [bars[i]['color'], bars[i+1]['color'], bars[i+2]['color']]
        
        if colors == ['green', 'red', 'green']:
            # 检查中间红柱的上涨占比
            middle_ratio = bars[i+1]['up_ratio']
            
            if middle_ratio < 10:
                return {
                    'pattern': 'pattern_4',
                    'pattern_name': '诱空信号',
                    'pattern_type': '绿→红→绿 (3根)',
                    'signal': '逢低做多',
                    'signal_type': 'long',
                    'time_range': f"{bars[i]['time']} - {bars[i+2]['time']}",
                    'bars': [
                        f"{bars[i]['time']} {bars[i]['up_ratio']:.1f}%",
                        f"{bars[i+1]['time']} {bars[i+1]['up_ratio']:.1f}%",
                        f"{bars[i+2]['time']} {bars[i+2]['up_ratio']:.1f}%"
                    ],
                    'detected_at': bars[i+2]['time'],
                    'middle_ratios': [middle_ratio]
                }
    
    return None


def check_pattern_2(bars):
    """检查模式2：诱空试仓抄底
    
    红柱子后面连续3个空白柱子，且空白占比≤25%
    
    Returns:
        dict or None: 如果检测到模式，返回详情
    """
    if len(bars) < 4:
        return None
    
    # 计算空白柱子占比
    total_bars = len(bars)
    blank_bars = sum(1 for bar in bars if bar['color'] == 'blank')
    blank_ratio = blank_bars / total_bars if total_bars > 0 else 0
    
    # 检查空白占比是否符合条件
    if blank_ratio > BLANK_RATIO_THRESHOLD:
        log(f"⚠️ 空白占比 {blank_ratio*100:.1f}% 超过阈值 {BLANK_RATIO_THRESHOLD*100}%，不满足模式2条件")
        return None
    
    # 检查红柱子后面是否有连续3个空白柱子
    for i in range(len(bars) - 3):
        if bars[i]['color'] == 'red':
            if (bars[i+1]['color'] == 'blank' and 
                bars[i+2]['color'] == 'blank' and 
                bars[i+3]['color'] == 'blank'):
                
                return {
                    'pattern': 'pattern_2',
                    'pattern_name': '诱空试仓抄底',
                    'signal': '开多单试仓',
                    'signal_type': 'long',
                    'time_range': f"{bars[i]['time']} - {bars[i+3]['time']}",
                    'bars': [
                        f"{bars[i]['time']} 红色 {bars[i]['up_ratio']:.1f}%",
                        f"{bars[i+1]['time']} 空白 {bars[i+1]['up_ratio']:.1f}%",
                        f"{bars[i+2]['time']} 空白 {bars[i+2]['up_ratio']:.1f}%",
                        f"{bars[i+3]['time']} 空白 {bars[i+3]['up_ratio']:.1f}%"
                    ],
                    'blank_ratio': f"{blank_ratio*100:.1f}%",
                    'detected_at': bars[i+3]['time']
                }
    
    return None


def save_detection_record(pattern_info):
    """保存检测记录"""
    try:
        beijing_time = get_beijing_time()
        date_str = beijing_time.strftime('%Y-%m-%d')
        
        record = {
            'timestamp': beijing_time.isoformat(),
            'time': beijing_time.strftime('%Y-%m-%d %H:%M:%S'),
            'date': date_str,
            **pattern_info
        }
        
        # 保存到JSONL文件
        record_file = DATA_DIR / f'detections_{date_str}.jsonl'
        with open(record_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        log(f"✅ 检测记录已保存: {record_file}")
        return True
        
    except Exception as e:
        log(f"❌ 保存记录失败: {e}")
        return False


def check_if_already_notified(pattern_info):
    """检查今天是否已经通知过相同的模式"""
    try:
        beijing_time = get_beijing_time()
        date_str = beijing_time.strftime('%Y-%m-%d')
        record_file = DATA_DIR / f'detections_{date_str}.jsonl'
        
        if not record_file.exists():
            return False
        
        with open(record_file, 'r', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line.strip())
                # 检查是否是相同的模式和时间点
                if (record.get('pattern') == pattern_info['pattern'] and
                    record.get('detected_at') == pattern_info['detected_at']):
                    return True
        
        return False
        
    except Exception as e:
        log(f"⚠️ 检查通知记录失败: {e}")
        return False


def send_pattern_notification(pattern_info, daily_prediction=None):
    """发送模式检测通知"""
    beijing_time = get_beijing_time()
    
    # 添加大周期信息
    daily_info = ""
    if daily_prediction:
        daily_info = f"\n📅 <b>大周期预判</b>: {daily_prediction.get('signal', '未知')}\n"
    
    if pattern_info['pattern'] == 'pattern_1':
        # 模式1: 诱多等待新低
        emoji = "📉" if "红→黄→绿" in pattern_info['pattern_type'] else "📈"
        message = (
            f"{emoji} <b>【日内模式检测】诱多等待新低</b>\n\n"
            f"⏰ 检测时间: {beijing_time.strftime('%H:%M:%S')}\n"
            f"📊 模式类型: {pattern_info['pattern_type']}\n"
            f"⚠️ 操作信号: <b>{pattern_info['signal']}</b>\n\n"
            f"📈 连续3根柱子:\n"
        )
        for bar in pattern_info['bars']:
            message += f"   {bar}\n"
        
        message += (
            daily_info +
            f"\n💡 <b>操作建议</b>:\n"
            f"   当前出现诱多信号，可能还有新低\n"
            f"   建议：逢高做空，等待更好入场点\n\n"
            f"🔗 查看详情: https://9002-iopxcqas7abbrajoi4k4x-2e77fc33.sandbox.novita.ai/coin-change-tracker"
        )
        
    elif pattern_info['pattern'] == 'pattern_2':
        # 模式2: 诱空试仓抄底
        message = (
            f"🟢 <b>【日内模式检测】诱空试仓抄底</b>\n\n"
            f"⏰ 检测时间: {beijing_time.strftime('%H:%M:%S')}\n"
            f"📊 模式: 红柱后连续3个空白柱子\n"
            f"⚠️ 操作信号: <b>{pattern_info['signal']}</b>\n\n"
            f"📈 检测到的柱子:\n"
        )
        for bar in pattern_info['bars']:
            message += f"   {bar}\n"
        
        message += (
            f"\n📊 空白占比: {pattern_info['blank_ratio']} (≤25%)\n" +
            daily_info +
            f"\n💡 <b>操作建议</b>:\n"
            f"   当前出现诱空信号，可以试仓抄底\n"
            f"   建议：小仓位开多单试仓\n\n"
            f"🔗 查看详情: https://9002-iopxcqas7abbrajoi4k4x-2e77fc33.sandbox.novita.ai/coin-change-tracker"
        )
        
    elif pattern_info['pattern'] == 'pattern_3':
        # 模式3: 筑底信号
        message = (
            f"🟡 <b>【日内模式检测】筑底信号</b>\n\n"
            f"⏰ 检测时间: {beijing_time.strftime('%H:%M:%S')}\n"
            f"📊 模式: {pattern_info['pattern_type']}\n"
            f"⚠️ 操作信号: <b>{pattern_info['signal']}</b>\n\n"
            f"📈 连续3根柱子:\n"
        )
        for bar in pattern_info['bars']:
            message += f"   {bar}\n"
        
        message += (
            daily_info +
            f"\n💡 <b>操作建议</b>:\n"
            f"   黄→绿→黄形态表明底部正在形成\n"
            f"   建议：逢低做多，分批建仓\n\n"
            f"🔗 查看详情: https://9002-iopxcqas7abbrajoi4k4x-2e77fc33.sandbox.novita.ai/coin-change-tracker"
        )
        
    else:  # pattern_4
        # 模式4: 诱空信号
        message = (
            f"🟢 <b>【日内模式检测】诱空信号</b>\n\n"
            f"⏰ 检测时间: {beijing_time.strftime('%H:%M:%S')}\n"
            f"📊 模式: {pattern_info['pattern_type']}\n"
            f"⚠️ 操作信号: <b>{pattern_info['signal']}</b>\n\n"
            f"📈 检测到的柱子:\n"
        )
        for bar in pattern_info['bars']:
            message += f"   {bar}\n"
        
        message += (
            daily_info +
            f"\n💡 <b>操作建议</b>:\n"
            f"   V型反转形态，诱空后快速拉升\n"
            f"   建议：逢低做多，把握反弹机会\n\n"
            f"🔗 查看详情: https://9002-iopxcqas7abbrajoi4k4x-2e77fc33.sandbox.novita.ai/coin-change-tracker"
        )
    
    return send_telegram_message(message)


def monitor_loop():
    """主监控循环"""
    log("="*80)
    log("🚀 日内模式监控器已启动")
    log(f"📊 监控时间段: {MONITOR_START_HOUR:02d}:00 - {MONITOR_END_HOUR:02d}:59 (北京时间)")
    log(f"🔍 检查间隔: {CHECK_INTERVAL}秒 ({CHECK_INTERVAL//60}分钟)")
    log(f"📁 数据目录: {DATA_DIR}")
    log("="*80 + "\n")
    
    while True:
        try:
            beijing_time = get_beijing_time()
            current_hour = beijing_time.hour
            
            # 检查是否在监控时间段内
            if not (MONITOR_START_HOUR <= current_hour <= MONITOR_END_HOUR):
                log(f"⏰ 当前时间 {current_hour:02d}:{beijing_time.minute:02d} 不在监控时间段内，等待...")
                time.sleep(CHECK_INTERVAL)
                continue
            
            log(f"\n{'='*80}")
            log(f"🔍 开始检查模式 [{beijing_time.strftime('%Y-%m-%d %H:%M:%S')}]")
            log(f"{'='*80}")
            
            # 获取今天的数据
            bars = fetch_today_data()
            if not bars:
                log("⚠️ 无法获取数据，跳过本次检查")
                time.sleep(CHECK_INTERVAL)
                continue
            
            log(f"📊 当前共有 {len(bars)} 个10分钟柱子")
            
            # 统计颜色分布
            color_counts = {'green': 0, 'yellow': 0, 'red': 0, 'blank': 0}
            for bar in bars:
                color_counts[bar['color']] += 1
            
            log(f"📈 颜色分布: 绿色{color_counts['green']}根, 黄色{color_counts['yellow']}根, "
                f"红色{color_counts['red']}根, 空白{color_counts['blank']}根")
            
            # 获取今日预判（大周期）
            daily_prediction = get_daily_prediction()
            
            # 计算当前涨跌幅总和（用于模式3）
            total_change = None
            if bars:
                try:
                    # 从API获取最新的total_change
                    beijing_time = get_beijing_time()
                    today_str = beijing_time.strftime('%Y-%m-%d')
                    url = f'{API_BASE}/api/coin-change-tracker/history?date={today_str}&limit=1'
                    response = requests.get(url, timeout=10)
                    result = response.json()
                    if result.get('success') and result.get('data'):
                        total_change = result['data'][0].get('total_change', 0)
                        log(f"📊 当前涨跌幅总和: {total_change:.2f}%")
                except Exception as e:
                    log(f"⚠️ 获取涨跌幅总和失败: {e}")
            
            # 检查所有模式
            patterns = [
                ('pattern_1', check_pattern_1(bars, daily_prediction)),
                ('pattern_2', check_pattern_2(bars)),
                ('pattern_3', check_pattern_3(bars, total_change)),
                ('pattern_4', check_pattern_4(bars))
            ]
            
            detected_any = False
            
            for pattern_id, pattern_info in patterns:
                if not pattern_info:
                    continue
                
                detected_any = True
                log(f"🎯 检测到{pattern_id.replace('_', '')}: {pattern_info['pattern_name']}")
                log(f"   类型: {pattern_info.get('pattern_type', 'N/A')}")
                log(f"   时间范围: {pattern_info['time_range']}")
                log(f"   信号: {pattern_info['signal']}")
                
                # 检查是否符合大周期方向（小周期服从大周期）
                signal_type = pattern_info.get('signal_type')
                if signal_type:
                    allowed, reason = is_signal_allowed(signal_type, daily_prediction, total_change)
                    if not allowed:
                        log(f"🚫 信号被大周期过滤: {reason}")
                        continue
                    else:
                        log(f"✅ 信号通过大周期检查: {reason}")
                
                # 检查是否已通知过
                if not check_if_already_notified(pattern_info):
                    # 发送通知
                    if send_pattern_notification(pattern_info, daily_prediction):
                        # 保存记录
                        save_detection_record(pattern_info)
                    else:
                        log("⚠️ 通知发送失败，不保存记录")
                else:
                    log("ℹ️ 今天已经通知过此模式，跳过")
            
            if not detected_any:
                log("✓ 未检测到特定模式")
            
            log(f"⏳ 等待 {CHECK_INTERVAL}秒后进行下次检查...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log("\n⏹️ 监控已停止")
            break
        except Exception as e:
            log(f"❌ 监控异常: {e}")
            import traceback
            traceback.print_exc()
            log(f"⏳ {CHECK_INTERVAL}秒后重试...")
            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    monitor_loop()
