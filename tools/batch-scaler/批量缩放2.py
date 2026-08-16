#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SolidWorks 批量处理脚本 - 修复文件选择版
"""

import os
import sys
import time
import builtins
import subprocess
from pathlib import Path

_str = builtins.str

def safe_str(obj):
    return _str(obj)

# ============================================================
# GUI选择文件夹
# ============================================================
def select_folder_gui():
    temp_script = Path(os.environ['TEMP']) / 'sw_select_folder.py'
    script_content = '''import tkinter as tk
from tkinter import filedialog
import sys
root = tk.Tk()
root.withdraw()
folder = filedialog.askdirectory(title="请选择包含SLDPRT文件的文件夹", initialdir="/")
root.destroy()
print(folder)
sys.stdout.flush()'''
    
    try:
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        result = subprocess.run([sys.executable, str(temp_script)], capture_output=True, text=True, timeout=60)
        try: temp_script.unlink()
        except: pass
        return result.stdout.strip() if result.stdout.strip() else None
    except Exception as e:
        print(f"GUI错误: {safe_str(e)}")
        return None

# ============================================================
# 修复：文件选择功能
# ============================================================
def select_files_to_process(files_list):
    """让用户选择要处理的文件 - 修复版"""
    if not files_list:
        return []
    
    print("\n" + "=" * 60)
    print("文件列表：")
    for i, f in enumerate(files_list, 1):
        print(f"  {i}. {f.name}")
    print("-" * 60)
    print("输入要处理的编号（如：1,3,5 或 a=全部）：", end="")
    
    choice = input().strip().lower()
    
    # 处理全部
    if choice == 'a' or choice == '':
        print(f"已选择全部 {len(files_list)} 个文件")
        return files_list
    
    # 解析选择
    selected_files = []
    try:
        # 支持逗号和空格分隔
        parts = choice.replace(' ', ',').split(',')
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # 处理范围（如 1-3）
            if '-' in part:
                try:
                    start, end = part.split('-')
                    start = int(start.strip())
                    end = int(end.strip())
                    for idx in range(start, end + 1):
                        if 1 <= idx <= len(files_list):
                            selected_files.append(files_list[idx - 1])
                except:
                    print(f"  警告：无法解析范围 '{part}'")
            else:
                # 单个数字
                try:
                    idx = int(part)
                    if 1 <= idx <= len(files_list):
                        selected_files.append(files_list[idx - 1])
                    else:
                        print(f"  警告：编号 {idx} 超出范围")
                except:
                    print(f"  警告：无法解析 '{part}'")
        
        # 去重（保持顺序）
        seen = set()
        unique_files = []
        for f in selected_files:
            if f.name not in seen:
                seen.add(f.name)
                unique_files.append(f)
        
        print(f"\n已选择 {len(unique_files)} 个文件：")
        for f in unique_files:
            print(f"  - {f.name}")
        
        return unique_files
        
    except Exception as e:
        print(f"选择解析错误: {safe_str(e)}")
        print("默认处理全部文件")
        return files_list

import win32com.client
import pythoncom

CONFIG = {
    'file_extensions': ['.SLDPRT'],
    'scale_factor': 1.0,
    'solidworks_version': 'SldWorks.Application.30',
    'visible': True,
}

stats = {
    'total': 0,
    'success': 0,
    'failed': 0,
    'errors': []
}

class swConst:
    swDocPART = 1
    swOpenDocOptions_Silent = 1
    swBodyType_e_swSolidBody = 0

class SolidWorksBatchProcessor:
    def __init__(self):
        self.sw_app = None
        self.sw_model = None
        
    def connect(self):
        try:
            print("正在连接 SolidWorks...")
            self.sw_app = win32com.client.Dispatch(CONFIG['solidworks_version'])
            self.sw_app.Visible = CONFIG['visible']
            print("✓ SolidWorks 连接成功")
            return True
        except Exception as error_info:
            print(f"✗ 连接失败: {safe_str(error_info)}")
            return False
    
    def open_file(self, file_path):
        try:
            errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
            warnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
            file_path_text = _str(file_path)
            
            self.sw_model = self.sw_app.OpenDoc6(
                file_path_text,
                swConst.swDocPART,
                swConst.swOpenDocOptions_Silent,
                "",
                errors,
                warnings
            )
            
            if self.sw_model is None:
                return False, "无法打开文件"
            
            return True, "文件已打开"
            
        except Exception as error_info:
            return False, f"打开失败: {safe_str(error_info)}"
    
    def scale_model(self):
        try:
            if self.sw_model is None:
                return False, "模型未初始化"
            
            try:
                bodies_variant = self.sw_model.GetBodies2(
                    swConst.swBodyType_e_swSolidBody,
                    True
                )
            except Exception as e:
                try:
                    bodies_variant = self.sw_model.GetBodies(swConst.swBodyType_e_swSolidBody)
                except Exception as e2:
                    return False, f"获取实体失败"
            
            if bodies_variant is None:
                return False, "未找到任何实体"
            
            try:
                if hasattr(bodies_variant, '__len__'):
                    body_count = len(bodies_variant)
                    bodies_list = list(bodies_variant)
                else:
                    body_count = 1
                    bodies_list = [bodies_variant]
            except Exception as e:
                return False, f"解析实体失败"
            
            print(f"    ✓ 找到 {body_count} 个实体")
            
            if body_count == 0:
                return False, "实体数量为 0"
            
            success_count = 0
            for i, body in enumerate(bodies_list):
                try:
                    body_name = "Unknown"
                    try:
                        body_name = body.Name
                    except:
                        pass
                    
                    print(f"      处理实体 {i+1}/{body_count}: {safe_str(body_name)}")
                    
                    try:
                        body.Select2(False, None)
                    except Exception as e:
                        print(f"        警告: 选择失败")
                    
                    success_count += 1
                        
                except Exception as body_error:
                    print(f"      处理实体 {i+1} 时出错")
            
            if success_count > 0:
                return True, f"成功处理 {success_count}/{body_count} 个实体"
            else:
                return False, "未能成功处理"
            
        except Exception as error_info:
            return False, f"缩放失败"
    
    def close_file(self, save_changes=False):
        try:
            if self.sw_model:
                self.sw_app.CloseDoc(self.sw_model.GetTitle())
                self.sw_model = None
        except:
            pass
    
    def quit(self):
        try:
            if self.sw_app:
                self.sw_app.ExitApp()
        except:
            pass

def main():
    print("=" * 60)
    print("SolidWorks 批量处理工具")
    print("=" * 60)
    
    # 选择文件夹
    print("\n正在打开文件夹选择对话框...")
    source_folder = select_folder_gui()
    
    if not source_folder:
        print("未选择文件夹，程序退出")
        input("按回车键退出...")
        return
    
    print(f"已选择: {safe_str(source_folder)}")
    
    # 检查路径
    source_path = Path(source_folder)
    if not source_path.exists():
        print(f"错误: 路径不存在")
        input("按回车键退出...")
        return
    
    # 获取所有文件
    all_files = []
    seen_names = set()
    
    for file_path in source_path.glob('*.SLDPRT'):
        name = file_path.name
        if name not in seen_names:
            seen_names.add(name)
            all_files.append(file_path)
    
    all_files.sort(key=lambda x: x.name)
    
    if not all_files:
        print("未找到任何 SLDPRT 文件")
        input("按回车键退出...")
        return
    
    print(f"\n找到 {len(all_files)} 个文件")
    
    # 选择要处理的文件
    files_to_process = select_files_to_process(all_files)
    
    if not files_to_process:
        print("未选择任何文件，程序退出")
        input("按回车键退出...")
        return
    
    stats['total'] = len(files_to_process)
    
    print(f"\n{'='*60}")
    print(f"准备处理 {len(files_to_process)} 个文件")
    print(f"{'='*60}")
    
    # 显示最终选择的文件
    print("\n最终选择的文件：")
    for i, f in enumerate(files_to_process, 1):
        print(f"  {i}. {f.name}")
    
    # 确认
    print(f"\n确认处理？(y/n)：", end="")
    if input().strip().lower() != 'y':
        print("已取消")
        return
    
    # 连接SW
    processor = SolidWorksBatchProcessor()
    
    if not processor.connect():
        input("按回车键退出...")
        return
    
    # 处理文件
    for idx, file_path in enumerate(files_to_process, 1):
        filename = file_path.name
        print(f"\n{'='*60}")
        print(f"处理: {safe_str(filename)}")
        print(f"进度: [{idx}/{len(files_to_process)}]")
        
        success, message = processor.open_file(file_path)
        print(f"  {'✓' if success else '✗'} {safe_str(message)}")
        
        if not success:
            stats['failed'] += 1
            stats['errors'].append(f"{safe_str(filename)}: {safe_str(message)}")
            continue
        
        success, message = processor.scale_model()
        print(f"  {'✓' if success else '✗'} {safe_str(message)}")
        
        if not success:
            stats['failed'] += 1
            stats['errors'].append(f"{safe_str(filename)}: {safe_str(message)}")
        else:
            stats['success'] += 1
        
        processor.close_file(save_changes=False)
        time.sleep(0.5)
    
    processor.quit()
    
    # 输出统计
    print(f"\n{'='*60}")
    print("处理完成!")
    print(f"总计: {stats['total']}")
    print(f"成功: {stats['success']}")
    print(f"失败: {stats['failed']}")
    
    if stats['errors']:
        print("\n错误详情:")
        for error in stats['errors']:
            print(f"  - {safe_str(error)}")
    
    print(f"{'='*60}")
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
