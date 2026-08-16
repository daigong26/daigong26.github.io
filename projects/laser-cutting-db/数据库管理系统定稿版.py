#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
激光切割数据库管理系统 v7.1
- 修正字段索引显示错误
- 全防闪退输入
- 智能简写识别
- 模糊匹配查询
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
    '420': 'Q420',
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
    '17': 'φ1.2双层', '双层1.2', 'φ1.2双层',

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

MACHINE_MAP = {
    '1': '宏山G3015', '宏山': '宏山G3015', 'g3015': '宏山G3015',
    '2': '宏山T230', 't230': '宏山T230', '管材机': '宏山T230',
    '3': '宏山G4020', 'g4020': '宏山G4020',
    '4': '邦德T230', '邦德': '邦德T230',
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

CORNER_MAP = {
    '1': '降速', '降': '降速', '降速': '降速',
    '2': '降功率', '功': '降功率', '降功率': '降功率',
    '3': '不关光', '光': '不关光', '不关光': '不关光',
}

GAS_MAP = {
    '1': '空气', '空': '空气', '空气': '空气',
    '2': '氧气', '氧': '氧气', '氧气': '氧气',
    '3': '氮气', '氮': '氮气', '氮气': '氮气',
    '4': '混合气', '混': '混合气', '混合': '混合气',
}

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
    for k, v in options_map.items():
        if k in ['1', '2', '3', '4', '5'] and v not in shown:
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

# ========== 数据库 ==========
def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS material_process (
            process_id INTEGER PRIMARY KEY AUTOINCREMENT,
            workpiece_type VARCHAR(10),
            material VARCHAR(20),
            thickness_mm DECIMAL(4,1),
            spec_note VARCHAR(30),
            head_model VARCHAR(30),
            nozzle_spec VARCHAR(20),
            laser_source VARCHAR(20),
            machine_model VARCHAR(30),
            condition VARCHAR(10),
            temp_env VARCHAR(10),
            machine_warmup VARCHAR(10),
            corner_strategy VARCHAR(20),
            pulse_freq_hz INTEGER DEFAULT 0,
            pulse_duty_pct INTEGER DEFAULT 100,
            power_actual_w INTEGER,
            speed_mm_min INTEGER,
            gas_type VARCHAR(10),
            pressure_mpa DECIMAL(3,2),
            focus_mm DECIMAL(4,2),
            nozzle_height_mm DECIMAL(3,2),
            pierce_s1_power_pct INTEGER,
            pierce_s1_time_ms INTEGER,
            pierce_s1_height_mm DECIMAL(4,2),
            pierce_s2_power_pct INTEGER,
            pierce_s2_time_ms INTEGER,
            pierce_s2_height_mm DECIMAL(4,2),
            pierce_s3_power_pct INTEGER,
            pierce_s3_time_ms INTEGER,
            pierce_s3_height_mm DECIMAL(4,2),
            quality_rating INTEGER,
            verified_count INTEGER DEFAULT 0,
            last_used_date TIMESTAMP,
            notes TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(workpiece_type, material, thickness_mm, spec_note,
                   head_model, nozzle_spec, laser_source, 
                   condition, temp_env, machine_warmup,
                   corner_strategy, pulse_freq_hz)
        );

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

# ========== 核心功能 ==========
def add_process_interactive():
    """录入工艺参数"""
    print("\n" + "="*70)
    print("🔧 录入新工艺参数")
    print("="*70)
    
    # 工件类型
    print("\n【工件类型】")
    print("  1. 板材  2. 管材  3. 型材")
    t = input("选择[1]: ").strip()
    workpiece_type = {'2': '管材', '3': '型材'}.get(t, '板材')
    print(f"  → {workpiece_type}")
    
    # 材质
    print("\n【材质】简写: 235=Q235")
    m = input("材质[Q235]: ").strip().lower()
    material = parse_material(m)
    
    # 厚度
    thickness = safe_float("厚度/壁厚mm[0]: ", 0)
    
    # 规格
    spec_note = ""
    if workpiece_type == '管材':
        print("\n【规格】格式: D100x5, 100x5, 80x60x5")
    elif workpiece_type == '型材':
        print("\n【规格】格式: 63x63x6角钢, 10槽钢, H200x100")
    s = input("规格: ").strip()
    if s:
        spec_note = parse_spec(workpiece_type, s)
    
    # 查重
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT power_actual_w, speed_mm_min, verified_count, notes
        FROM material_process
        WHERE workpiece_type=? AND material=? AND thickness_mm=? AND spec_note=?
    """, (workpiece_type, material, thickness, spec_note))
    existing = cursor.fetchone()
    
    if existing:
        print(f"\n⚠️ 已有: {existing[0]}W/{existing[1]}mm/min, 验证{existing[2]}次")
        if input("覆盖?[y/N]: ").lower() != 'y':
            conn.close()
            return
        conn.execute("""
            DELETE FROM material_process 
            WHERE workpiece_type=? AND material=? AND thickness_mm=? AND spec_note=?
        """, (workpiece_type, material, thickness, spec_note))
    
    # 设备
    head = select_option("【切割头】", HEAD_MAP, '2')
    nozzle = select_option("【喷嘴】", NOZZLE_MAP, '2')
    laser = select_option("【激光器】", LASER_MAP, '2')
    machine = select_option("【机床】", MACHINE_MAP, '1')
    
    # 环境
    condition = select_option("【材料状态】", CONDITION_MAP, '1')
    temp = select_option("【环境温度】", TEMP_MAP, '1')
    warmup = select_option("【设备状态】", WARMUP_MAP, '2')
    
    # 工艺
    corner = select_option("【拐角策略】", CORNER_MAP, '1')
    print("\n【脉冲】回车=连续波")
    freq = safe_int("脉冲频率Hz[0]: ", 0)
    duty = safe_int("占空比%[100]: ", 100) if freq > 0 else 100
    
    # 切割参数
    print("\n【切割参数】")
    power = safe_int("实际功率W[0]: ", 0)
    speed = safe_int("速度mm/min[0]: ", 0)
    gas = select_option("【气体】", GAS_MAP, '1')
    pressure = safe_float("气压MPa[0]: ", 0)
    focus = safe_float("焦点mm[0]: ", 0)
    nozzle_h = safe_float("割嘴高度mm[0]: ", 0)
    
    # 穿孔
    print("\n【多级穿孔】厚板填写，薄板回车跳过")
    pierce = []
    for i in range(1, 4):
        print(f"\n第{i}级（全回车=跳过）:")
        p = safe_int("  功率%: ", 0)
        if p == 0:
            break
        t = safe_int("  时间ms: ", 0)
        h = safe_float("  高度mm: ", 0)
        pierce.append({'power': p, 'time': t, 'height': h})
    
    s1 = pierce[0] if len(pierce) > 0 else {'power': None, 'time': None, 'height': None}
    s2 = pierce[1] if len(pierce) > 1 else {'power': None, 'time': None, 'height': None}
    s3 = pierce[2] if len(pierce) > 2 else {'power': None, 'time': None, 'height': None}
    
    notes = input("\n经验备注: ").strip()
    
    # 保存
    try:
        conn.execute("""
            INSERT INTO material_process 
            (workpiece_type, material, thickness_mm, spec_note,
             head_model, nozzle_spec, laser_source, machine_model,
             condition, temp_env, machine_warmup,
             corner_strategy, pulse_freq_hz, pulse_duty_pct,
             power_actual_w, speed_mm_min, gas_type, pressure_mpa, focus_mm, nozzle_height_mm,
             pierce_s1_power_pct, pierce_s1_time_ms, pierce_s1_height_mm,
             pierce_s2_power_pct, pierce_s2_time_ms, pierce_s2_height_mm,
             pierce_s3_power_pct, pierce_s3_time_ms, pierce_s3_height_mm,
             notes, verified_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (workpiece_type, material, thickness, spec_note,
              head, nozzle, laser, machine,
              condition, temp, warmup,
              corner, freq, duty,
              power, speed, gas, pressure, focus, nozzle_h,
              s1['power'], s1['time'], s1['height'],
              s2['power'], s2['time'], s2['height'],
              s3['power'], s3['time'], s3['height'],
              notes))
        conn.commit()
        print(f"\n✅ 已保存: {workpiece_type} {material} {thickness}mm {spec_note}")
        print(f"   {power}W/{speed}mm/min | 验证:1")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
    finally:
        conn.close()

def query_process():
    """查询工艺参数 - 修正索引版"""
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
        
        # ========== 修正后的字段索引 ==========
        # result[0]=process_id
        # result[1]=workpiece_type, [2]=material, [3]=thickness_mm, [4]=spec_note
        # result[5]=head_model, [6]=nozzle_spec, [7]=laser_source, [8]=machine_model
        # result[9]=condition, [10]=temp_env, [11]=machine_warmup
        # result[12]=corner_strategy, [13]=pulse_freq_hz, [14]=pulse_duty_pct
        # result[15]=power_actual_w, [16]=speed_mm_min
        # result[17]=gas_type, [18]=pressure_mpa, [19]=focus_mm, [20]=nozzle_height_mm
        # result[21-29]=穿孔参数, [30]=quality_rating, [31]=verified_count, [32]=notes
        
        print(f"\n🔧 【{result[1]} {result[2]}mm {result[4] or ''}】{match_type}")
        print(f"   设备: {result[5]} | {result[6]} | {result[7]}")
        print(f"   机床: {result[8]}")
        print(f"   状态: {result[9]}/{result[10]}/{result[11]}")
        print(f"   策略: {result[12]} | 脉冲: {result[13]}Hz/{result[14]}%")
        print(f"   功率: {result[15]}W | 速度: {result[16]}mm/min")
        print(f"   气体: {result[17]} | 气压: {result[18]}MPa")
        print(f"   焦点: {result[19]}mm | 割嘴高: {result[20]}mm")
        
        # 穿孔
        if result[21]:
            print(f"   穿孔1: {result[21]}%/{result[22]}ms/{result[23]}mm")
        if result[24]:
            print(f"   穿孔2: {result[24]}%/{result[25]}ms/{result[26]}mm")
        if result[27]:
            print(f"   穿孔3: {result[27]}%/{result[28]}ms/{result[29]}mm")
        
        print(f"   质量: {result[30] or '未评'}星 | 验证: {result[31]}次")
        if result[32]:
            print(f"   备注: {result[32]}")
    else:
        print("\n❌ 无记录")
        # 显示相近记录
        cursor = conn.execute("""
            SELECT workpiece_type, material, thickness_mm, spec_note, verified_count
            FROM material_process 
            WHERE material=? OR (thickness_mm BETWEEN ?-2 AND ?+2)
            ORDER BY verified_count DESC LIMIT 5
        """, (material, thickness, thickness))
        similar = cursor.fetchall()
        if similar:
            print("\n相近记录:")
            for s in similar:
                print(f"   {s[0]} {s[1]} {s[2]}mm {s[3] or ''} (验证{s[4]}次)")
    
    conn.close()

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
        # 简单检查字段
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
        print("    激光切割数据库管理系统 v7.1")
        print("="*70)
        print("【数据管理】")
        print("  1. 查询工艺参数      2. 录入余料")
        print("  3. 查看余料库存      4. 录入/更新工艺参数")
        print("\n【生产数据】")
        print("  5. 导入柏楚日志      6. 导入维宏CSV报表")
        print("\n【分析报表】")
        print("  7. 效率分析          8. 质量统计")
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
