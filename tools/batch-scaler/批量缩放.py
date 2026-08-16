#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SolidWorks 批量处理脚本 - 基于成功版本（修复重复问题）
"""

import os
import sys
import time
import builtins
import win32com.client
import pythoncom
from pathlib import Path

# ============================================================
# 强制恢复内置 str 函数
# ============================================================
_str = builtins.str

def safe_str(obj):
    return _str(obj)

# ============================================================
# 手动输入路径
# ============================================================
def get_folder_path():
    print("\n" + "=" * 60)
    print("请输入文件夹路径")
    print("示例：E:\\360MoveData\\Users\\Administrator\\Desktop")
    print("=" * 60)
    print("路径：", end="")
    
    path = input().strip().strip('"').strip("'")
    
    if not path:
        print("路径为空！")
        return None
    
    path = os.path.normpath(path)
    
    if not os.path.exists(path):
        print(f"路径不存在：{safe_str(path)}")
        return None
    
    return path

# ============================================================
# 配置
# ============================================================
CONFIG = {
    'file_extensions': ['.SLDPRT'],  # 只保留大写，避免重复匹配
    'scale_factor': 1.0,
    'solidworks_version': 'SldWorks.Application.30',
    'visible': True,
}

# ============================================================
# 统计
# ============================================================
stats = {
    'total': 0,
    'success': 0,
    'failed': 0,
    'errors': []
}

# ============================================================
# 常量
# ============================================================
class swConst:
    swDocPART = 1
    swOpenDocOptions_Silent = 1
    swBodyType_e_swSolidBody = 0

# ============================================================
# 核心类
# ============================================================
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
            
            # 关键：使用 _str(file_path)
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
                return False, "无法打开文件（可能文件损坏或版本不兼容）"
            
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
                    return False, f"获取实体失败: {safe_str(e)}, {safe_str(e2)}"
            
            if bodies_variant is None:
                return False, "未找到任何实体（零件可能为空）"
            
            try:
                if hasattr(bodies_variant, '__len__'):
                    body_count = len(bodies_variant)
                    bodies_list = list(bodies_variant)
                else:
                    body_count = 1
                    bodies_list = [bodies_variant]
            except Exception as e:
                return False, f"解析实体数组失败: {safe_str(e)}"
            
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
                        print(f"        警告: 选择实体失败: {safe_str(e)}")
                    
                    success_count += 1
                        
                except Exception as body_error:
                    print(f"      ✗ 处理实体 {i+1} 时出错: {safe_str(body_error)}")
            
            if success_count > 0:
                return True, f"成功处理 {success_count}/{body_count} 个实体"
            else:
                return False, "未能成功处理任何实体"
            
        except Exception as error_info:
            return False, f"缩放失败: {safe_str(error_info)}"
    
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


# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 60)
    print("SolidWorks 批量处理工具")
    print("=" * 60)
    
    # 获取路径
    source_folder = get_folder_path()
    if not source_folder:
        input("按回车键退出...")
        return
    
    print(f"已选择: {safe_str(source_folder)}")
    
    # 检查路径
    source_path = Path(source_folder)
    if not source_path.exists():
        print(f"错误: 路径不存在")
        input("按回车键退出...")
        return
    
    # 获取文件 - 关键修复：使用 set 去重，只保留大写扩展名
    files_to_process = []
    seen_names = set()
    
    # 只使用一种扩展名匹配，避免重复
    for file_path in source_path.glob('*.SLDPRT'):
        name = file_path.name
        if name not in seen_names:
            seen_names.add(name)
            files_to_process.append(file_path)
    
    # 排序
    files_to_process.sort(key=lambda x: x.name)
    
    if not files_to_process:
        print("未找到任何 SLDPRT 文件")
        input("按回车键退出...")
        return
    
    stats['total'] = len(files_to_process)
    print(f"找到 {len(files_to_process)} 个文件待处理\n")
    
    # 显示文件列表确认
    print("文件列表：")
    for i, f in enumerate(files_to_process, 1):
        print(f"  {i}. {f.name}")
    
    print(f"\n确认处理这 {len(files_to_process)} 个文件？(y/n)：", end="")
    if input().strip().lower() != 'y':
        print("已取消")
        return
    
    # 创建处理器
    processor = SolidWorksBatchProcessor()
    
    if not processor.connect():
        input("按回车键退出...")
        return
    
    # 处理文件
    for idx, file_path in enumerate(files_to_process, 1):
        filename = file_path.name
        print(f"\n处理: {safe_str(filename)}")
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
    print("\n" + "=" * 60)
    print("处理完成!")
    print(f"总计: {stats['total']}")
    print(f"成功: {stats['success']}")
    print(f"失败: {stats['failed']}")
    
    if stats['errors']:
        print("\n错误详情:")
        for error in stats['errors']:
            print(f"  - {safe_str(error)}")
    
    print("=" * 60)
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
