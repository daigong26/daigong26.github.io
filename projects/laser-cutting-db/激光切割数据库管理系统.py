import sqlite3
from datetime import datetime
import os

DB_PATH = r'C:\Users\Administrator\laser_cutting_master.db'

def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS material_process (
            process_id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_type VARCHAR(20) NOT NULL,
            thickness_mm DECIMAL(4,1) NOT NULL,
            laser_power_w INTEGER,
            cutting_speed_mm_min INTEGER,
            gas_type VARCHAR(10),
            gas_pressure_mpa DECIMAL(3,2),
            focus_position_mm DECIMAL(4,2),
            nozzle_diameter_mm DECIMAL(3,2),
            nozzle_height_mm DECIMAL(3,2),
            pierce_power_percent INTEGER,
            pierce_time_ms INTEGER,
            pierce_height_mm DECIMAL(4,2),
            cut_quality_rating INTEGER CHECK(cut_quality_rating BETWEEN 1 AND 5),
            edge_roughness_ra DECIMAL(4,2),
            dross_attachment BOOLEAN,
            created_by VARCHAR(20) DEFAULT '你',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified_count INTEGER DEFAULT 0,
            last_used_date TIMESTAMP,
            notes TEXT,
            UNIQUE(material_type, thickness_mm, cut_quality_rating)
        );

        CREATE TABLE IF NOT EXISTS remnant_inventory (
            remnant_id VARCHAR(20) PRIMARY KEY,
            material_type VARCHAR(20) NOT NULL,
            thickness_mm DECIMAL(4,1) NOT NULL,
            length_mm INTEGER NOT NULL,
            width_mm INTEGER NOT NULL,
            area_mm2 INTEGER GENERATED ALWAYS AS (length_mm * width_mm) STORED,
            location_zone VARCHAR(20),
            location_shelf VARCHAR(20),
            location_layer INTEGER,
            status VARCHAR(10) DEFAULT 'available',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_check_date TIMESTAMP,
            source_job_id VARCHAR(20),
            original_sheet_id VARCHAR(20)
        );

        CREATE TABLE IF NOT EXISTS part_history (
            part_id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_name VARCHAR(50) NOT NULL,
            part_number VARCHAR(50),
            customer_name VARCHAR(50),
            file_path VARCHAR(200),
            material_type VARCHAR(20),
            thickness_mm DECIMAL(4,1),
            part_area_mm2 INTEGER,
            part_perimeter_mm INTEGER,
            bounding_length_mm INTEGER,
            bounding_width_mm INTEGER,
            total_quantity_cut INTEGER DEFAULT 0,
            total_cut_time_min INTEGER,
            first_cut_date TIMESTAMP,
            last_cut_date TIMESTAMP,
            quality_issues TEXT,
            best_process_id INTEGER,
            FOREIGN KEY (best_process_id) REFERENCES material_process(process_id)
        );

        CREATE TABLE IF NOT EXISTS cut_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id VARCHAR(20),
            part_id INTEGER,
            remnant_id VARCHAR(20),
            machine_id VARCHAR(20),
            operator_id VARCHAR(20),
            actual_power_w INTEGER,
            actual_speed_mm_min INTEGER,
            actual_gas_pressure_mpa DECIMAL(3,2),
            cut_start_time TIMESTAMP,
            cut_end_time TIMESTAMP,
            actual_quantity INTEGER,
            quality_check_result VARCHAR(10),
            issues_found TEXT,
            FOREIGN KEY (part_id) REFERENCES part_history(part_id),
            FOREIGN KEY (remnant_id) REFERENCES remnant_inventory(remnant_id)
        );
    """)
    
    conn.commit()
    conn.close()
    print("✅ 数据库创建成功")

def add_your_experience():
    """录入核心工艺经验"""
    conn = sqlite3.connect(DB_PATH)
    
    your_knowledge = [
        ("Q235", 1.5,  3000,  25000, "空气", 0.8, -1.0, "薄板高速，空气最省成本"),
        ("Q235", 3,    6000,  15000, "空气", 1.0, -1.0, "夜班稳定参数"),
        ("Q235", 5,    8000,   8000, "氧气", 0.3, -2.0, "中厚板氧气断面光亮"),
        ("Q235", 8,   12000,   4500, "氧气", 0.25, -3.0, "厚板注意分层穿孔"),
        ("Q235", 10,  15000,   3500, "氧气", 0.2, -4.0, "降速防挂渣"),
        ("304",  2,    4000,  18000, "氮气", 1.5, -1.0, "不锈钢必须氮气防氧化"),
        ("304",  5,    8000,   8000, "氮气", 2.0, -2.0, "厚不锈钢高气压大流量"),
    ]
    
    for params in your_knowledge:
        try:
            conn.execute("""
                INSERT INTO material_process 
                (material_type, thickness_mm, laser_power_w, cutting_speed_mm_min,
                 gas_type, gas_pressure_mpa, focus_position_mm, notes, verified_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 999)
            """, params)
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()
    print(f"✅ 已录入 {len(your_knowledge)} 条核心工艺经验")

def query_process(material, thickness):
    """查询最优参数"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT laser_power_w, cutting_speed_mm_min, gas_type, 
               gas_pressure_mpa, focus_position_mm, notes, verified_count
        FROM material_process
        WHERE material_type = ? AND thickness_mm = ?
        ORDER BY verified_count DESC
        LIMIT 1
    """, (material, thickness))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        print(f"\n🔧 【{material} {thickness}mm 最优参数】")
        print(f"   功率：{result[0]}W")
        print(f"   速度：{result[1]}mm/min")
        print(f"   气体：{result[2]}  气压：{result[3]}MPa")
        print(f"   焦点：{result[4]}mm")
        print(f"   💡 经验：{result[5]}")
        print(f"   ✅ 验证次数：{result[6]}")
    else:
        print(f"\n❌ 暂无 {material} {thickness}mm 的记录，需要试切录入")
    
    return result

def add_remnant():
    """交互式录入余料"""
    print("\n📦 录入新余料")
    
    remnant_id = input("余料编号（如YM-250331-001）: ").strip()
    material = input("材质（Q235/304/316/铝板）: ").strip()
    thickness = float(input("厚度mm: "))
    length = int(input("长度mm: "))
    width = int(input("宽度mm: "))
    zone = input("存放区域（A区/B区/3号机旁）: ").strip()
    shelf = input("料架编号（1#架/2#架）: ").strip()
    layer = int(input("层数（1-4）: "))
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO remnant_inventory 
        (remnant_id, material_type, thickness_mm, length_mm, width_mm,
         location_zone, location_shelf, location_layer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (remnant_id, material, thickness, length, width, zone, shelf, layer))
    conn.commit()
    conn.close()
    
    area = length * width / 1000000
    print(f"\n✅ 已保存！")
    print(f"   编号：{remnant_id}")
    print(f"   尺寸：{length} x {width} mm")
    print(f"   面积：{area:.3f} ㎡")
    print(f"   位置：{zone} - {shelf} - {layer}层")

def list_remnants(material=None, thickness=None):
    """查询余料库存 - 列出明细规格"""
    conn = sqlite3.connect(DB_PATH)
    
    if material and thickness:
        # 明细查询
        cursor = conn.execute("""
            SELECT remnant_id, length_mm, width_mm, area_mm2,
                   location_zone, location_shelf, location_layer, created_date
            FROM remnant_inventory
            WHERE material_type = ? AND thickness_mm = ? AND status = 'available'
            ORDER BY area_mm2 DESC
        """, (material, thickness))
        
        rows = cursor.fetchall()
        if not rows:
            print(f"\n📭 {material} {thickness}mm 暂无库存")
            conn.close()
            return
            
        print(f"\n📋 {material} {thickness}mm 可用余料明细（{len(rows)}张）：")
        print("=" * 70)
        for row in rows:
            area_m2 = row[3] / 1000000
            print(f"\n🔹 编号：{row[0]}")
            print(f"   尺寸：{row[1]} x {row[2]} mm")
            print(f"   面积：{area_m2:.3f} ㎡")
            print(f"   位置：{row[4]} → {row[5]} → {row[6]}层")
            print(f"   入库：{row[7][:10]}")
            print("-" * 70)
    else:
        # 汇总查询 - 列出明细规格（修正版）
        cursor = conn.execute("""
            SELECT 
                material_type, 
                thickness_mm, 
                COUNT(*) as count, 
                SUM(area_mm2) as total_area,
                GROUP_CONCAT(DISTINCT location_zone) as zones
            FROM remnant_inventory
            WHERE status = 'available'
            GROUP BY material_type, thickness_mm
            ORDER BY material_type, thickness_mm
        """)
        
        rows = cursor.fetchall()
        if not rows:
            print("\n📭 余料库为空")
            conn.close()
            return
            
        print("\n📊 余料库存汇总：")
        print("=" * 70)
        for row in rows:
            material = row[0]
            thickness = row[1]
            count = row[2]
            total_area = row[3]
            zones = row[4]
            
            # 查询该材质厚度的所有规格及数量
            cursor2 = conn.execute("""
                SELECT length_mm, width_mm, COUNT(*) as num
                FROM remnant_inventory
                WHERE material_type = ? AND thickness_mm = ? AND status = 'available'
                GROUP BY length_mm, width_mm
                ORDER BY length_mm * width_mm DESC
            """, (material, thickness))
            
            # 构建规格列表
            size_list = []
            for r in cursor2:
                length, width, num = r
                if num == 1:
                    size_list.append(f"{length}×{width}")
                else:
                    size_list.append(f"{length}×{width}({num}张)")
            
            print(f"\n🔸 {material} {thickness}mm：共 {count} 张，总面积 {total_area/1000000:.2f} ㎡")
            print(f"   规格：{' / '.join(size_list)}")
            print(f"   位置：{zones}")
            print("-" * 70)
    
    conn.close()

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("首次运行，初始化数据库...")
        init_database()
        add_your_experience()
        print(f"\n数据库位置：{DB_PATH}")
    else:
        print(f"数据库已加载：{DB_PATH}")
    
    while True:
        print("\n" + "=" * 50)
        print("    激光切割数据库管理系统 v3.0")
        print("=" * 50)
        print("1. 查询工艺参数")
        print("2. 录入新余料")
        print("3. 查询余料库存（列出明细规格）")
        print("4. 退出")
        
        choice = input("\n选择操作（1-4）: ").strip()
        
        if choice == '1':
            mat = input("材质: ").strip()
            thick = float(input("厚度mm: "))
            query_process(mat, thick)
        elif choice == '2':
            add_remnant()
        elif choice == '3':
            mat = input("材质（直接回车查全部）: ").strip()
            if mat:
                thick = float(input("厚度mm: "))
                list_remnants(mat, thick)
            else:
                list_remnants()
        elif choice == '4':
            print("\n再见！数据已自动保存")
            break
        else:
            print("无效选择，请重新输入")
