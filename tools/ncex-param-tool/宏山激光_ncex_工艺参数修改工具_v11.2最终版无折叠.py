#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宏山激光 .ncex 工艺参数修改工具 v11.2
修复：Combobox IntVar绑定问题，改用StringVar存储数字
"""

import zipfile
import re
import shutil
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime


class HongshanNcexModifier:
    # 穿孔方式映射：数字 -> 显示文本
    # 基于切割软件实际行为修正
    PUNCH_METHODS = {0: "分段", 1: "渐进", 2: "变频"}
    # 反向映射：显示文本 -> 数字
    PUNCH_METHODS_REV = {"分段": 0, "渐进": 1, "变频": 2}
    
    def __init__(self, root):
        self.root = root
        self.root.title("宏山激光 .ncex 工艺参数修改工具 v11.2")
        self.root.geometry("1250x1050")

        self.file_path = tk.StringVar()
        self.layer_info = []
        self.target_layers = {}

        # === 大图形参数 ===
        self.big_cut_speed = tk.StringVar(value='1.9')
        self.big_cut_gas = tk.StringVar(value='氧气')
        self.big_cut_power = tk.StringVar(value='50')
        self.big_cut_frequency = tk.StringVar(value='5000')
        self.big_cut_pressure = tk.StringVar(value='0.7')
        self.big_cut_duty = tk.StringVar(value='60')
        self.big_cut_focus = tk.StringVar(value='-2')
        self.big_cut_height = tk.StringVar(value='1')
        self.big_punch_data = self.create_punch_vars()

        # === 小图形参数 ===
        self.small_cut_speed = tk.StringVar(value='1.9')
        self.small_cut_gas = tk.StringVar(value='氧气')
        self.small_cut_power = tk.StringVar(value='50')
        self.small_cut_frequency = tk.StringVar(value='5000')
        self.small_cut_pressure = tk.StringVar(value='0.7')
        self.small_cut_duty = tk.StringVar(value='60')
        self.small_cut_focus = tk.StringVar(value='-2')
        self.small_cut_height = tk.StringVar(value='1')
        self.small_punch_data = self.create_punch_vars()

        # === 打标层参数 ===
        self.mark_cut_speed = tk.StringVar(value='100')
        self.mark_cut_gas = tk.StringVar(value='空气')
        self.mark_cut_power = tk.StringVar(value='30')
        self.mark_cut_frequency = tk.StringVar(value='5000')
        self.mark_cut_pressure = tk.StringVar(value='10')
        self.mark_cut_duty = tk.StringVar(value='10')
        self.mark_cut_focus = tk.StringVar(value='0')
        self.mark_cut_height = tk.StringVar(value='10')

        self.create_widgets()

    def create_punch_vars(self):
        data = []
        for i in range(5):
            data.append({
                'enabled': tk.BooleanVar(value=(i == 0)),
                'power': tk.StringVar(value=str(100 - i*10)),
                'freq': tk.StringVar(value=str(5000 if i == 0 else 500)),
                'duty': tk.StringVar(value=str(100 - i*15)),
                'delay': tk.StringVar(value=str(200 + i*50)),
                'gas': tk.StringVar(value='氧气'),
                'pressure': tk.StringVar(value=str(10 - i)),
                'height': tk.StringVar(value=str(10 - i*2)),
                'focus': tk.StringVar(value='-2'),
                'punch_method': tk.StringVar(value='0'),
                'laser_off': tk.BooleanVar(value=False),
                'loff_pressure': tk.StringVar(value='10'),
                'loff_gas': tk.StringVar(value='氮气'),
                'loff_delay': tk.StringVar(value='200'),
                'loff_height': tk.StringVar(value='10'),
                'start_freq': tk.StringVar(value='500'),
                'end_freq': tk.StringVar(value='500'),
                'start_duty': tk.StringVar(value='50'),
                'end_duty': tk.StringVar(value='50'),
                'start_focus': tk.StringVar(value='-2'),
                'end_focus': tk.StringVar(value='-2'),
                'var_freq_time': tk.StringVar(value='1000'),
                'inc_speed': tk.StringVar(value='1000'),
            })
        return data

    def gas_to_num(self, gas):
        return {'空气': 0, '氮气': 1, '氧气': 2}.get(gas, 0)

    def create_widgets(self):
        tk.Label(self.root, text="v11.2 完整修正版", 
                 font=('微软雅黑', 14, 'bold'), fg='red').pack(pady=5)

        file_frame = tk.Frame(self.root)
        file_frame.pack(fill='x', padx=20, pady=3)
        tk.Entry(file_frame, textvariable=self.file_path, width=80).pack(side='left', padx=5)
        tk.Button(file_frame, text="浏览...", command=self.browse_file, width=10).pack(side='left', padx=5)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="分析文件", command=self.analyze, bg='#2196F3', fg='white', width=15, height=2).pack(side='left', padx=10)
        tk.Button(btn_frame, text="修改参数", command=self.modify, bg='#4CAF50', fg='white', width=15, height=2).pack(side='left', padx=10)

        main_container = tk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=15, pady=5)

        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        big_frame = tk.LabelFrame(scrollable_frame, text="【大图形】主切割 + 五级穿孔", padx=10, pady=10)
        big_frame.pack(fill='x', pady=5)
        self.create_cut_widgets(big_frame, 'big')
        self.create_punch_widgets(big_frame, self.big_punch_data)

        small_frame = tk.LabelFrame(scrollable_frame, text="【小图形】主切割 + 五级穿孔", padx=10, pady=10)
        small_frame.pack(fill='x', pady=5)
        self.create_cut_widgets(small_frame, 'small')
        self.create_punch_widgets(small_frame, self.small_punch_data)

        mark_frame = tk.LabelFrame(scrollable_frame, text="【打标层】仅主切割", padx=10, pady=10)
        mark_frame.pack(fill='x', pady=5)
        self.create_cut_widgets(mark_frame, 'mark')

        log_frame = tk.LabelFrame(self.root, text="日志", padx=5, pady=5)
        log_frame.pack(fill='x', padx=15, pady=5)
        self.log_text = tk.Text(log_frame, height=6, wrap='word', font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True)

    def create_cut_widgets(self, parent, prefix):
        cut_frame = tk.LabelFrame(parent, text="主切割参数", padx=10, pady=8)
        cut_frame.pack(fill='x', pady=5)

        vars_map = {
            'big': [self.big_cut_speed, self.big_cut_power, self.big_cut_frequency, self.big_cut_duty,
                   self.big_cut_pressure, self.big_cut_gas, self.big_cut_focus, self.big_cut_height],
            'small': [self.small_cut_speed, self.small_cut_power, self.small_cut_frequency, self.small_cut_duty,
                     self.small_cut_pressure, self.small_cut_gas, self.small_cut_focus, self.small_cut_height],
            'mark': [self.mark_cut_speed, self.mark_cut_power, self.mark_cut_frequency, self.mark_cut_duty,
                    self.mark_cut_pressure, self.mark_cut_gas, self.mark_cut_focus, self.mark_cut_height]
        }
        
        labels = ["切割速度:", "功率%:", "频率:", "占空比:", "气压:", "气体:", "焦点:", "高度:"]
        vars_list = vars_map[prefix]
        
        for i, (label, var) in enumerate(zip(labels, vars_list)):
            row, col = i // 4, (i % 4) * 2
            tk.Label(cut_frame, text=label, width=10, anchor='e').grid(row=row, column=col, pady=4, padx=2)
            if '气体' in label:
                ttk.Combobox(cut_frame, textvariable=var, values=['空气', '氮气', '氧气'], width=10, state='readonly').grid(row=row, column=col+1)
            else:
                tk.Entry(cut_frame, textvariable=var, width=10).grid(row=row, column=col+1)

    def create_punch_widgets(self, parent, punch_data):
        punch_container = tk.LabelFrame(parent, text="五级穿孔参数", padx=8, pady=8)
        punch_container.pack(fill='x', pady=5)

        colors = ['#2E7D32', '#1565C0', '#EF6C00', '#6A1B9A', '#C62828']
        
        for i in range(5):
            d = punch_data[i]
            frame = tk.LabelFrame(punch_container, text="第" + str(i+1) + "级穿孔", padx=4, pady=2, fg=colors[i])
            frame.pack(fill='x', padx=2, pady=2)
            
            row1 = tk.Frame(frame)
            row1.pack(fill='x', pady=1)
            tk.Checkbutton(row1, variable=d['enabled'], text="启用").pack(side='left', padx=2)
            
            # FIX: 穿孔方式使用文本显示，但存储数字字符串
            tk.Label(row1, text="方式:", width=6).pack(side='left', padx=(10,0))
            # values 用中文文本，但 textvariable 绑定 StringVar 存数字
            cb = ttk.Combobox(row1, width=8, state='readonly')
            cb['values'] = list(self.PUNCH_METHODS.values())  # ["分段", "变频", "渐进"]
            cb.pack(side='left', padx=2)
            
            # 绑定变量和转换
            def on_method_change(event, var=d['punch_method'], combo=cb):
                # 把中文转成数字存到 StringVar
                text = combo.get()
                num = self.PUNCH_METHODS_REV.get(text, 0)
                var.set(str(num))
            
            def sync_method_display(var=d['punch_method'], combo=cb):
                # 从 StringVar 的数字同步到 Combobox 显示
                try:
                    num = int(var.get())
                    combo.set(self.PUNCH_METHODS.get(num, "分段"))
                except:
                    combo.set("分段")
            
            cb.bind('<<ComboboxSelected>>', on_method_change)
            # 初始化显示
            sync_method_display()
            
            row2 = tk.Frame(frame)
            row2.pack(fill='x', pady=1)
            for label, var, w in [("功率:", d['power'], 5), ("频率:", d['freq'], 6), ("占空比:", d['duty'], 5), ("延时:", d['delay'], 6)]:
                tk.Label(row2, text=label).pack(side='left', padx=(8 if label != "功率:" else 2, 0))
                tk.Entry(row2, textvariable=var, width=w).pack(side='left', padx=1)
            
            row3 = tk.Frame(frame)
            row3.pack(fill='x', pady=1)
            tk.Label(row3, text="气体:").pack(side='left', padx=2)
            ttk.Combobox(row3, textvariable=d['gas'], values=['空气', '氮气', '氧气'], width=5, state='readonly').pack(side='left', padx=1)
            for label, var in [("气压:", d['pressure']), ("高度:", d['height']), ("焦点:", d['focus'])]:
                tk.Label(row3, text=label).pack(side='left', padx=(8,0))
                tk.Entry(row3, textvariable=var, width=5).pack(side='left', padx=1)
            
            row4 = tk.Frame(frame)
            row4.pack(fill='x', pady=1)
            tk.Checkbutton(row4, variable=d['laser_off'], text="停光").pack(side='left', padx=2)
            for label, var in [("停光气压:", d['loff_pressure']), ("停光气体:", d['loff_gas']), ("停光延时:", d['loff_delay']), ("停光高度:", d['loff_height'])]:
                if '气体' in label:
                    tk.Label(row4, text=label).pack(side='left', padx=(8,0))
                    ttk.Combobox(row4, textvariable=var, values=['空气', '氮气', '氧气'], width=5, state='readonly').pack(side='left', padx=1)
                else:
                    tk.Label(row4, text=label).pack(side='left', padx=(8,0))
                    tk.Entry(row4, textvariable=var, width=5).pack(side='left', padx=1)

            # === 第5行：变频/渐进参数 ===
            row5 = tk.Frame(frame)
            row5.pack(fill='x', pady=1)
            tk.Label(row5, text="起频:", width=6).pack(side='left', padx=2)
            tk.Entry(row5, textvariable=d['start_freq'], width=6).pack(side='left', padx=1)
            tk.Label(row5, text="终频:", width=6).pack(side='left', padx=(6,0))
            tk.Entry(row5, textvariable=d['end_freq'], width=6).pack(side='left', padx=1)
            tk.Label(row5, text="变频时间:", width=8).pack(side='left', padx=(6,0))
            tk.Entry(row5, textvariable=d['var_freq_time'], width=6).pack(side='left', padx=1)
            tk.Label(row5, text="渐进速度:", width=8).pack(side='left', padx=(6,0))
            tk.Entry(row5, textvariable=d['inc_speed'], width=6).pack(side='left', padx=1)

            # === 第6行：变频占空比 + 变频焦距 ===
            row6 = tk.Frame(frame)
            row6.pack(fill='x', pady=1)
            tk.Label(row6, text="起始占空比:", width=10).pack(side='left', padx=2)
            tk.Entry(row6, textvariable=d['start_duty'], width=6).pack(side='left', padx=1)
            tk.Label(row6, text="终止占空比:", width=10).pack(side='left', padx=(6,0))
            tk.Entry(row6, textvariable=d['end_duty'], width=6).pack(side='left', padx=1)
            tk.Label(row6, text="起始焦距:", width=8).pack(side='left', padx=(6,0))
            tk.Entry(row6, textvariable=d['start_focus'], width=6).pack(side='left', padx=1)
            tk.Label(row6, text="终止焦距:", width=8).pack(side='left', padx=(6,0))
            tk.Entry(row6, textvariable=d['end_focus'], width=6).pack(side='left', padx=1)

    def log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert('end', "[" + timestamp + "] " + message + "\n")
        self.log_text.see('end')
        self.root.update()

    def browse_file(self):
        filename = filedialog.askopenfilename(title="选择.ncex文件", filetypes=[("ncex文件", "*.ncex")])
        if filename:
            self.file_path.set(filename)
            self.log("选择文件: " + os.path.basename(filename))

    def analyze(self):
        file_path = self.file_path.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("错误", "请先选择文件")
            return
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                for item in zf.infolist():
                    if item.filename.endswith('Technology.xml'):
                        data = zf.read(item.filename)
                        xml_content = data.decode('utf-8')
                        
                        self.layer_info = []
                        self.target_layers = {}
                        
                        pos = 0
                        count = 0
                        while True:
                            start = xml_content.find('<Layer color="', pos)
                            if start == -1:
                                break
                            
                            c_start = start + len('<Layer color="')
                            c_end = xml_content.find('"', c_start)
                            color = xml_content[c_start:c_end]
                            
                            p_start = xml_content.find('params="', start)
                            p_content_start = p_start + len('params="')
                            p_end = xml_content.find('"/>', p_content_start)
                            params = xml_content[p_content_start:p_end]
                            layer_end = p_end + len('"/>')
                            
                            idx_match = re.search(r'\[(\d+)\]', params)
                            idx = idx_match.group(1) if idx_match else '?'
                            
                            has_cut = 'Cut=' in params
                            has_mark = 'Mark=' in params
                            name_match = re.search(r'Name=\[\[(.*?)\]\]', params)
                            name = name_match.group(1) if name_match else ''
                            
                            layer_type = "其他"
                            target_key = None
                            
                            if color == '60395' and has_cut and '大图形' in name:
                                layer_type = "🎯【目标】大图形"
                                target_key = 'big'
                            elif color == '16776960' and has_cut and '小图形' in name:
                                layer_type = "🎯【目标】小图形"
                                target_key = 'small'
                            elif color == '5193599' and has_cut:
                                layer_type = "🎯【目标】打标层"
                                target_key = 'mark'
                            elif color == '60' and has_mark:
                                layer_type = "⚪全局参数"
                            elif has_cut:
                                layer_type = "🔴切割层-" + name
                            elif has_mark:
                                layer_type = "🔵打标层"
                            
                            info = {
                                'seq': count,
                                'idx': idx,
                                'color': color,
                                'type': layer_type,
                                'target_key': target_key,
                                'start': start,
                                'end': layer_end,
                                'params': params
                            }
                            
                            self.layer_info.append(info)
                            if target_key:
                                self.target_layers[target_key] = count
                            
                            count += 1
                            pos = layer_end
                        
                        self.log("=" * 50)
                        self.log("发现 " + str(count) + " 个Layer:")
                        for info in self.layer_info:
                            marker = " <<< 修改目标" if info['target_key'] else ""
                            self.log("  [" + str(info['seq']) + "] 颜色=" + info['color'] + " " + info['type'] + marker)
                        
                        found = []
                        for key, name in [('big', '大图形'), ('small', '小图形'), ('mark', '打标层')]:
                            if key in self.target_layers:
                                found.append(name + "[" + str(self.target_layers[key]) + "]")
                        self.log("✅ 目标图层: " + ", ".join(found) if found else "❌ 未找到目标图层")
                        
                        return
                        
        except Exception as e:
            self.log("错误: " + str(e))
            import traceback
            self.log(traceback.format_exc())

    def modify(self):
        file_path = self.file_path.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("错误", "请先选择文件")
            return
        
        if not self.target_layers:
            messagebox.showerror("错误", "请先分析文件")
            return
        
        try:
            layers_to_modify = {}
            
            if 'big' in self.target_layers:
                layers_to_modify['big'] = {
                    'cut': {
                        'speed': float(self.big_cut_speed.get()),
                        'gas': self.gas_to_num(self.big_cut_gas.get()),
                        'power': float(self.big_cut_power.get()),
                        'frequency': int(self.big_cut_frequency.get()),
                        'pressure': float(self.big_cut_pressure.get()),
                        'duty': int(self.big_cut_duty.get()),
                        'focus': float(self.big_cut_focus.get()),
                        'height': float(self.big_cut_height.get()),
                    },
                    'punch': self.collect_punch_data(self.big_punch_data)
                }
            
            if 'small' in self.target_layers:
                layers_to_modify['small'] = {
                    'cut': {
                        'speed': float(self.small_cut_speed.get()),
                        'gas': self.gas_to_num(self.small_cut_gas.get()),
                        'power': float(self.small_cut_power.get()),
                        'frequency': int(self.small_cut_frequency.get()),
                        'pressure': float(self.small_cut_pressure.get()),
                        'duty': int(self.small_cut_duty.get()),
                        'focus': float(self.small_cut_focus.get()),
                        'height': float(self.small_cut_height.get()),
                    },
                    'punch': self.collect_punch_data(self.small_punch_data)
                }
            
            if 'mark' in self.target_layers:
                layers_to_modify['mark'] = {
                    'cut': {
                        'speed': float(self.mark_cut_speed.get()),
                        'gas': self.gas_to_num(self.mark_cut_gas.get()),
                        'power': float(self.mark_cut_power.get()),
                        'frequency': int(self.mark_cut_frequency.get()),
                        'pressure': float(self.mark_cut_pressure.get()),
                        'duty': int(self.mark_cut_duty.get()),
                        'focus': float(self.mark_cut_focus.get()),
                        'height': float(self.mark_cut_height.get()),
                    },
                    'punch': []
                }
            
            self.log("=" * 50)
            for key, data in layers_to_modify.items():
                name = {'big': '大图形', 'small': '小图形', 'mark': '打标层'}[key]
                punch_count = len(data['punch'])
                self.log("修改 " + name + ": 主切割 + " + (str(punch_count) + "级穿孔" if punch_count > 0 else "无穿孔"))
            
            success = self.process_file(file_path, layers_to_modify)
            
            if success:
                msg = "修改完成！\n"
                for key in layers_to_modify:
                    msg += {'big': '✅ 大图形\n', 'small': '✅ 小图形\n', 'mark': '✅ 打标层\n'}[key]
                messagebox.showinfo("成功", msg)
            else:
                self.log("处理失败")
                
        except Exception as e:
            self.log("错误: " + str(e))
            import traceback
            self.log(traceback.format_exc())

    def collect_punch_data(self, punch_vars):
        result = []
        for i, d in enumerate(punch_vars):
            if d['enabled'].get():
                # FIX: punch_method 从 StringVar 取字符串转整数
                try:
                    method_val = int(d['punch_method'].get())
                except ValueError:
                    method_val = 0
                
                result.append({
                    'level': i,
                    'power': float(d['power'].get()),
                    'freq': int(d['freq'].get()),
                    'duty': int(d['duty'].get()),
                    'delay': int(d['delay'].get()),
                    'gas': self.gas_to_num(d['gas'].get()),
                    'pressure': float(d['pressure'].get()),
                    'height': float(d['height'].get()),
                    'focus': float(d['focus'].get()),
                    'punch_method': method_val,
                    'laser_off': 'true' if d['laser_off'].get() else 'false',
                    'loff_pressure': float(d['loff_pressure'].get()),
                    'loff_gas': self.gas_to_num(d['loff_gas'].get()),
                    'loff_delay': int(d['loff_delay'].get()),
                    'loff_height': float(d['loff_height'].get()),
                    'start_freq': int(d['start_freq'].get()),
                    'end_freq': int(d['end_freq'].get()),
                    'start_duty': int(d['start_duty'].get()),
                    'end_duty': int(d['end_duty'].get()),
                    'start_focus': float(d['start_focus'].get()),
                    'end_focus': float(d['end_focus'].get()),
                    'var_freq_time': int(d['var_freq_time'].get()),
                    'inc_speed': int(d['inc_speed'].get()),
                })
        return result

    def process_file(self, file_path, layers_to_modify):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = file_path + ".备份_" + timestamp
        shutil.copy2(file_path, backup_path)
        self.log("已备份: " + os.path.basename(backup_path))
        
        output_path = file_path.replace('.ncex', '_已修改.ncex')
        
        with zipfile.ZipFile(file_path, 'r') as zf_in:
            with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf_out:
                for item in zf_in.infolist():
                    data = zf_in.read(item.filename)
                    if item.filename.endswith('Technology.xml'):
                        xml_content = data.decode('utf-8')
                        modified = self.modify_xml(xml_content, layers_to_modify)
                        data = modified.encode('utf-8')
                    zf_out.writestr(item, data)
        
        self.log("完成: " + os.path.basename(output_path))
        return True

    def find_block_end(self, content, start_pos):
        """找到从start_pos开始的 { } 块的结束位置（考虑嵌套）"""
        brace_count = 0
        i = start_pos
        while i < len(content):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return i
            i += 1
        return -1

    def find_balanced_block(self, content, key):
        """
        找到 key= 后面的 { } 块
        确保 key 是独立的（前面不是字母、数字或下划线）
        返回 (start_pos_of_value, end_pos_of_block)
        start_pos_of_value 是 { 的位置
        end_pos_of_block 是 闭合 } 的位置
        """
        pos = 0
        while True:
            pos = content.find(key, pos)
            if pos == -1:
                return -1, -1

            # 检查 key 前面是否是合法的分隔符（不能是字母、数字、下划线）
            if pos > 0:
                prev_char = content[pos - 1]
                if prev_char.isalnum() or prev_char == '_':
                    pos += 1
                    continue

            # 找到 key 后面的第一个 {
            brace_start = content.find('{', pos)
            if brace_start == -1:
                return -1, -1

            brace_end = self.find_block_end(content, brace_start)
            return brace_start, brace_end
    def modify_xml(self, xml_content, layers_to_modify):
        new_xml = xml_content
        
        for key in ['mark', 'small', 'big']:
            if key not in layers_to_modify:
                continue
            
            layer_seq = self.target_layers[key]
            info = self.layer_info[layer_seq]
            layer_start = info['start']
            layer_end = info['end']
            params_content = info['params']
            data = layers_to_modify[key]
            
            self.log("-" * 40)
            self.log("修改 " + {'big': '大图形', 'small': '小图形', 'mark': '打标层'}[key] + 
                     " 顺序[" + str(layer_seq) + "] 索引[" + info['idx'] + "]")
            
            # === 1. 修改 Cut[0] 主切割参数 ===
            # 找到 Cut= 块
            cut_brace_start, cut_brace_end = self.find_balanced_block(params_content, 'Cut=')
            if cut_brace_start == -1:
                self.log("  ⚠️ 未找到 Cut= 块")
                continue
            
            cut_block = params_content[cut_brace_start:cut_brace_end+1]
            
            # 在 Cut 块内找到 [0]=
            array0_pos = cut_block.find('[0]=')
            if array0_pos == -1:
                self.log("  ⚠️ 未找到 Cut[0]")
                continue
            
            # 找到 [0]= 后面的 { 块
            array0_brace_start = cut_block.find('{', array0_pos)
            array0_brace_end = self.find_block_end(cut_block, array0_brace_start)
            if array0_brace_end == -1:
                self.log("  ⚠️ 未找到 Cut[0]的闭合 }")
                continue
            
            # 提取并修改 Cut[0] 内容
            original_array0 = cut_block[array0_pos:array0_brace_end+1]
            array0_content = original_array0
            
            cut_params = data['cut']
            array0_content = re.sub(r'Speed=\d+', 'Speed=' + str(int(cut_params['speed']*1000)), array0_content)
            array0_content = re.sub(r'Power=[\d.]+', 'Power=' + str(cut_params['power']), array0_content)
            array0_content = re.sub(r'Frequency=\d+', 'Frequency=' + str(cut_params['frequency']), array0_content)
            array0_content = re.sub(r'DutyCycle=\d+', 'DutyCycle=' + str(cut_params['duty']), array0_content)
            array0_content = re.sub(r'Pressure=[\d.]+', 'Pressure=' + str(cut_params['pressure']), array0_content)
            array0_content = re.sub(r'Gas=\d+', 'Gas=' + str(cut_params['gas']), array0_content)
            array0_content = re.sub(r'FocusPos=[\d.-]+', 'FocusPos=' + str(cut_params['focus']), array0_content)
            array0_content = re.sub(r'Height=[\d.]+', 'Height=' + str(cut_params['height']), array0_content)
            
            if array0_content != original_array0:
                cut_block = cut_block[:array0_pos] + array0_content + cut_block[array0_brace_end+1:]
                self.log("  ✓ Cut[0]主切割已更新")
            
            # 重建 Cut= 块到 params_content
            new_params = params_content[:cut_brace_start] + cut_block + params_content[cut_brace_end+1:]
            
            # === 2. 修改 Punch 块 ===
            punch_data = data['punch']
            
            # 找到 Punch= 块
            punch_key_pos = new_params.find('Punch=')
            if punch_key_pos != -1:
                punch_brace_start, punch_brace_end = self.find_balanced_block(new_params, 'Punch=')
                if punch_brace_start != -1 and punch_brace_end != -1:
                    # 生成新的 Punch 块
                    new_punch_block = self.generate_punch_block(punch_data)
                    new_params = new_params[:punch_brace_start] + new_punch_block + new_params[punch_brace_end+1:]
                    if punch_data:
                        self.log("  ✓ Punch块已更新: " + str(len(punch_data)) + "级启用")
                    else:
                        self.log("  ✓ Punch块已清空 (无穿孔)")
                else:
                    self.log("  ⚠️ 找到Punch=但无法定位块范围")
            else:
                self.log("  ℹ️ 未找到Punch=块 (可能无穿孔功能)")
            
            # === 3. 重建 Layer 标签 ===
            original_tag = new_xml[layer_start:layer_end]
            color_match = re.search(r'color="(\d+)"', original_tag)
            if color_match:
                color = color_match.group(1)
                new_layer_tag = '<Layer color="' + color + '" params="' + new_params + '"/>'
                new_xml = new_xml[:layer_start] + new_layer_tag + new_xml[layer_end:]
                self.log("  ✓ Layer重建完成")
        
        self.log("=" * 50)
        self.log("✓ XML修改完成")
        return new_xml

    def generate_punch_block(self, punch_data):
        """
        生成 Punch= 后面的 { ... } 块内容
        结构: {
            [0]={Type=X, [0]={...}, [1]={...}, ... [4]={...} },
            [1]={Type=0, [0]={...}, ... [4]={...} },
            ...
            [8]={Type=0, [0]={...}, ... [4]={...} }
        }
        """
        groups = []
        
        # [0] 组：实际的穿孔参数
        if punch_data:
            enabled_count = len(punch_data)
            type_value = enabled_count  # 1-5
            
            stages = []
            for s in range(5):
                if s < enabled_count:
                    p = punch_data[s]
                else:
                    p = punch_data[-1]  # 用最后一个启用的参数填充
                
                stage = (
                    "[" + str(s) + "]={"
                    "LaserOffGasOnPressure=" + str(p['loff_pressure']) + ","
                    "LaserOffGasOn=" + p['laser_off'] + ","
                    "FocusPos=" + str(p['focus']) + ","
                    "Frequency=" + str(p['freq']) + ","
                    "Height=" + str(p['height']) + ","
                    "PunchMethod=" + str(p['punch_method']) + ","
                    "EndDutyCycle=" + str(p['end_duty']) + ","
                    "DutyCycle=" + str(p['duty']) + ","
                    "StartDutyCycle=" + str(p['start_duty']) + ","
                    "EndFocusPos=" + str(p['end_focus']) + ","
                    "LaserOffGasOnDelay=" + str(p['loff_delay']) + ","
                    "Delay=" + str(p['delay']) + ","
                    "Pressure=" + str(p['pressure']) + ","
                    "StartFrequency=" + str(p['start_freq']) + ","
                    "VariableFrequencyTime=" + str(p['var_freq_time']) + ","
                    "LaserOffGasOnGas=" + str(p['loff_gas']) + ","
                    "Gas=" + str(p['gas']) + ","
                    "IncrementalSpeed=" + str(p['inc_speed']) + ","
                    "StartFocusPos=" + str(p['start_focus']) + ","
                    "LaserOffGasOnType=0,"
                    "Power=" + str(p['power']) + ","
                    "EndFrequency=" + str(p['end_freq']) + ","
                    "LaserOffGasOnHeight=" + str(p['loff_height']) + "}"
                )
                stages.append(stage)
            
            group0 = "[0]={Type=" + str(type_value) + "," + ",".join(stages) + "}"
            groups.append(group0)
        else:
            # 无穿孔：[0] 组也是 Type=0
            empty_stages = []
            for s in range(5):
                empty_stages.append(
                    "[" + str(s) + "]={"
                    "LaserOffGasOnPressure=10,LaserOffGasOn=false,FocusPos=0,Frequency=5000,Height=20,"
                    "PunchMethod=0,EndDutyCycle=100,DutyCycle=100,StartDutyCycle=100,EndFocusPos=0,"
                    "LaserOffGasOnDelay=200,Delay=200,Pressure=10,StartFrequency=500,VariableFrequencyTime=1000,"
                    "LaserOffGasOnGas=0,Gas=0,IncrementalSpeed=1000,StartFocusPos=0,LaserOffGasOnType=0,"
                    "Power=100,EndFrequency=500,LaserOffGasOnHeight=0}"
                )
            groups.append("[0]={Type=0," + ",".join(empty_stages) + "}")
        
        # [1]-[8] 组：始终 Type=0 空参数
        for g in range(1, 9):
            empty_stages = []
            for s in range(5):
                empty_stages.append(
                    "[" + str(s) + "]={"
                    "LaserOffGasOnPressure=10,LaserOffGasOn=false,FocusPos=0,Frequency=5000,Height=20,"
                    "PunchMethod=0,EndDutyCycle=100,DutyCycle=100,StartDutyCycle=100,EndFocusPos=0,"
                    "LaserOffGasOnDelay=200,Delay=200,Pressure=10,StartFrequency=500,VariableFrequencyTime=1000,"
                    "LaserOffGasOnGas=0,Gas=0,IncrementalSpeed=1000,StartFocusPos=0,LaserOffGasOnType=0,"
                    "Power=100,EndFrequency=500,LaserOffGasOnHeight=0}"
                )
            groups.append("[" + str(g) + "]={Type=0," + ",".join(empty_stages) + "}")
        
        return "{" + ",".join(groups) + "}"




def main():
    root = tk.Tk()
    app = HongshanNcexModifier(root)
    root.mainloop()


if __name__ == '__main__':
    main()
