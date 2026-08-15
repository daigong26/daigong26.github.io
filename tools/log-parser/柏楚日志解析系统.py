import re
import sqlite3
from datetime import datetime

DB_PATH = r'C:\Users\Administrator\laser_cutting_master.db'
LOG_PATH = r'C:\Bochu\FSCUT\Log\2026\04\01\切割日志.txt'

def parse_log(filepath):
    """解析柏楚格式日志"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按空行分割成块
    jobs = [block.strip() for block in content.split('\n\n') if block.strip()]
    
    records = []
    for job in jobs:
        lines = job.split('\n')
        if len(lines) < 3:
            continue
        
        # 解析 [START]
        start_match = re.search(r'\[(.*?)\] \[START\] Job:(\w+) Material:(\w+) Thickness:(\d+)mm', lines[0])
        if not start_match:
            continue
            
        # 解析 [PARAM]
        param_match = re.search(r'Power:(\d+)W Speed:(\d+) Gas:(\w+) Pressure:([\d.]+) Focus:([\d.-]+)', lines[1])
        
        # 解析 [END]
        end_match = re.search(r'\[(.*?)\] \[END\] Length:([\d.]+)m Time:(\d+)s Quality:(\w+)', lines[2])
        
        record = {
            'start_time': start_match.group(1),
            'job_id': start_match.group(2),
            'material': start_match.group(3),
            'thickness': int(start_match.group(4)),
            'power': int(param_match.group(1)),
            'speed': int(param_match.group(2)),
            'gas': param_match.group(3),
            'pressure': float(param_match.group(4)),
            'focus': float(param_match.group(5)),
            'end_time': end_match.group(1),
            'length': float(end_match.group(2)),
            'time_sec': int(end_match.group(3)),
            'quality': end_match.group(4),
        }
        
        # 计算实际速度
        record['actual_speed'] = (record['length'] * 1000) / record['time_sec'] * 60
        
        records.append(record)
    
    return records

def save_to_db(records):
    """保存到数据库"""
    conn = sqlite3.connect(DB_PATH)
    
    for r in records:
        # 检查是否已存在
        cursor = conn.execute("SELECT COUNT(*) FROM cut_records WHERE job_id = ?", (r['job_id'],))
        if cursor.fetchone()[0] > 0:
            print(f"⚠️ {r['job_id']} 已存在，跳过")
            continue
        
        conn.execute("""
            INSERT INTO cut_records 
            (job_id, cut_start_time, cut_end_time, actual_power_w, actual_speed_mm_min,
             actual_quantity, issues_found, machine_id, operator_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r['job_id'],
            r['start_time'],
            r['end_time'],
            r['power'],
            r['actual_speed'],
            r['length'] * 1000,
            f"材质{r['material']}{r['thickness']}mm,气压{r['pressure']},焦点{r['focus']},质量{r['quality']}",
            '柏楚2万瓦',
            '你'
        ))
        
        print(f"✅ {r['job_id']}: {r['material']}{r['thickness']}mm 切割{r['length']}m 速度{r['actual_speed']:.0f}mm/min 质量{r['quality']}")
    
    conn.commit()
    conn.close()

def main():
    print("=" * 60)
    print("柏楚日志解析系统")
    print("=" * 60)
    
    records = parse_log(LOG_PATH)
    print(f"\n解析到 {len(records)} 条切割记录：\n")
    
    for r in records:
        print(f"Job {r['job_id']}: {r['material']} {r['thickness']}mm")
        print(f"  功率{r['power']}W 理论速度{r['speed']}mm/min")
        print(f"  实际速度{r['actual_speed']:.0f}mm/min 差异{r['actual_speed']-r['speed']:.0f}mm/min")
        print(f"  质量：{r['quality']}")
        print()
    
    save_to_db(records)
    print(f"\n完成！共入库 {len(records)} 条记录")

if __name__ == "__main__":
    main()
