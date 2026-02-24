#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日线级别暴跌预警监控
全天候监控，独立于0-2点预判
检测A点RSI总和连续递减模式：A1 > A2 > A3 或 A2 > A3 > A4
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 项目根目录
BASE_DIR = Path('/home/user/webapp')
sys.path.insert(0, str(BASE_DIR))

# 数据目录
WAVE_PEAKS_DIR = BASE_DIR / 'data' / 'coin_change_tracker' / 'wave_peaks'
WARNING_DIR = BASE_DIR / 'data' / 'daily_crash_warnings'
WARNING_DIR.mkdir(parents=True, exist_ok=True)

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def load_wave_peaks(date_str):
    """加载指定日期的波峰数据
    
    Args:
        date_str: YYYYMMDD格式
    
    Returns:
        波峰列表，按时间排序
    """
    file_path = WAVE_PEAKS_DIR / f'wave_peaks_{date_str}.json'
    if not file_path.exists():
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            peaks = data.get('peaks', [])
            # 按A点时间排序
            peaks.sort(key=lambda x: x.get('a_point', {}).get('beijing_time', ''))
            return peaks
    except Exception as e:
        print(f"⚠️ 加载波峰数据失败 {date_str}: {e}")
        return []

def get_recent_dates(days=5):
    """获取最近N天的日期列表（YYYYMMDD格式）"""
    beijing_now = get_beijing_time()
    dates = []
    for i in range(days):
        date = beijing_now - timedelta(days=i)
        dates.append(date.strftime('%Y%m%d'))
    return dates

def check_crash_warning_pattern(peaks):
    """检测暴跌预警模式：A点RSI总和连续递减
    
    检测两种模式：
    1. A1 > A2 > A3 (连续3个A点递减)
    2. A2 > A3 > A4 (后3个A点递减)
    
    Args:
        peaks: 完整波峰列表（至少需要3-4个完整波峰）
    
    Returns:
        预警信息字典，如果没有预警则返回None
    """
    if len(peaks) < 3:
        return None
    
    # 只使用完整的波峰（有A、B、C点）
    complete_peaks = [p for p in peaks if 'c_point' in p and p.get('c_point')]
    
    if len(complete_peaks) < 3:
        return None
    
    warnings = []
    
    # 检测所有可能的3连模式
    for i in range(len(complete_peaks) - 2):
        peak1, peak2, peak3 = complete_peaks[i], complete_peaks[i+1], complete_peaks[i+2]
        
        # 提取A点的RSI总和
        a1 = peak1.get('a_point', {}).get('rsi_sum', 0)
        a2 = peak2.get('a_point', {}).get('rsi_sum', 0)
        a3 = peak3.get('a_point', {}).get('rsi_sum', 0)
        
        # 如果没有RSI数据，使用value（总涨跌幅）
        if a1 == 0:
            a1 = peak1.get('a_point', {}).get('value', 0)
        if a2 == 0:
            a2 = peak2.get('a_point', {}).get('value', 0)
        if a3 == 0:
            a3 = peak3.get('a_point', {}).get('value', 0)
        
        # 检测递减模式：A1 > A2 > A3
        if (a1 > a2) and (a2 > a3):
            # 计算递减幅度
            decline_rate_12 = ((a1 - a2) / abs(a1)) * 100 if a1 != 0 else 0
            decline_rate_23 = ((a2 - a3) / abs(a2)) * 100 if a2 != 0 else 0
            
            warning = {
                'pattern_type': 'A点递减_3波',
                'peak_indices': f'{i+1}-{i+2}-{i+3}',
                'detection_time': get_beijing_time().strftime('%Y-%m-%d %H:%M:%S'),
                'warning_level': 'high',
                'signal': '即将暴跌',
                'operation_tip': '逢高做空',
                'peaks': [
                    {
                        'index': i+1,
                        'a_point_time': peak1.get('a_point', {}).get('beijing_time', ''),
                        'a_point_value': a1,
                        'label': 'A1'
                    },
                    {
                        'index': i+2,
                        'a_point_time': peak2.get('a_point', {}).get('beijing_time', ''),
                        'a_point_value': a2,
                        'label': 'A2'
                    },
                    {
                        'index': i+3,
                        'a_point_time': peak3.get('a_point', {}).get('beijing_time', ''),
                        'a_point_value': a3,
                        'label': 'A3'
                    }
                ],
                'comparisons': {
                    'A2_vs_A1': {
                        'values': f'{a2:.2f} vs {a1:.2f}',
                        'decline_rate': f'{decline_rate_12:.2f}%',
                        'is_declining': a2 < a1
                    },
                    'A3_vs_A2': {
                        'values': f'{a3:.2f} vs {a2:.2f}',
                        'decline_rate': f'{decline_rate_23:.2f}%',
                        'is_declining': a3 < a2
                    }
                },
                'description': f'连续3个A点RSI总和递减：A1({a1:.2f}) > A2({a2:.2f}) > A3({a3:.2f})',
                'warning_message': f'🚨 暴跌预警！连续3个A点递减，市场可能接跌'
            }
            
            warnings.append(warning)
    
    # 检测后3波模式（如果有4个以上完整波峰）
    if len(complete_peaks) >= 4:
        for i in range(1, len(complete_peaks) - 2):
            peak2, peak3, peak4 = complete_peaks[i], complete_peaks[i+1], complete_peaks[i+2]
            
            a2 = peak2.get('a_point', {}).get('rsi_sum', 0) or peak2.get('a_point', {}).get('value', 0)
            a3 = peak3.get('a_point', {}).get('rsi_sum', 0) or peak3.get('a_point', {}).get('value', 0)
            a4 = peak4.get('a_point', {}).get('rsi_sum', 0) or peak4.get('a_point', {}).get('value', 0)
            
            # 检测递减模式：A2 > A3 > A4
            if (a2 > a3) and (a3 > a4):
                decline_rate_23 = ((a2 - a3) / abs(a2)) * 100 if a2 != 0 else 0
                decline_rate_34 = ((a3 - a4) / abs(a3)) * 100 if a3 != 0 else 0
                
                warning = {
                    'pattern_type': 'A点递减_后3波',
                    'peak_indices': f'{i+1}-{i+2}-{i+3}',
                    'detection_time': get_beijing_time().strftime('%Y-%m-%d %H:%M:%S'),
                    'warning_level': 'high',
                    'signal': '即将暴跌',
                    'operation_tip': '逢高做空',
                    'peaks': [
                        {
                            'index': i+1,
                            'a_point_time': peak2.get('a_point', {}).get('beijing_time', ''),
                            'a_point_value': a2,
                            'label': 'A2'
                        },
                        {
                            'index': i+2,
                            'a_point_time': peak3.get('a_point', {}).get('beijing_time', ''),
                            'a_point_value': a3,
                            'label': 'A3'
                        },
                        {
                            'index': i+3,
                            'a_point_time': peak4.get('a_point', {}).get('beijing_time', ''),
                            'a_point_value': a4,
                            'label': 'A4'
                        }
                    ],
                    'comparisons': {
                        'A3_vs_A2': {
                            'values': f'{a3:.2f} vs {a2:.2f}',
                            'decline_rate': f'{decline_rate_23:.2f}%',
                            'is_declining': a3 < a2
                        },
                        'A4_vs_A3': {
                            'values': f'{a4:.2f} vs {a3:.2f}',
                            'decline_rate': f'{decline_rate_34:.2f}%',
                            'is_declining': a4 < a3
                        }
                    },
                    'description': f'后3个A点RSI总和递减：A2({a2:.2f}) > A3({a3:.2f}) > A4({a4:.2f})',
                    'warning_message': f'🚨 暴跌预警！后3个A点递减，市场可能接跌'
                }
                
                warnings.append(warning)
    
    return warnings if warnings else None

def save_warning(date_str, warnings):
    """保存预警信息到文件"""
    output_file = WARNING_DIR / f'crash_warning_{date_str}.json'
    
    data = {
        'date': date_str,
        'check_time': get_beijing_time().strftime('%Y-%m-%d %H:%M:%S'),
        'has_warning': bool(warnings),
        'warning_count': len(warnings) if warnings else 0,
        'warnings': warnings or []
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return output_file

def monitor_today():
    """监控今天的暴跌预警"""
    beijing_now = get_beijing_time()
    today_str = beijing_now.strftime('%Y%m%d')
    
    print(f"\n{'='*60}")
    print(f"🔍 日线级别暴跌预警监控")
    print(f"⏰ 检测时间: {beijing_now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 监控日期: {today_str}")
    print(f"{'='*60}\n")
    
    # 加载今天的波峰数据
    peaks = load_wave_peaks(today_str)
    
    if not peaks:
        print(f"⚠️ 今天暂无波峰数据")
        # 保存空预警
        save_warning(today_str, None)
        return None
    
    print(f"✅ 加载今天的波峰数据: {len(peaks)} 个波峰")
    
    # 检测完整波峰数量
    complete_peaks = [p for p in peaks if 'c_point' in p and p.get('c_point')]
    print(f"📊 完整波峰数量: {len(complete_peaks)} 个")
    
    if len(complete_peaks) < 3:
        print(f"⚠️ 完整波峰不足3个，无法检测暴跌预警")
        save_warning(today_str, None)
        return None
    
    # 检测暴跌预警模式
    warnings = check_crash_warning_pattern(peaks)
    
    if warnings:
        print(f"\n🚨 检测到 {len(warnings)} 个暴跌预警！\n")
        
        for i, warning in enumerate(warnings, 1):
            print(f"预警 {i}:")
            print(f"  类型: {warning['pattern_type']}")
            print(f"  波峰编号: {warning['peak_indices']}")
            print(f"  信号: {warning['signal']}")
            print(f"  操作建议: {warning['operation_tip']}")
            print(f"  描述: {warning['description']}")
            print(f"  {warning['warning_message']}\n")
            
            print(f"  A点数据:")
            for peak in warning['peaks']:
                print(f"    {peak['label']}: {peak['a_point_value']:.2f} @ {peak['a_point_time']}")
            
            print(f"\n  递减对比:")
            for key, comp in warning['comparisons'].items():
                status = "✅" if comp['is_declining'] else "❌"
                print(f"    {status} {key}: {comp['values']} (降幅: {comp['decline_rate']})")
            print()
        
        # 保存预警
        output_file = save_warning(today_str, warnings)
        print(f"💾 预警信息已保存到: {output_file.name}")
        
        return warnings
    else:
        print(f"✅ 暂无暴跌预警")
        save_warning(today_str, None)
        return None

def monitor_date(date_str):
    """监控指定日期的暴跌预警"""
    print(f"\n{'='*60}")
    print(f"🔍 日线级别暴跌预警监控")
    print(f"⏰ 检测时间: {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 监控日期: {date_str}")
    print(f"{'='*60}\n")
    
    # 加载指定日期的波峰数据
    peaks = load_wave_peaks(date_str)
    
    if not peaks:
        print(f"⚠️ {date_str} 暂无波峰数据")
        save_warning(date_str, None)
        return None
    
    print(f"✅ 加载波峰数据: {len(peaks)} 个波峰")
    
    # 检测完整波峰数量
    complete_peaks = [p for p in peaks if 'c_point' in p and p.get('c_point')]
    print(f"📊 完整波峰数量: {len(complete_peaks)} 个")
    
    if len(complete_peaks) < 3:
        print(f"⚠️ 完整波峰不足3个，无法检测暴跌预警")
        save_warning(date_str, None)
        return None
    
    # 检测暴跌预警模式
    warnings = check_crash_warning_pattern(peaks)
    
    if warnings:
        print(f"\n🚨 检测到 {len(warnings)} 个暴跌预警！\n")
        
        for i, warning in enumerate(warnings, 1):
            print(f"预警 {i}:")
            print(f"  类型: {warning['pattern_type']}")
            print(f"  波峰编号: {warning['peak_indices']}")
            print(f"  信号: {warning['signal']}")
            print(f"  操作建议: {warning['operation_tip']}")
            print(f"  描述: {warning['description']}")
            print(f"  {warning['warning_message']}\n")
            
            print(f"  A点数据:")
            for peak in warning['peaks']:
                print(f"    {peak['label']}: {peak['a_point_value']:.2f} @ {peak['a_point_time']}")
            
            print(f"\n  递减对比:")
            for key, comp in warning['comparisons'].items():
                status = "✅" if comp['is_declining'] else "❌"
                print(f"    {status} {key}: {comp['values']} (降幅: {comp['decline_rate']})")
            print()
        
        # 保存预警
        output_file = save_warning(date_str, warnings)
        print(f"💾 预警信息已保存到: {output_file.name}")
        
        return warnings
    else:
        print(f"✅ 暂无暴跌预警")
        save_warning(date_str, None)
        return None

def monitor_today():
    """监控今天的暴跌预警"""
    beijing_now = get_beijing_time()
    today_str = beijing_now.strftime('%Y%m%d')
    return monitor_date(today_str)


def main():
    """主函数"""
    try:
        # 支持命令行参数指定日期
        if len(sys.argv) > 1:
            date_str = sys.argv[1]
            warnings = monitor_date(date_str)
        else:
            warnings = monitor_today()
        
        if warnings:
            print(f"\n{'='*60}")
            print(f"🚨 预警总结: 检测到 {len(warnings)} 个暴跌预警信号")
            print(f"⚠️ 建议: 逢高做空，注意风险控制")
            print(f"{'='*60}\n")
            sys.exit(1)  # 有预警时返回非0退出码
        else:
            print(f"\n{'='*60}")
            print(f"✅ 监控完成: 暂无暴跌预警")
            print(f"{'='*60}\n")
            sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ 监控失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

if __name__ == '__main__':
    main()
