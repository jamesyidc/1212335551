#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
波峰检测和假突破判断模块（状态机版）
按照 B确认 → A确认 → C确认 的严格顺序检测波峰
C点可以作为下一个波峰的B点复用
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from enum import Enum

class DetectionState(Enum):
    """波峰检测状态"""
    LOOKING_FOR_B = 1  # 寻找B点
    CONFIRMING_B = 2   # 确认B点（等待15分钟）
    LOOKING_FOR_A = 3  # 寻找A点
    CONFIRMING_A = 4   # 确认A点（等待15分钟）
    LOOKING_FOR_C = 5  # 寻找C点

class WavePeakDetector:
    """波峰检测器（状态机版）"""
    
    def __init__(self, min_amplitude: float = 35.0, window_minutes: int = 15):
        """
        初始化波峰检测器
        
        Args:
            min_amplitude: 最小振幅（B到A的涨跌幅差值），默认35%
            window_minutes: 确认窗口（分钟），点位需要在此窗口内保持极值才算确认，默认15分钟
        """
        self.min_amplitude = min_amplitude
        self.window_minutes = window_minutes
        self.data_dir = '/home/user/webapp/data/coin_change_tracker'
    
    def load_data(self, file_path: str) -> List[Dict]:
        """
        加载数据文件
        
        Args:
            file_path: 数据文件路径
            
        Returns:
            数据列表
        """
        if not os.path.exists(file_path):
            print(f"❌ 数据文件不存在: {file_path}")
            return []
        
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    
                    # 兼容旧格式：如果没有beijing_time字段，从timestamp字段生成
                    if 'beijing_time' not in record and 'timestamp' in record:
                        # timestamp格式：2026-02-01T09:12:25.698836+08:00
                        # 提取日期和时间部分
                        timestamp_str = record['timestamp']
                        # 去掉时区信息
                        if '+' in timestamp_str:
                            timestamp_str = timestamp_str.split('+')[0]
                        # 转换为beijing_time格式：2026-02-01 09:12:25
                        record['beijing_time'] = timestamp_str.replace('T', ' ').split('.')[0]
                    
                    data.append(record)
        
        return data
    
    def detect_wave_peaks(self, data: List[Dict]) -> tuple[List[Dict], Dict]:
        """
        检测波峰（B-A-C结构）- 状态机版本
        
        状态转换流程：
        1. LOOKING_FOR_B: 找到局部最低点 → CONFIRMING_B
        2. CONFIRMING_B: 等待15分钟确认
           - 期间出现更低点 → 回到 LOOKING_FOR_B
           - 15分钟后仍是最低 → B点确认 → LOOKING_FOR_A
        3. LOOKING_FOR_A: 找到局部最高点且振幅≥35% → CONFIRMING_A
        4. CONFIRMING_A: 等待15分钟确认
           - 期间出现更高点 → 回到 LOOKING_FOR_A
           - 15分钟后仍是最高 → A点确认 → LOOKING_FOR_C
        5. LOOKING_FOR_C: 找到回落>50%后反弹的点 → 记录波峰
           - C点成为下一个波峰的B点候选
        
        Args:
            data: 数据列表
            
        Returns:
            (波峰列表, 当前状态信息)
            - 波峰列表：已完成的波峰（有B、A、C三个点）
            - 当前状态：包含进行中的波峰信息（可能只有B，或只有B-A）
        """
        if len(data) < self.window_minutes * 3:
            return []
        
        wave_peaks = []
        state = DetectionState.LOOKING_FOR_B
        
        # 当前候选点
        b_candidate = None
        b_confirm_start_index = None
        
        a_candidate = None
        a_confirm_start_index = None
        
        # 从C点继承的B点（如果有）
        inherited_b = None
        
        i = 0
        while i < len(data):
            current_value = data[i]['total_change']
            
            # ==================== 状态1: 寻找B点 ====================
            if state == DetectionState.LOOKING_FOR_B:
                # 如果有从上一个波峰的C点继承的B点，直接使用
                if inherited_b is not None:
                    b_candidate = inherited_b
                    b_confirm_start_index = i
                    state = DetectionState.CONFIRMING_B
                    inherited_b = None  # 清除继承
                    print(f"📍 使用继承的B点: {b_candidate['beijing_time']} = {b_candidate['value']:.2f}%")
                # 否则寻找新的局部最低点
                elif i > 0 and current_value < data[i-1]['total_change']:
                    # 发现下降趋势，可能是B点候选
                    b_candidate = {
                        'index': i,
                        'timestamp': data[i]['timestamp'],
                        'beijing_time': data[i]['beijing_time'],
                        'value': current_value
                    }
                    b_confirm_start_index = i
                    state = DetectionState.CONFIRMING_B
                    print(f"🔍 发现B点候选: {b_candidate['beijing_time']} = {b_candidate['value']:.2f}%")
                
                i += 1
            
            # ==================== 状态2: 确认B点 ====================
            elif state == DetectionState.CONFIRMING_B:
                # 检查是否出现了更低点
                if current_value < b_candidate['value']:
                    print(f"⚠️  B点被推翻，发现更低点: {data[i]['beijing_time']} = {current_value:.2f}%")
                    # 重新设置B点候选
                    b_candidate = {
                        'index': i,
                        'timestamp': data[i]['timestamp'],
                        'beijing_time': data[i]['beijing_time'],
                        'value': current_value
                    }
                    b_confirm_start_index = i
                    print(f"🔍 新的B点候选: {b_candidate['beijing_time']} = {b_candidate['value']:.2f}%")
                
                # 检查是否已经过了确认窗口
                if i - b_confirm_start_index >= self.window_minutes:
                    # B点确认成功
                    print(f"✅ B点确认: {b_candidate['beijing_time']} = {b_candidate['value']:.2f}%")
                    a_candidate = None  # 重置A点候选
                    state = DetectionState.LOOKING_FOR_A
                
                i += 1
            
            # ==================== 状态3: 寻找A点 ====================
            elif state == DetectionState.LOOKING_FOR_A:
                # 确保A点在B点之后
                if i <= b_candidate['index']:
                    i += 1
                    continue
                
                # ⚠️ 检查是否出现了比B点更低的点，如果是，则放弃当前B点，重新寻找
                if current_value < b_candidate['value']:
                    print(f"⚠️  在寻找A点期间，发现比B点更低的点: {data[i]['beijing_time']} = {current_value:.2f}%")
                    print(f"   放弃当前B点，重新开始寻找B点")
                    state = DetectionState.LOOKING_FOR_B
                    b_candidate = None
                    a_candidate = None
                    # 不增加i，让下一轮循环处理这个新的低点
                    continue
                
                # 检查振幅是否满足要求
                amplitude = current_value - b_candidate['value']
                
                # 如果还没有A候选，或者当前值更高且振幅满足要求
                if a_candidate is None:
                    if amplitude >= self.min_amplitude:
                        a_candidate = {
                            'index': i,
                            'timestamp': data[i]['timestamp'],
                            'beijing_time': data[i]['beijing_time'],
                            'value': current_value
                        }
                        a_confirm_start_index = i
                        state = DetectionState.CONFIRMING_A
                        print(f"🔍 发现A点候选: {a_candidate['beijing_time']} = {a_candidate['value']:.2f}%, 振幅={amplitude:.2f}%")
                elif current_value > a_candidate['value'] and amplitude >= self.min_amplitude:
                    # 更新A候选
                    a_candidate = {
                        'index': i,
                        'timestamp': data[i]['timestamp'],
                        'beijing_time': data[i]['beijing_time'],
                        'value': current_value
                    }
                    a_confirm_start_index = i
                    print(f"🔄 更新A点候选: {a_candidate['beijing_time']} = {a_candidate['value']:.2f}%, 振幅={amplitude:.2f}%")
                
                i += 1
            
            # ==================== 状态4: 确认A点 ====================
            elif state == DetectionState.CONFIRMING_A:
                # ⚠️ 检查是否出现了比B点更低的点
                if current_value < b_candidate['value']:
                    print(f"⚠️  在确认A点期间，发现比B点更低的点: {data[i]['beijing_time']} = {current_value:.2f}%")
                    print(f"   放弃当前B点和A点，重新开始")
                    state = DetectionState.LOOKING_FOR_B
                    b_candidate = None
                    a_candidate = None
                    continue
                
                # 检查是否出现了更高点
                if current_value > a_candidate['value']:
                    # 检查新的高点振幅是否仍然满足
                    new_amplitude = current_value - b_candidate['value']
                    if new_amplitude >= self.min_amplitude:
                        print(f"⚠️  A点被推翻，发现更高点: {data[i]['beijing_time']} = {current_value:.2f}%")
                        a_candidate = {
                            'index': i,
                            'timestamp': data[i]['timestamp'],
                            'beijing_time': data[i]['beijing_time'],
                            'value': current_value
                        }
                        a_confirm_start_index = i
                        print(f"🔍 新的A点候选: {a_candidate['beijing_time']} = {a_candidate['value']:.2f}%, 振幅={new_amplitude:.2f}%")
                
                # 检查是否已经过了确认窗口
                if i - a_confirm_start_index >= self.window_minutes:
                    # A点确认成功
                    amplitude = a_candidate['value'] - b_candidate['value']
                    print(f"✅ A点确认: {a_candidate['beijing_time']} = {a_candidate['value']:.2f}%, 振幅={amplitude:.2f}%")
                    state = DetectionState.LOOKING_FOR_C
                
                i += 1
            
            # ==================== 状态5: 寻找C点 ====================
            elif state == DetectionState.LOOKING_FOR_C:
                # 确保C点在A点之后
                if i <= a_candidate['index']:
                    i += 1
                    continue
                
                # ⚠️ 关键逻辑：即使在寻找C点期间，如果出现更高点，A点也要更新！
                if current_value > a_candidate['value']:
                    new_amplitude = current_value - b_candidate['value']
                    if new_amplitude >= self.min_amplitude:
                        print(f"⚠️  在寻找C点期间，发现更高点！A点更新")
                        print(f"   旧A点: {a_candidate['beijing_time']} = {a_candidate['value']:.2f}%")
                        a_candidate = {
                            'index': i,
                            'timestamp': data[i]['timestamp'],
                            'beijing_time': data[i]['beijing_time'],
                            'value': current_value
                        }
                        print(f"   新A点: {a_candidate['beijing_time']} = {a_candidate['value']:.2f}%")
                        print(f"   新振幅: {new_amplitude:.2f}%")
                        i += 1
                        continue  # 继续寻找C点，但使用新的A点
                
                # 计算目标回落值（振幅的一半）
                amplitude = a_candidate['value'] - b_candidate['value']
                half_amplitude = amplitude / 2
                target_decline = a_candidate['value'] - half_amplitude
                
                # 检查是否已经回落超过一半
                if current_value <= target_decline:
                    # 检查是否止跌反弹
                    if i + 1 < len(data) and data[i + 1]['total_change'] > current_value:
                        # 找到C点，记录完整波峰
                        c_point = {
                            'index': i,
                            'timestamp': data[i]['timestamp'],
                            'beijing_time': data[i]['beijing_time'],
                            'value': current_value
                        }
                        
                        decline = a_candidate['value'] - c_point['value']
                        decline_ratio = (decline / amplitude) * 100
                        
                        wave_peak = {
                            'b_point': b_candidate,
                            'a_point': a_candidate,
                            'c_point': c_point,
                            'amplitude': amplitude,
                            'decline': decline,
                            'decline_ratio': decline_ratio
                        }
                        wave_peaks.append(wave_peak)
                        
                        print(f"✅ 完整波峰记录: B({b_candidate['value']:.2f}%) → A({a_candidate['value']:.2f}%) → C({c_point['value']:.2f}%)")
                        print(f"   振幅={amplitude:.2f}%, 回调={decline:.2f}% ({decline_ratio:.1f}%)")
                        
                        # C点作为下一个波峰的B点候选
                        inherited_b = c_point
                        print(f"♻️  C点将作为下一个波峰的B点候选")
                        
                        # 重置状态，开始寻找下一个波峰
                        state = DetectionState.LOOKING_FOR_B
                        b_candidate = None
                        a_candidate = None
                
                i += 1
        
        # 构建当前状态信息
        current_state = {
            'state': state.value if state else 'COMPLETED',
            'b_candidate': b_candidate if b_candidate else None,
            'a_candidate': a_candidate if a_candidate else None,
            'has_incomplete_peak': (b_candidate is not None or a_candidate is not None)
        }
        
        # 如果有B-A但没有C，说明有一个进行中的波峰
        if b_candidate and a_candidate and state == DetectionState.LOOKING_FOR_C:
            amplitude = a_candidate['value'] - b_candidate['value']
            current_state['incomplete_peak'] = {
                'b_point': b_candidate,
                'a_point': a_candidate,
                'amplitude': amplitude,
                'status': '等待C点形成'
            }
        
        return wave_peaks, current_state
    
    def detect_crash_warning(self, wave_peaks: List[Dict]) -> Optional[Dict]:
        """
        检测暴跌前兆信号
        
        支持四种模式：
        1. 情况8：暴跌幅度递增（最高优先级）
           - 连续3波：a1→b1 < a2→b2 < a3→b3
           - 连续4波（后3波）：a2→b2 < a3→b3 < a4→b4
        2. 顶部递减模式（A1 > A2 > A3）：反弹高点逐渐降低，上攻力量减弱
        3. 底部递增模式（A1 < A2 < A3）：反弹高点升高但处于下跌趋势
        
        扫描所有连续波峰的组合（不仅仅是最后几个）
        
        Args:
            wave_peaks: 波峰列表
            
        Returns:
            暴跌预警信号字典，如果没有暴跌前兆返回None
        """
        if len(wave_peaks) < 3:
            return None
        
        # 优先检测情况8：4个波峰的后3波递增（如果有至少4个波峰）
        if len(wave_peaks) >= 4:
            for i in range(len(wave_peaks) - 4, -1, -1):
                peak1 = wave_peaks[i]
                peak2 = wave_peaks[i + 1]
                peak3 = wave_peaks[i + 2]
                peak4 = wave_peaks[i + 3]
                
                a2 = peak2['a_point']['value']
                a3 = peak3['a_point']['value']
                a4 = peak4['a_point']['value']
                b2 = peak2['b_point']['value']
                b3 = peak3['b_point']['value']
                b4 = peak4['b_point']['value']
                
                # 计算后3波的暴跌幅度
                crash_amplitude_2 = abs(a2 - b2)
                crash_amplitude_3 = abs(a3 - b3)
                crash_amplitude_4 = abs(a4 - b4)
                
                # 情况8b：后3波暴跌幅度递增
                if (crash_amplitude_2 < crash_amplitude_3) and (crash_amplitude_3 < crash_amplitude_4):
                    peak_indices = f"{i+2}-{i+3}-{i+4}"
                    warning_msg = f'🚨🚨🚨 【情况8】极度危险！波峰{peak_indices}暴跌幅度递增，每次下跌力度在增强，即将暴跌！'
                    
                    return {
                        'signal_type': 'crash_warning_amplifying',
                        'pattern_name': '情况8：暴跌幅度递增（后3波）',
                        'consecutive_peaks': 3,
                        'peak_indices': peak_indices,
                        'warning_level': 'critical',
                        'warning': warning_msg,
                        'operation_tip': '逢高做空',
                        'peaks': [peak2, peak3, peak4],
                        'pattern': {
                            'crash_amplifying': True,
                            'description': '暴跌幅度递增：第2波跌幅 < 第3波跌幅 < 第4波跌幅'
                        },
                        'comparisons': {
                            'crash_amplitudes': {
                                'amplitude_2': crash_amplitude_2,
                                'amplitude_3': crash_amplitude_3,
                                'amplitude_4': crash_amplitude_4,
                                'amp3_vs_amp2': {
                                    'increase': crash_amplitude_3 > crash_amplitude_2,
                                    'diff': crash_amplitude_3 - crash_amplitude_2,
                                    'diff_pct': ((crash_amplitude_3 - crash_amplitude_2) / abs(crash_amplitude_2) * 100) if crash_amplitude_2 != 0 else 0
                                },
                                'amp4_vs_amp3': {
                                    'increase': crash_amplitude_4 > crash_amplitude_3,
                                    'diff': crash_amplitude_4 - crash_amplitude_3,
                                    'diff_pct': ((crash_amplitude_4 - crash_amplitude_3) / abs(crash_amplitude_3) * 100) if crash_amplitude_3 != 0 else 0
                                }
                            },
                            'a_values': {
                                'a2': a2,
                                'a3': a3,
                                'a4': a4
                            },
                            'b_values': {
                                'b2': b2,
                                'b3': b3,
                                'b4': b4
                            }
                        }
                    }
        
        # 扫描所有可能的连续3波组合，从最新到最旧
        # 如果有10个波峰，i的范围应该是7到0（即波峰8-10, 7-9, ..., 1-3）
        for i in range(len(wave_peaks) - 3, -1, -1):
            peak1 = wave_peaks[i]
            peak2 = wave_peaks[i + 1]
            peak3 = wave_peaks[i + 2]
            
            a1 = peak1['a_point']['value']
            a2 = peak2['a_point']['value']
            a3 = peak3['a_point']['value']
            
            # 检查B点是否也在下降（更强的暴跌信号）
            b1 = peak1['b_point']['value']
            b2 = peak2['b_point']['value']
            b3 = peak3['b_point']['value']
            
            # 如果有第4个波峰，也检测 A2 > A3 > A4 的模式
            if i + 3 < len(wave_peaks):
                peak4 = wave_peaks[i + 3]
                a4 = peak4['a_point']['value']
                b4 = peak4['b_point']['value']
                
                # 情况8b：A2 > A3 > A4（使用后3个波峰）
                if (a2 > a3) and (a3 > a4):
                    peak_indices_234 = f"{i+2}-{i+3}-{i+4}"
                    warning_msg = f'🚨 【情况8】暴跌预警！波峰{peak_indices_234} A点递减（A2 > A3 > A4），即将暴跌'
                    
                    return {
                        'signal_type': 'crash_warning_case8_a234',
                        'pattern_name': '情况8：暴跌预警（A2 > A3 > A4）',
                        'consecutive_peaks': 3,
                        'peak_indices': peak_indices_234,
                        'warning_level': 'critical',
                        'warning': warning_msg,
                        'operation_tip': '逢高做空',
                        'peaks': [peak2, peak3, peak4],
                        'pattern': {
                            'a_descending': True,
                            'description': '情况8：A点递减（A2 > A3 > A4），反弹高点逐渐降低，即将暴跌'
                        },
                        'comparisons': {
                            'a_values': {
                                'a2': a2,
                                'a3': a3,
                                'a4': a4,
                                'a3_vs_a2': {
                                    'decrease': a3 < a2,
                                    'diff': a3 - a2,
                                    'diff_pct': ((a3 - a2) / abs(a2) * 100) if a2 != 0 else 0
                                },
                                'a4_vs_a3': {
                                    'decrease': a4 < a3,
                                    'diff': a4 - a3,
                                    'diff_pct': ((a4 - a3) / abs(a3) * 100) if a3 != 0 else 0
                                }
                            },
                            'b_values': {
                                'b2': b2,
                                'b3': b3,
                                'b4': b4
                            }
                        }
                    }
            
            # 模式1：顶部递减（A1 > A2 > A3）- 反弹高点降低
            a_descending = (a1 > a2) and (a2 > a3)
            
            # 模式2：底部递增（A1 < A2 < A3）- 反弹高点升高
            a_ascending = (a1 < a2) and (a2 < a3)
            
            # 判断B点是否递减：B1 > B2 > B3（谷底越来越低）
            b_descending = (b1 > b2) and (b2 > b3)
            
            # 计算每个波峰的暴跌幅度（A点到B点的跌幅，取绝对值）
            # amplitude是B到A的涨幅，暴跌幅度就是A到下一个B的跌幅
            crash_amplitude_1 = abs(a1 - peak1['b_point']['value'])  # 第1波的暴跌幅度
            crash_amplitude_2 = abs(a2 - peak2['b_point']['value'])  # 第2波的暴跌幅度
            crash_amplitude_3 = abs(a3 - peak3['b_point']['value'])  # 第3波的暴跌幅度
            
            # 情况8：暴跌幅度递增 - 每次下跌力度在增强
            # 检测两种情况：
            # 1. a1→b1 < a2→b2 < a3→b3 (连续三波递增)
            # 2. a2→b2 < a3→b3 < a4→b4 (后三波递增)
            crash_amplifying = (crash_amplitude_1 < crash_amplitude_2) and (crash_amplitude_2 < crash_amplitude_3)
            
            # 找到符合条件的组合
            recent_peaks = [peak1, peak2, peak3]
            peak_indices = f"{i+1}-{i+2}-{i+3}"  # 波峰编号（从1开始）
            
            # 最优先检测：情况8 - 暴跌幅度递增（最危险的信号）
            if crash_amplifying:
                warning_level = 'critical'  # 最高级别预警
                warning_msg = f'🚨🚨🚨 【情况8】极度危险！波峰{peak_indices}暴跌幅度递增，每次下跌力度在增强，即将暴跌！'
                
                return {
                    'signal_type': 'crash_warning_amplifying',
                    'pattern_name': '情况8：暴跌幅度递增',
                    'consecutive_peaks': 3,
                    'peak_indices': peak_indices,
                    'warning_level': warning_level,
                    'warning': warning_msg,
                    'operation_tip': '逢高做空',
                    'peaks': recent_peaks,
                    'pattern': {
                        'crash_amplifying': crash_amplifying,
                        'description': '暴跌幅度递增：第1波跌幅 < 第2波跌幅 < 第3波跌幅'
                    },
                    'comparisons': {
                        'crash_amplitudes': {
                            'amplitude_1': crash_amplitude_1,
                            'amplitude_2': crash_amplitude_2,
                            'amplitude_3': crash_amplitude_3,
                            'amp2_vs_amp1': {
                                'increase': crash_amplitude_2 > crash_amplitude_1,
                                'diff': crash_amplitude_2 - crash_amplitude_1,
                                'diff_pct': ((crash_amplitude_2 - crash_amplitude_1) / abs(crash_amplitude_1) * 100) if crash_amplitude_1 != 0 else 0
                            },
                            'amp3_vs_amp2': {
                                'increase': crash_amplitude_3 > crash_amplitude_2,
                                'diff': crash_amplitude_3 - crash_amplitude_2,
                                'diff_pct': ((crash_amplitude_3 - crash_amplitude_2) / abs(crash_amplitude_2) * 100) if crash_amplitude_2 != 0 else 0
                            }
                        },
                        'a_values': {
                            'a1': a1,
                            'a2': a2,
                            'a3': a3
                        },
                        'b_values': {
                            'b1': b1,
                            'b2': b2,
                            'b3': b3
                        }
                    }
                }
            
            # 情况8优先检测：A点递减模式（A1 > A2 > A3）
            if a_descending:
                # 情况8：A1 > A2 > A3，反弹高点逐渐降低，即将暴跌
                warning_level = 'critical'
                warning_msg = f'🚨 【情况8】暴跌预警！波峰{peak_indices} A点递减（A1 > A2 > A3），即将暴跌'
                
                return {
                    'signal_type': 'crash_warning_case8_a123',
                    'pattern_name': '情况8：暴跌预警（A1 > A2 > A3）',
                    'consecutive_peaks': 3,
                    'peak_indices': peak_indices,
                    'warning_level': warning_level,
                    'warning': warning_msg,
                    'operation_tip': '逢高做空',
                    'peaks': recent_peaks,
                    'pattern': {
                        'a_descending': a_descending,
                        'b_descending': b_descending,
                        'description': '情况8：A点递减（A1 > A2 > A3），反弹高点逐渐降低，即将暴跌'
                    },
                    'comparisons': {
                        'a_values': {
                            'a1': a1,
                            'a2': a2,
                            'a3': a3,
                            'a2_vs_a1': {
                                'decrease': a2 < a1,
                                'diff': a2 - a1,
                                'diff_pct': ((a2 - a1) / abs(a1) * 100) if a1 != 0 else 0
                            },
                            'a3_vs_a2': {
                                'decrease': a3 < a2,
                                'diff': a3 - a2,
                                'diff_pct': ((a3 - a2) / abs(a2) * 100) if a2 != 0 else 0
                            }
                        },
                        'b_values': {
                            'b1': b1,
                            'b2': b2,
                            'b3': b3,
                            'b2_vs_b1': {
                                'decrease': b2 < b1,
                                'diff': b2 - b1,
                                'diff_pct': ((b2 - b1) / abs(b1) * 100) if b1 != 0 else 0
                            },
                            'b3_vs_b2': {
                                'decrease': b3 < b2,
                                'diff': b3 - b2,
                                'diff_pct': ((b3 - b2) / abs(b2) * 100) if b2 != 0 else 0
                            }
                        }
                    }
                }
            
            # 检测底部递增模式（次要信号）
            elif a_ascending:
                # 底部递增：A1 < A2 < A3，反弹高点升高但处于下跌趋势
                warning_level = 'high' if b_descending else 'medium'
                warning_msg = f'⚠️ 暴跌预警！波峰{peak_indices}连续反弹高点升高，但可能是下跌趋势中的反弹'
                
                if b_descending:
                    warning_msg = f'🚨 强烈暴跌预警！波峰{peak_indices}A点递增且B点递减，市场处于加速下跌趋势'
                
                return {
                    'signal_type': 'crash_warning_ascending',
                    'pattern_name': '底部递增模式',
                    'consecutive_peaks': 3,
                    'peak_indices': peak_indices,
                    'warning_level': warning_level,
                    'warning': warning_msg,
                    'peaks': recent_peaks,
                    'pattern': {
                        'a_ascending': a_ascending,
                        'b_descending': b_descending,
                        'description': 'A点递增（反弹高点升高）' + (' + B点递减（谷底下降）' if b_descending else '')
                    },
                    'comparisons': {
                        'a_values': {
                            'a1': a1,
                            'a2': a2,
                            'a3': a3,
                            'a2_vs_a1': {
                                'increase': a2 > a1,
                                'diff': a2 - a1,
                                'diff_pct': ((a2 - a1) / abs(a1) * 100) if a1 != 0 else 0
                            },
                            'a3_vs_a2': {
                                'increase': a3 > a2,
                                'diff': a3 - a2,
                                'diff_pct': ((a3 - a2) / abs(a2) * 100) if a2 != 0 else 0
                            }
                        },
                        'b_values': {
                            'b1': b1,
                            'b2': b2,
                            'b3': b3,
                            'b2_vs_b1': {
                                'decrease': b2 < b1,
                                'diff': b2 - b1,
                                'diff_pct': ((b2 - b1) / abs(b1) * 100) if b1 != 0 else 0
                            },
                            'b3_vs_b2': {
                                'decrease': b3 < b2,
                                'diff': b3 - b2,
                                'diff_pct': ((b3 - b2) / abs(b2) * 100) if b2 != 0 else 0
                            }
                        }
                    }
                }
        
        # 没有找到符合条件的连续3波组合
        return None
    def detect_false_breakout(self, wave_peaks: List[Dict]) -> Optional[Dict]:
        """
        检测假突破信号
        
        连续3个波峰的A点都没有突破第一个波峰的前高，判断为假突破
        
        Args:
            wave_peaks: 波峰列表
            
        Returns:
            假突破信号字典，如果没有假突破返回None
        """
        if len(wave_peaks) < 3:
            return None
        
        # 检查最近的3个波峰
        recent_peaks = wave_peaks[-3:]
        
        peak1 = recent_peaks[0]
        peak2 = recent_peaks[1]
        peak3 = recent_peaks[2]
        
        a1 = peak1['a_point']['value']
        a2 = peak2['a_point']['value']
        a3 = peak3['a_point']['value']
        
        # 判断A2是否突破A1
        a2_breaks_a1 = a2 > a1
        
        # 判断A3是否突破A1或A2
        a3_breaks_a1 = a3 > a1
        a3_breaks_a2 = a3 > a2
        a3_breaks_any = a3_breaks_a1 or a3_breaks_a2
        
        # 检查后续两个波峰是否都没有突破第一个波峰的高点
        if not a2_breaks_a1 and not a3_breaks_a1:
            return {
                'consecutive_peaks': 3,
                'reference_high': a1,
                'peaks': recent_peaks,
                'warning': '市场可能转跌，建议谨慎操作',
                # 添加详细的比较信息
                'comparisons': {
                    'a1': a1,
                    'a2': a2,
                    'a3': a3,
                    'a2_vs_a1': {
                        'breaks': a2_breaks_a1,
                        'diff': a2 - a1,
                        'diff_pct': ((a2 - a1) / abs(a1) * 100) if a1 != 0 else 0
                    },
                    'a3_vs_a1': {
                        'breaks': a3_breaks_a1,
                        'diff': a3 - a1,
                        'diff_pct': ((a3 - a1) / abs(a1) * 100) if a1 != 0 else 0
                    },
                    'a3_vs_a2': {
                        'breaks': a3_breaks_a2,
                        'diff': a3 - a2,
                        'diff_pct': ((a3 - a2) / abs(a2) * 100) if a2 != 0 else 0
                    },
                    'a3_breaks_any': a3_breaks_any
                }
            }
        
        return None

def main():
    """主函数 - 测试指定日期的数据"""
    from datetime import datetime
    import sys
    
    detector = WavePeakDetector(min_amplitude=35.0, window_minutes=15)
    
    # 从命令行参数获取日期，如果没有则使用今天
    if len(sys.argv) > 1:
        today = sys.argv[1]
    else:
        today = datetime.now().strftime('%Y%m%d')
    
    file_path = f'/home/user/webapp/data/coin_change_tracker/coin_change_{today}.jsonl'
    
    data = detector.load_data(file_path)
    
    print('=' * 80)
    print('📊 波峰检测分析（状态机版 - B→A→C严格顺序）')
    print('=' * 80)
    print(f"\n📅 日期: {today}")
    print(f"📈 数据点数: {len(data)}")
    print(f"⚙️  参数设置:")
    print(f"   - 最小振幅: {detector.min_amplitude}%")
    print(f"   - 确认窗口: {detector.window_minutes}分钟")
    print(f"\n🔄 检测逻辑:")
    print(f"   1. 先找到B点 → 等待15分钟确认")
    print(f"   2. B点确认后 → 开始找A点 → 等待15分钟确认")
    print(f"   3. A点确认后 → 开始找C点")
    print(f"   4. C点找到后 → 作为下一个波峰的B点候选")
    
    print(f"\n{'=' * 80}")
    print('🔍 开始检测...')
    print('=' * 80)
    
    # 检测波峰
    wave_peaks, current_state = detector.detect_wave_peaks(data)
    
    print(f"\n{'=' * 80}")
    print(f"🏔️  检测到波峰数: {len(wave_peaks)}")
    print('=' * 80)
    
    if len(wave_peaks) > 0:
        for i, peak in enumerate(wave_peaks, 1):
            print(f"\n波峰 {i}:")
            print(f"  B点（谷底）: {peak['b_point']['beijing_time']} | 涨跌幅: {peak['b_point']['value']:.2f}%")
            print(f"  A点（峰顶）: {peak['a_point']['beijing_time']} | 涨跌幅: {peak['a_point']['value']:.2f}%")
            print(f"  C点（回调）: {peak['c_point']['beijing_time']} | 涨跌幅: {peak['c_point']['value']:.2f}%")
            print(f"  振幅 (B→A): {peak['amplitude']:.2f}%")
            print(f"  回调 (A→C): {peak['decline']:.2f}% (占振幅 {peak['decline_ratio']:.1f}%)")
    
    # 显示进行中的波峰
    if current_state.get('incomplete_peak'):
        print(f"\n{'=' * 80}")
        print(f"⏳ 进行中的波峰")
        print('=' * 80)
        incomplete = current_state['incomplete_peak']
        print(f"\n  B点（谷底）: {incomplete['b_point']['beijing_time']} | 涨跌幅: {incomplete['b_point']['value']:.2f}%")
        print(f"  A点（峰顶）: {incomplete['a_point']['beijing_time']} | 涨跌幅: {incomplete['a_point']['value']:.2f}%")
        print(f"  C点（回调）: {incomplete['status']}")
        print(f"  振幅 (B→A): {incomplete['amplitude']:.2f}%")
        print(f"\n  💡 提示：A点已确认，正在等待价格回落超过50%振幅后反弹，形成C点")
    
    # 检测假突破
    false_breakout = detector.detect_false_breakout(wave_peaks)
    
    if false_breakout:
        print(f"\n{'=' * 80}")
        print('⚠️  假突破信号')
        print('=' * 80)
        
        print(f"\n🚨 检测到假突破：连续3个波峰的A点均未突破第一个波峰前高")
        print(f"\n参考高点: {false_breakout['reference_high']:.2f}%")
        print(f"\n连续3个波峰:")
        for i, peak in enumerate(false_breakout['peaks'], 1):
            print(f"  波峰{i} A点: {peak['a_point']['value']:.2f}% ({peak['a_point']['beijing_time']})")
        print(f"\n⚠️  {false_breakout['warning']}")
    else:
        print(f"\n✅ 暂无假突破信号")
    
    print(f"\n{'=' * 80}")

if __name__ == '__main__':
    main()
