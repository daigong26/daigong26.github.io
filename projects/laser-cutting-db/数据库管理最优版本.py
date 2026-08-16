#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
激光切割数据库管理系统 v8.2
- 图层替代拐角策略（大/中/小，板材管材公用）
- 管材专用拐角工艺参数（13个字段）
- 打标自动使用小图层
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = r'C:\Users\Administrator\laser_cutting_master.db'

# ========== 简写映射表 ==========
MATERIAL_MAP = {
    '235': 'Q235', 'q235': 'Q235', 'Q235': 'Q235',
    '345': 'Q345', 'q345': 'Q345',
    '304': '304', '316': '316', '316l': '316L',
    '201': '201',
    '铝': '铝板', '铝板': '铝板', '铝5052': '5052铝板', '5052': '铝镁合金', '1060': '纯铝',
    '铜': '铜板', '黄铜': 'H62黄铜',
    '355': 'Q335B', 
    '420': 'Q420', 'q420': 'Q420',
    '235B': 'Q235B',
    '430': '铁素体不锈钢',
    '20#': '优质碳素钢', '45#': '优质碳素钢',
    '65Mn': '弹簧钢',
    '40Cr': '铬合金钢',
    'NM400': '耐磨钢', 'NM500': '耐磨钢',
}

NOZZLE_MAP = {
    '1': 'φ2.0单层', '单层2.0': 'φ2.0单层',
    '2': 'φ3.0单层', '单层3.0': 'φ3.0单层',
    '3': 'φ1.4双层', '双层1.4': 'φ1.4双层',
    '4': 'φ1.6双层', '双层1.6': 'φ1.6双层',
    '5': 'φ4.0单层', '单层4.0': 'φ4.0单层',
    '6': 'φ1.5单层', '单层1.5': 'φ1.5单层',
    '7': '坡口双层1.4',
    '8': '坡口双层1.6',
    '9': '坡口单层3.0',
    '10': '坡口双层1.8',
    '11': '坡口单层4.0',
    '12': 'φ1.2单层', '1.2': 'φ1.2单层', '单层': 'φ1.2单层', '单层1.2': 'φ1.2单层',
    '13': 'φ1.5双层', '1.5': 'φ1.5双层', '双层': 'φ1.5双层', '双层1.5': 'φ1.5双层',
    '14': 'φ2.0双层', '2.0': 'φ2.0双层', '双层2.0': 'φ2.0双层',
    '15': 'φ2.5双层', '2.5': 'φ2.5双层',
    '16': 'φ3.0三层', '3.0': 'φ3.0三层', '三层': 'φ3.0三层',
    '17': 'φ1.2双层', '双层1.2': 'φ1.2双层', 'φ1.2双层': 'φ1.2双层',
}

HEAD_MAP = {
    '1': 'BT240-F150', 'f150': 'BT240-F150', '150': 'BT240-F150',
    '2': 'BT240-F200', 'f200': 'BT240-F200', '200': 'BT240-F200',
    '3': 'Precitec-LightCutter', 'precitec': 'Precitec-LightCutter',
    '4': 'Precitec-ProCutter', 'procutter': 'Precitec-ProCutter',
}

LASER_MAP = {
    '1': '华俄型材-6000', 
    '2': '高能板材-12000', '高能': '高能板材-12000', '高能12000': '高能板材-12000',
    '3': '华俄型材-3000', 
    '4': '宏山型材-6000', 
    '5': '宏山坡口板材20000W',
}

ACCEL_MAP = {
    '0.5': '0.5G', '0.5g': '0.5G', '05': '0.5G',
    '1': '1.0G', '1.0': '1.0G', '1g': '1.0G',
    '1.5': '1.5G', '1.5g': '1.5G',
    '2': '2.0G', '2.0': '2.0G', '2g': '2.0G',
    '2.5': '2.5G', '2.5g': '2.5G',
    '3': '3.0G', '3.0': '3.0G', '3g': '3.0G',
}

# 图层映射表（大/中/小，板材管材公用，打标=小）
LAYER_MAP = {
    '1': '大', '大': '大', 'L': '大', 'large': '大',
    '2': '中', '中': '中', 'M': '中', 'medium': '中', '默认': '中',
    '3': '小', '小': '小', 'S': '小', 'small': '小', '打标': '小',
}

CONDITION_MAP = {
    '1': '净料', '净': '净料', '净板': '净料',
    '2': '浮锈', '锈': '浮锈', '浮锈': '浮锈',
    '3': '重锈', '重': '重锈',
    '4': '覆膜', '膜': '覆膜', '覆膜': '覆膜',
    '5': '油板', '油': '油板',
}

TEMP_MAP = {
    '1': '常温', '常': '常温',
    '2': '冬季', '冬': '冬季', '冷': '冬季',
    '3': '夏季', '夏': '夏季', '热': '夏季',
}

WARMUP_MAP = {
    '1': '冷机', '冷': '冷机',
    '2': '热机', '热': '热机',
}

GAS_MAP = {
    '1': '空气', '空': '空气', '空气': '空气',
    '2': '氧气', '氧': '氧气', '氧气': '氧气',
    '3': '氮气', '氮': '氮气', '氮气': '氮气',
    '4': '混合气', '混': '混合气', '混合': '混合气',
}

# ========== 字段定义（优化版）==========
FIELD_DEFS = {
    # 基础信息
    'workpiece_type': {'type': 'VARCHAR(10)', 'default': '板材', 'input': '工件类型', 'category': 'basic'},
    'material': {'type': 'VARCHAR(20)', 'default': 'Q235', 'input': '材质', 'category': 'basic'},
    'thickness_mm': {'type': 'DECIMAL(4,1)', 'default': 0, 'input': '厚度', 'category': 'basic'},
    'spec_note': {'type': 'VARCHAR(30)', 'default': '', 'input': '规格', 'category': 'basic'},
    
    # 设备信息
    'head_model': {'type': 'VARCHAR(30)', 'default': 'BT240-F200', 'input': '切割头', 'category': 'device'},
    'nozzle_spec': {'type': 'VARCHAR(20)', 'default': 'φ3.0单层', 'input': '喷嘴', 'category': 'device'},
    'laser_source': {'type': 'VARCHAR(20)', 'default': '高能板材-12000', 'input': '激光器', 'category': 'device'},
    'accel_g': {'type': 'VARCHAR(10)', 'default': '2.0G', 'input': '加速度', 'category': 'device'},
    
    # 环境状态
    'condition': {'type': 'VARCHAR(10)', 'default': '净料', 'input': '材料状态', 'category': 'env'},
    'temp_env': {'type': 'VARCHAR(10)', 'default': '常温', 'input': '环境温度', 'category': 'env'},
    'machine_warmup': {'type': 'VARCHAR(10)', 'default': '热机', 'input': '设备状态', 'category': 'env'},
    
    # 图层参数（替代原来的corner_strategy，大/中/小公用）
    'layer_size': {'type': 'VARCHAR(5)', 'default': '中', 'input': '图层大小', 'category': 'layer'},
    
    # 脉冲参数
    'pulse_freq_hz': {'type': 'INTEGER', 'default': 0, 'input': '脉冲频率Hz', 'category': 'pulse'},
    'pulse_duty_pct': {'type': 'INTEGER', 'default': 100, 'input': '占空比', 'category': 'pulse'},
    
    # 切割参数
    'power_actual_w': {'type': 'INTEGER', 'default': 0, 'input': '实际功率W', 'category': 'cut'},
    'speed_mm_min': {'type': 'INTEGER', 'default': 0, 'input': '速度mm/min', 'category': 'cut'},
    'gas_type': {'type': 'VARCHAR(10)', 'default': '空气', 'input': '气体', 'category': 'cut'},
    'pressure_mpa': {'type': 'DECIMAL(3,2)', 'default': 0, 'input': '气压MPa', 'category': 'cut'},
    'focus_mm': {'type': 'DECIMAL(4,2)', 'default': 0, 'input': '焦点mm', 'category': 'cut'},
    'nozzle_height_mm': {'type': 'DECIMAL(3,2)', 'default': 0, 'input': '割嘴高度mm', 'category': 'cut'},
    
    # 穿孔1参数（8个字段，默认None）
    'pierce_s1_power_pct': {'type': 'INTEGER', 'default': None, 'input': '穿孔1功率', 'category': 'pierce1'},
    'pierce_s1_time_ms': {'type': 'INTEGER', 'default': None, 'input': '穿孔1时间', 'category': 'pierce1'},
    'pierce_s1_height_mm': {'type': 'DECIMAL(4,2)', 'default': None, 'input': '穿孔1高度', 'category': 'pierce1'},
    'pierce_s1_freq_hz': {'type': 'INTEGER', 'default': None, 'input': '穿孔1频率', 'category': 'pierce1'},
    'pierce_s1_duty_pct': {'type': 'INTEGER', 'default': None, 'input': '穿孔1占空比', 'category': 'pierce1'},
    'pierce_s1_pressure_mpa': {'type': 'DECIMAL(3,2)', 'default': None, 'input': '穿孔1气压', 'category': 'pierce1'},
    'pierce_s1_focus_mm': {'type': 'DECIMAL(4,2)', 'default': None, 'input': '穿孔1焦点', 'category': 'pierce1'},
    'pierce_s1_accel_g': {'type': 'VARCHAR(10)', 'default': None, 'input': '穿孔1加速度', 'category': 'pierce1'},
    
    # 穿孔2参数（8个字段，默认None）
    'pierce_s2_power_pct': {'type': 'INTEGER', 'default': None, 'input': '穿孔2功率', 'category': 'pierce2'},
    'pierce_s2_time_ms': {'type': 'INTEGER', 'default': None, 'input': '穿孔2时间', 'category': 'pierce2'},
    'pierce_s2_height_mm': {'type': 'DECIMAL(4,2)', 'default': None, 'input': '穿孔2高度', 'category': 'pierce2'},
    'pierce_s2_freq_hz': {'type': 'INTEGER', 'default': None, 'input': '穿孔2频率', 'category': 'pierce2'},
    'pierce_s2_duty_pct': {'type': 'INTEGER', 'default': None, 'input': '穿孔2占空比', 'category': 'pierce2'},
    'pierce_s2_pressure_mpa': {'type': 'DECIMAL(3,2)', 'default': None, 'input': '穿孔2气压', 'category': 'pierce2'},
    'pierce_s2_focus_mm': {'type': 'DECIMAL(4,2)', 'default': None, 'input': '穿孔2焦点', 'category': 'pierce2'},
    'pierce_s2_accel_g': {'type': 'VARCHAR(10)', 'default': None, 'input': '穿孔2加速度', 'category': 'pierce2'},
    
    # 穿孔3参数（8个字段，默认None）
    'pierce_s3_power_pct': {'type': 'INTEGER', 'default': None, 'input': '穿孔3功率', 'category': 'pierce3'},
    'pierce_s3_time_ms': {'type': 'INTEGER', 'default': None, 'input': '穿孔3时间', 'category': 'pierce3'},
    'pierce_s3_height_mm': {'type': 'DECIMAL(4,2)', 'default': None, 'input': '穿孔3高度', 'category': 'pierce3'},
    'pierce_s3_freq_hz': {'type': 'INTEGER', 'default': None, 'input': '穿孔3频率', 'category': 'pierce3'},
    'pierce_s3_duty_pct': {'type': 'INTEGER', 'default': None, 'input': '穿孔3占空比', 'category': 'pierce3'},
    'pierce_s3_pressure_mpa': {'type': 'DECIMAL(3,2)', 'default': None, 'input': '穿孔3气压', 'category': 'pierce3'},
    'pierce_s3_focus_mm': {'type': 'DECIMAL(4,2)', 'default': None, 'input': '穿孔3焦点', 'category': 'pierce3'},
    'pierce_s3_accel_g': {'type': 'VARCHAR(10)', 'default': None, 'input': '穿孔3加速度', 'category': 'pierce3'},
    
    # 管材拐角工艺（13个字段，仅管材显示）
    'tube_corner_enable': {'type': 'VARCHAR(5)', 'default': '开启', 'input': '启用管拐角工艺', 'category': 'tube_corner'},
    'tube_corner_height_offset': {'type': 'DECIMAL(3,2)', 'default': 1.5, 'input': '拐角高度修正mm', 'category': 'tube_corner'},
    'tube_corner_pressure': {'type': 'DECIMAL(3,2)', 'default': 5.0, 'input': '拐角气压BAR', 'category': 'tube_corner'},
    'tube_corner_duty': {'type': 'INTEGER', 'default': 8, 'input': '拐角占空比%', 'category': 'tube_corner'},
    'tube_corner_freq': {'type': 'INTEGER', 'default': 1000, 'input': '拐角频率Hz', 'category': 'tube_corner'},
    'tube_corner_threshold': {'type': 'DECIMAL(4,3)', 'default': 1.146, 'input': '拐角判定标准°/mm', 'category': 'tube_corner'},
    'tube_r_corner_enable': {'type': 'VARCHAR(5)', 'default': '关闭', 'input': '使用R角修正', 'category': 'tube_corner'},
    'tube_r_ab': {'type': 'INTEGER', 'default': 3, 'input': 'AB面R角mm', 'category': 'tube_corner'},
    'tube_r_bc': {'type': 'INTEGER', 'default': 3, 'input': 'BC面R角mm', 'category': 'tube_corner'},
    'tube_r_cd': {'type': 'INTEGER', 'default': 3, 'input': 'CD面R角mm', 'category': 'tube_corner'},
    'tube_r_da': {'type': 'INTEGER', 'default': 3, 'input': 'DA面R角mm', 'category': 'tube_corner'},
    'tube_b_axis_limit': {'type': 'VARCHAR(5)', 'default': '关闭', 'input': '启用B轴限速', 'category': 'tube_corner'},
    'tube_b_speed': {'type': 'INTEGER', 'default': 1, 'input': 'B轴速度RPM', 'category': 'tube_corner'},
    'tube_b_accel': {'type': 'INTEGER', 'default': 1, 'input': 'B轴加速度rad/s²', 'category': 'tube_corner'},
    
    # 其他
    'quality_rating': {'type': 'INTEGER', 'default': None, 'input': '质量评级', 'category': 'other'},
    'verified_count': {'type': 'INTEGER', 'default': 1, 'input': '验证次数', 'category': 'other'},
    'last_used_date': {'type': 'TIMESTAMP', 'default': None, 'input': '最后使用', 'category': 'other'},
    'notes': {'type': 'TEXT', 'default': '', 'input': '备注', 'category': 'other'},
    'created_date': {'type': 'TIMESTAMP', 'default': 'CURRENT_TIMESTAMP', 'input': '创建时间', 'category': 'other'},
}

# 自动计算字段信息
FIELD_NAMES = list(FIELD_DEFS.keys())
FIELD_COUNT = len(FIELD_NAMES)
TUBE_CORNER_FIELDS = [k for k in FIELD_NAMES if 'tube_' in k]

print(f"✓ 已定义 {FIELD_COUNT} 个字段")
print(f"  - 图层参数: 1个（大/中/小公用）")
print(f"  - 管材拐角: {len(TUBE_CORNER_FIELDS)}个字段")
# ========== 安全输入函数 ==========
def safe_int(prompt, default=0):
    val = input(prompt).strip()
    return int(val) if val and val.isdigit() else default

def safe_float(prompt, default=0.0):
    val = input(prompt).strip()
    try:
        return float(val) if val else default
    except:
        return default

def select_option(prompt, options_map, default_key='1'):
    """选项选择"""
    print(f"\n{prompt}")
    shown = set()
    for k in sorted([k for k in options_map.keys() if k.isdigit()], key=int):
        v = options_map[k]
        if v not in shown:
            print(f"  {k}. {v}")
            shown.add(v)
    print(f"  [回车=默认: {options_map.get(default_key)}]")
    
    val = input("选择: ").strip().lower()
    if not val:
        val = default_key
    
    result = options_map.get(val, options_map.get(default_key))
    print(f"  → {result}")
    return result

def parse_material(val):
    """解析材质简写"""
    val = val.strip().lower()
    return MATERIAL_MAP.get(val, val.upper() if val else 'Q235')

def parse_spec(workpiece_type, val):
    """解析规格简写"""
    val = val.strip().upper().replace('X', 'x').replace('*', 'x')
    
    if workpiece_type == '管材':
        if val.startswith('D'):
            return val
        elif 'x' in val:
            parts = val.split('x')
            if len(parts) == 2:
                return f"{parts[0]}x{parts[1]}"
            elif len(parts) == 3:
                return f"{parts[0]}x{parts[1]}x{parts[2]}"
    elif workpiece_type == '型材':
        if 'x' in val:
            return val
        elif '角' in val or '槽' in val or 'H' in val:
            return val
    return val

# ========== SQL自动生成函数 ==========
def build_create_table_sql():
    """根据FIELD_DEFS自动生成CREATE TABLE语句"""
    fields_sql = []
    for name, info in FIELD_DEFS.items():
        default = info['default']
        if default is None:
            default_str = ''
        elif isinstance(default, str):
            if default == 'CURRENT_TIMESTAMP':
                default_str = " DEFAULT CURRENT_TIMESTAMP"
            else:
                default_str = f" DEFAULT '{default}'"
        else:
            default_str = f" DEFAULT {default}"
        fields_sql.append(f"            {name} {info['type']}{default_str}")
    
    return f"""CREATE TABLE IF NOT EXISTS material_process (
            process_id INTEGER PRIMARY KEY AUTOINCREMENT,
{','.join(fields_sql)},
            UNIQUE(workpiece_type, material, thickness_mm, spec_note,
                   head_model, nozzle_spec, laser_source, 
                   condition, temp_env, machine_warmup,
                   layer_size, pulse_freq_hz)
        );"""

def build_insert_sql():
    """自动生成INSERT语句"""
    fields = list(FIELD_DEFS.keys())
    placeholders = ', '.join(['?'] * len(fields))
    return f"""INSERT INTO material_process 
            ({', '.join(fields)})
            VALUES ({placeholders})"""

def build_update_sql():
    """自动生成UPDATE语句"""
    fields = [f"{k}=?" for k in FIELD_DEFS.keys()]
    return f"""UPDATE material_process SET 
            {', '.join(fields)}
            WHERE process_id=?"""

def get_field_index(field_name):
    """获取字段在查询结果中的索引"""
    try:
        return 1 + FIELD_NAMES.index(field_name)  # +1因为process_id是0
    except ValueError:
        return -1

print(f"✓ SQL生成函数已加载（{FIELD_COUNT}个字段）")

# ========== 数据库初始化 ==========
def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    
    conn.executescript(f"""
        {build_create_table_sql()};

        CREATE TABLE IF NOT EXISTS remnant_inventory (
            remnant_id VARCHAR(20) PRIMARY KEY,
            material_type VARCHAR(20),
            thickness_mm DECIMAL(4,1),
            length_mm INTEGER,
            width_mm INTEGER,
            area_mm2 INTEGER GENERATED ALWAYS AS (length_mm * width_mm) STORED,
            location_zone VARCHAR(20),
            location_shelf VARCHAR(20),
            location_layer INTEGER,
            status VARCHAR(10) DEFAULT 'available',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS part_history (
            part_id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_name VARCHAR(50),
            part_number VARCHAR(50),
            material_type VARCHAR(20),
            thickness_mm DECIMAL(4,1),
            workpiece_type VARCHAR(10),
            total_quantity_cut INTEGER DEFAULT 0,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS cut_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id VARCHAR(20),
            part_id INTEGER,
            process_id INTEGER,
            actual_power_w INTEGER,
            actual_speed_mm_min INTEGER,
            cut_start_time TIMESTAMP,
            actual_quantity INTEGER,
            quality_check_result VARCHAR(10)
        );
    """)
    
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")

# ========== 核心功能：录入工艺参数（智能区分板材/管材）==========
def add_process_interactive():
    """录入工艺参数"""
    print("\n" + "="*70)
    print("🔧 录入新工艺参数")
    print("="*70)
    
    # 初始化数据：必填字段用默认值，穿孔/管材字段用None
    data = {}
    for k, v in FIELD_DEFS.items():
        if v['category'] in ['pierce1', 'pierce2', 'pierce3', 'tube_corner']:
            data[k] = None  # 可选字段默认None
        else:
            data[k] = v['default']  # 必填字段用默认值
    
    # 工件类型
    print("\n【工件类型】")
    print("  1. 板材  2. 管材  3. 型材")
    t = input("选择[1]: ").strip()
    data['workpiece_type'] = {'2': '管材', '3': '型材'}.get(t, '板材')
    print(f"  → {data['workpiece_type']}")
    
    # 材质
    print("\n【材质】简写: 235=Q235")
    m = input("材质[Q235]: ").strip().lower()
    data['material'] = parse_material(m)
    
    # 厚度
    data['thickness_mm'] = safe_float("厚度/壁厚mm[0]: ", 0)
    
    # 规格
    data['spec_note'] = ""
    if data['workpiece_type'] == '管材':
        print("\n【规格】格式: D100x5, 100x5, 80x60x5")
    elif data['workpiece_type'] == '型材':
        print("\n【规格】格式: 63x63x6角钢, 10槽钢, H200x100")
    s = input("规格: ").strip()
    if s:
        data['spec_note'] = parse_spec(data['workpiece_type'], s)
    
    # 查重
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT process_id, power_actual_w, speed_mm_min, verified_count, notes
        FROM material_process
        WHERE workpiece_type=? AND material=? AND thickness_mm=? AND spec_note=?
    """, (data['workpiece_type'], data['material'], data['thickness_mm'], data['spec_note']))
    existing = cursor.fetchone()
    
    if existing:
        print(f"\n⚠️ 已有记录: ID={existing[0]}, {existing[1]}W/{existing[2]}mm/min, 验证{existing[3]}次")
        print("  选项: [U]更新 [S]跳过 [D]删除旧记录再新建")
        choice = input("选择[U]: ").strip().upper() or 'U'
        if choice == 'S':
            conn.close()
            return
        elif choice == 'D':
            conn.execute("DELETE FROM material_process WHERE process_id=?", (existing[0],))
            print(f"✓ 已删除旧记录 ID={existing[0]}")
        else:  # U - 更新
            conn.close()
            modify_process(existing[0])
            return
    
    # 设备选择
    data['head_model'] = select_option("【切割头】", HEAD_MAP, '2')
    data['nozzle_spec'] = select_option("【喷嘴】", NOZZLE_MAP, '2')
    data['laser_source'] = select_option("【激光器】", LASER_MAP, '2')
    data['accel_g'] = select_option("【加速度】", ACCEL_MAP, '3')
    
    # 环境
    data['condition'] = select_option("【材料状态】", CONDITION_MAP, '1')
    data['temp_env'] = select_option("【环境温度】", TEMP_MAP, '1')
    data['machine_warmup'] = select_option("【设备状态】", WARMUP_MAP, '2')
    
    # 图层（大/中/小公用，打标=小）
    if data['workpiece_type'] == '板材':
        data['layer_size'] = select_option("【图层】大=厚板/中=常规/小=薄板/打标", LAYER_MAP, '2')
    else:  # 管材/型材
        data['layer_size'] = select_option("【图层】大=大管/中=常规/小=小管/打标", LAYER_MAP, '2')
    
    # 脉冲
    print("\n【脉冲】回车=连续波")
    data['pulse_freq_hz'] = safe_int("脉冲频率Hz[0]: ", 0)
    data['pulse_duty_pct'] = safe_int("占空比%[100]: ", 100) if data['pulse_freq_hz'] > 0 else 100
    
    # 切割参数
    print("\n【切割参数】")
    data['power_actual_w'] = safe_int("实际功率W[0]: ", 0)
    data['speed_mm_min'] = safe_int("速度mm/min[0]: ", 0)
    data['gas_type'] = select_option("【气体】", GAS_MAP, '1')
    data['pressure_mpa'] = safe_float("气压MPa[0]: ", 0)
    data['focus_mm'] = safe_float("焦点mm[0]: ", 0)
    data['nozzle_height_mm'] = safe_float("割嘴高度mm[0]: ", 0)
    
    # 穿孔（只有用户输入了才保存）
    print("\n【多级穿孔】厚板填写，薄板回车跳过")
    for i in range(1, 4):
        print(f"\n第{i}级（功率回车=跳过）:")
        p = safe_int("  功率%: ", 0)
        if p == 0:
            break  # 跳过，保持None
        
        prefix = f'pierce_s{i}_'
        data[f'{prefix}power_pct'] = p
        data[f'{prefix}time_ms'] = safe_int("  时间ms: ", 0)
        data[f'{prefix}height_mm'] = safe_float("  高度mm: ", 0)
        data[f'{prefix}freq_hz'] = safe_int("  频率Hz[0]: ", 0)
        data[f'{prefix}duty_pct'] = safe_int("  占空比%[100]: ", 100) if data[f'{prefix}freq_hz'] > 0 else 100
        data[f'{prefix}pressure_mpa'] = safe_float("  气压MPa[0]: ", 0)
        data[f'{prefix}focus_mm'] = safe_float("  焦点mm[0]: ", 0)
        data[f'{prefix}accel_g'] = select_option(f"  【加速度】", ACCEL_MAP, '3')
    
    # 管材拐角工艺（仅管材/型材显示）
    if data['workpiece_type'] in ['管材', '型材']:
        print("\n【管材拐角工艺】")
        data['tube_corner_enable'] = select_option("【启用管拐角】", {'1': '开启', '2': '关闭'}, '1')
        
        if data['tube_corner_enable'] == '开启':
            data['tube_corner_height_offset'] = safe_float("拐角高度修正mm[1.5]: ", 1.5)
            data['tube_corner_pressure'] = safe_float("拐角气压BAR[5.0]: ", 5.0)
            data['tube_corner_duty'] = safe_int("拐角占空比%[8]: ", 8)
            data['tube_corner_freq'] = safe_int("拐角频率Hz[1000]: ", 1000)
            data['tube_corner_threshold'] = safe_float("拐角判定标准°/mm[1.146]: ", 1.146)
            
            data['tube_r_corner_enable'] = select_option("【使用R角修正】", {'1': '开启', '2': '关闭'}, '2')
            if data['tube_r_corner_enable'] == '开启':
                data['tube_r_ab'] = safe_int("AB面R角mm[3]: ", 3)
                data['tube_r_bc'] = safe_int("BC面R角mm[3]: ", 3)
                data['tube_r_cd'] = safe_int("CD面R角mm[3]: ", 3)
                data['tube_r_da'] = safe_int("DA面R角mm[3]: ", 3)
            
            data['tube_b_axis_limit'] = select_option("【启用B轴限速】", {'1': '开启', '2': '关闭'}, '2')
            if data['tube_b_axis_limit'] == '开启':
                data['tube_b_speed'] = safe_int("B轴速度RPM[1]: ", 1)
                data['tube_b_accel'] = safe_int("B轴加速度rad/s²[1]: ", 1)
    
    data['notes'] = input("\n经验备注: ").strip()
    
    # 保存
    try:
        sql = build_insert_sql()
        params = tuple(data.values())
        conn.execute(sql, params)
        conn.commit()
        print(f"\n✅ 已保存: {data['workpiece_type']} {data['material']} {data['thickness_mm']}mm 图层:{data['layer_size']}")
        print(f"   {data['power_actual_w']}W/{data['speed_mm_min']}mm/min | 验证:1")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
# ========== 修改工艺参数 ==========
def modify_process(process_id):
    """修改指定ID的工艺参数"""
    conn = sqlite3.connect(DB_PATH)
    
    cursor = conn.execute("SELECT * FROM material_process WHERE process_id=?", (process_id,))
    result = cursor.fetchone()
    if not result:
        print("❌ 记录不存在")
        conn.close()
        return
    
    # 构建字段索引
    idx = {name: i for i, name in enumerate(['process_id'] + FIELD_NAMES)}
    
    print(f"\n🔧 修改工艺参数 ID={process_id}")
    print(f"当前: {result[idx['workpiece_type']]} {result[idx['material']]} {result[idx['thickness_mm']]}mm 图层:{result[idx['layer_size']]}")
    
    # 初始化数据
    data = {}
    for k, v in FIELD_DEFS.items():
        val = result[idx[k]]
        data[k] = val if val is not None else (None if v['category'] in ['pierce1', 'pierce2', 'pierce3', 'tube_corner'] else v['default'])
    
    # 逐项修改
    print("\n【逐项修改】回车=保持原值")
    
    print(f"\n当前材质: {data['material']}")
    m = input("新材质: ").strip().lower()
    if m:
        data['material'] = parse_material(m)
    
    print(f"\n当前厚度: {data['thickness_mm']}")
    t = input("新厚度: ").strip()
    if t:
        data['thickness_mm'] = float(t)
    
    print(f"\n当前图层: {data['layer_size']}")
    l = input("新图层[大/中/小]: ").strip()
    if l in ['大', '中', '小']:
        data['layer_size'] = l
    
    print(f"\n当前功率: {data['power_actual_w']}W")
    p = input("新功率W: ").strip()
    if p:
        data['power_actual_w'] = int(p)
    
    print(f"\n当前速度: {data['speed_mm_min']}mm/min")
    s = input("新速度: ").strip()
    if s:
        data['speed_mm_min'] = int(s)
    
    # 管材可修改拐角参数
    if data['workpiece_type'] in ['管材', '型材'] and data['tube_corner_enable'] == '开启':
        print(f"\n当前拐角高度修正: {data['tube_corner_height_offset']}mm")
        h = input("新高度修正: ").strip()
        if h:
            data['tube_corner_height_offset'] = float(h)
    
    # 保存
    try:
        sql = build_update_sql()
        params = tuple(data.values()) + (process_id,)
        conn.execute(sql, params)
        conn.execute("UPDATE material_process SET last_used_date=CURRENT_TIMESTAMP WHERE process_id=?", (process_id,))
        conn.commit()
        print(f"\n✅ 已更新 ID={process_id}")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

# ========== 删除工艺参数 ==========
def delete_process(process_id, conn=None):
    """删除指定ID的工艺参数"""
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        close_conn = True
    
    try:
        cursor = conn.execute("SELECT workpiece_type, material, thickness_mm, layer_size FROM material_process WHERE process_id=?", (process_id,))
        result = cursor.fetchone()
        if not result:
            print("❌ 记录不存在")
            return False
        
        print(f"\n即将删除: {result[0]} {result[1]} {result[2]}mm 图层:{result[3]} (ID={process_id})")
        confirm = input("确认删除? [y/N]: ").strip().lower()
        
        if confirm == 'y':
            conn.execute("DELETE FROM material_process WHERE process_id=?", (process_id,))
            if close_conn:
                conn.commit()
            print(f"✅ 已删除 ID={process_id}")
            return True
        else:
            print("已取消")
            return False
            
    except Exception as e:
        print(f"❌ 删除错误: {e}")
        return False
    finally:
        if close_conn:
            conn.close()
# ========== 查询工艺参数（带删除/修改/图层显示）==========
def query_process():
    """查询工艺参数"""
    try:
        print("\n【查询条件】")
        print("  1. 板材  2. 管材  3. 型材")
        t = input("选择[1]: ").strip()
        workpiece_type = {'2': '管材', '3': '型材'}.get(t, '板材')
        
        print("\n材质简写: 235/304/铝...")
        m = input("材质[Q235]: ").strip().lower()
        material = parse_material(m)
        
        thickness = safe_float("厚度mm[0]: ", 0)
        
        # 规格
        spec_note = None
        if workpiece_type in ['管材', '型材']:
            s = input("规格(回车匹配所有): ").strip()
            if s:
                spec_note = parse_spec(workpiece_type, s)
        
        conn = sqlite3.connect(DB_PATH)
        
        # 查询
        result = None
        match_type = ""
        
        if spec_note:
            cursor = conn.execute("""
                SELECT * FROM material_process
                WHERE workpiece_type=? AND material=? AND thickness_mm=? AND spec_note=?
                ORDER BY verified_count DESC LIMIT 1
            """, (workpiece_type, material, thickness, spec_note))
            result = cursor.fetchone()
            if result:
                match_type = "精确匹配"
        
        if not result:
            cursor = conn.execute("""
                SELECT * FROM material_process
                WHERE workpiece_type=? AND material=? AND thickness_mm=?
                ORDER BY verified_count DESC LIMIT 1
            """, (workpiece_type, material, thickness))
            result = cursor.fetchone()
            if result:
                match_type = "模糊匹配" + (f"(忽略规格)" if spec_note else "")
        
        if result:
            # 更新验证次数
            conn.execute("""
                UPDATE material_process 
                SET verified_count=verified_count+1, last_used_date=CURRENT_TIMESTAMP
                WHERE process_id=?
            """, (result[0],))
            conn.commit()
            
            # 构建字段索引
            idx = {name: i for i, name in enumerate(['process_id'] + FIELD_NAMES)}
            
            # 显示结果
            print(f"\n🔧 【{result[idx['workpiece_type']]} {result[idx['material']]} {result[idx['thickness_mm']]}mm {result[idx['spec_note']] or ''}】{match_type}")
            print(f"   ID: {result[0]}")
            print(f"   图层: {result[idx['layer_size']]}")  # 显示图层
            print(f"   设备: {result[idx['head_model']]} | {result[idx['nozzle_spec']]} | {result[idx['laser_source']]}")
            print(f"   加速度: {result[idx['accel_g']]}")
            print(f"   状态: {result[idx['condition']]}/{result[idx['temp_env']]}/{result[idx['machine_warmup']]}")
            print(f"   脉冲: {result[idx['pulse_freq_hz']]}Hz/{result[idx['pulse_duty_pct']]}%")
            print(f"   功率: {result[idx['power_actual_w']]}W | 速度: {result[idx['speed_mm_min']]}mm/min")
            print(f"   气体: {result[idx['gas_type']]} | 气压: {result[idx['pressure_mpa']]}MPa")
            print(f"   焦点: {result[idx['focus_mm']]}mm | 割嘴高: {result[idx['nozzle_height_mm']]}mm")
            
            # 穿孔显示（只显示有数据的）
            for i in range(1, 4):
                prefix = f'pierce_s{i}_'
                power = result[idx.get(f'{prefix}power_pct', -1)]
                if power:
                    print(f"   穿孔{i}: {power}%/{result[idx[f'{prefix}time_ms']]}ms/{result[idx[f'{prefix}height_mm']]}mm")
                    print(f"         频率:{result[idx[f'{prefix}freq_hz']]}Hz 占空比:{result[idx[f'{prefix}duty_pct']]}% 气压:{result[idx[f'{prefix}pressure_mpa']]}MPa 焦点:{result[idx[f'{prefix}focus_mm']]}mm 加速度:{result[idx[f'{prefix}accel_g']]}")
            # 管材拐角显示
            if result[idx['workpiece_type']] in ['管材', '型材'] and result[idx['tube_corner_enable']] == '开启':
                print(f"   管拐角: 高度修正{result[idx['tube_corner_height_offset']]}mm 气压{result[idx['tube_corner_pressure']]}BAR")
                print(f"          占空比{result[idx['tube_corner_duty']]}% 频率{result[idx['tube_corner_freq']]}Hz")
                print(f"          拐角判定:{result[idx['tube_corner_threshold']]}°/mm")
                if result[idx['tube_r_corner_enable']] == '开启':
                    print(f"          R角: AB{result[idx['tube_r_ab']]} BC{result[idx['tube_r_bc']]} CD{result[idx['tube_r_cd']]} DA{result[idx['tube_r_da']]}mm")
                if result[idx['tube_b_axis_limit']] == '开启':
                    print(f"          B轴限速: {result[idx['tube_b_speed']]}RPM 加速度{result[idx['tube_b_accel']]}rad/s²")
            


            
            print(f"   质量: {result[idx['quality_rating']] or '未评'}星 | 验证: {result[idx['verified_count']]}次")
            if result[idx['notes']]:
                print(f"   备注: {result[idx['notes']]}")
            
            # 操作选项
            print("\n" + "-"*50)
            print("操作选项:")
            print("  [M] 修改此工艺参数")
            print("  [D] 删除此工艺参数")
            print("  [回车] 返回主菜单")
            action = input("选择: ").strip().upper()
            
            if action == 'M':
                modify_process(result[0])
            elif action == 'D':
                if delete_process(result[0], conn):
                    pass
            
        else:
            print("\n❌ 无记录")
            # 显示相近记录
            cursor = conn.execute("""
                SELECT process_id, workpiece_type, material, thickness_mm, spec_note, layer_size, verified_count
                FROM material_process 
                WHERE material=? OR (thickness_mm BETWEEN ?-2 AND ?+2)
                ORDER BY verified_count DESC LIMIT 5
            """, (material, thickness, thickness))
            similar = cursor.fetchall()
            if similar:
                print("\n相近记录:")
                for s in similar:
                    print(f"   ID:{s[0]} {s[1]} {s[2]} {s[3]}mm {s[4] or ''} 图层:{s[5]} (验证{s[6]}次)")
        
        conn.close()
    except Exception as e:
        print(f"\n❌ 查询出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            conn.close()
        except:
            pass
# ========== 余料功能 ==========
def add_remnant():
    """录入余料"""
    print("\n📦 录入新余料")
    rid = input(f"编号[YM-{datetime.now().strftime('%m%d%H%M')}]: ").strip()
    if not rid:
        rid = f"YM-{datetime.now().strftime('%m%d%H%M')}"
    
    print("材质简写: 235/304...")
    m = input("材质[Q235]: ").strip().lower()
    material = parse_material(m)
    
    t = safe_float("厚度mm[0]: ", 0)
    l = safe_int("长度mm[0]: ", 0)
    w = safe_int("宽度mm[0]: ", 0)
    zone = input("区域[A区]: ").strip() or "A区"
    shelf = input("料架[1#]: ").strip() or "1#"
    layer = safe_int("层[1]: ", 1)
    
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            INSERT INTO remnant_inventory 
            (remnant_id, material_type, thickness_mm, length_mm, width_mm,
             location_zone, location_shelf, location_layer, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'available')
        """, (rid, material, t, l, w, zone, shelf, layer))
        conn.commit()
        area = l * w / 1000000
        print(f"✅ 已保存: {rid} | {l}×{w}mm={area:.3f}㎡")
    except sqlite3.IntegrityError:
        print(f"❌ 编号{rid}已存在")
    finally:
        conn.close()

def list_remnants():
    """查询余料"""
    print("\n【查询余料】")
    print("材质简写: 235/304... (回车查全部)")
    m = input("材质: ").strip()
    
    conn = sqlite3.connect(DB_PATH)
    
    if m:
        material = parse_material(m)
        t = safe_float("厚度mm[0]: ", 0)
        cursor = conn.execute("""
            SELECT * FROM remnant_inventory 
            WHERE material_type=? AND thickness_mm=? AND status='available'
            ORDER BY area_mm2 DESC
        """, (material, t))
        rows = cursor.fetchall()
        print(f"\n📋 {material} {t}mm: {len(rows)}张")
        for r in rows:
            print(f"   {r[0]}: {r[3]}×{r[4]}mm @{r[6]}-{r[7]}-{r[8]}层")
    else:
        cursor = conn.execute("""
            SELECT material_type, thickness_mm, COUNT(*), SUM(area_mm2)
            FROM remnant_inventory WHERE status='available'
            GROUP BY material_type, thickness_mm
        """)
        print("\n📊 库存汇总:")
        for r in cursor.fetchall():
            print(f"   {r[0]} {r[1]}mm: {r[2]}张, {r[3]/1000000:.2f}㎡")
    
    conn.close()

# ========== 占位功能 ==========
def import_bochu_log():
    print("\n📄 导入柏楚日志（待实现）")

def import_weihong_csv():
    print("\n📄 导入维宏CSV（待实现）")

def analyze_efficiency():
    print("\n📊 效率分析（待实现）")

def analyze_quality():
    print("\n📊 质量统计（待实现）")

def export_excel():
    print("\n📊 导出Excel（待实现）")

# ========== 主菜单 ==========
def main():
    # 检查数据库
    if not os.path.exists(DB_PATH):
        print("首次运行，初始化数据库...")
        init_database()
    else:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.execute("SELECT workpiece_type FROM material_process LIMIT 1")
            conn.close()
            print(f"✅ 数据库已加载: {DB_PATH}")
        except:
            print("⚠️ 数据库需要升级，重新初始化...")
            os.remove(DB_PATH)
            init_database()
    
    while True:
        print("\n" + "="*70)
        print("    激光切割数据库管理系统 v8.2")
        print("    图层:大/中/小公用 | 管材拐角13参数 | 查询支持删改")
        print("="*70)
        print("【数据管理】")
        print("  1. 查询工艺参数(支持删改)  2. 录入余料")
        print("  3. 查看余料库存              4. 录入/更新工艺参数")
        print("\n【生产数据】")
        print("  5. 导入柏楚日志              6. 导入维宏CSV报表")
        print("\n【分析报表】")
        print("  7. 效率分析                  8. 质量统计")
        print("  9. 导出Excel报表")
        print("\n【系统】")
        print("  0. 退出")
        
        choice = input("\n选择: ").strip()
        
        if choice == '1':
            query_process()
        elif choice == '2':
            add_remnant()
        elif choice == '3':
            list_remnants()
        elif choice == '4':
            add_process_interactive()
        elif choice == '5':
            import_bochu_log()
        elif choice == '6':
            import_weihong_csv()
        elif choice == '7':
            analyze_efficiency()
        elif choice == '8':
            analyze_quality()
        elif choice == '9':
            export_excel()
        elif choice == '0':
            print("\n再见！")
            break

if __name__ == "__main__":
    main()
