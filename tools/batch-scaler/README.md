# 图纸批量缩放工具

## 解决什么现场问题

外协图纸或客户图纸比例不统一，导入套料软件前需要统一缩放比例，手工逐个修改效率低。

## 功能

- 批量读取 DXF 文件
- 按指定比例（如 1:1.05、1:0.95）统一缩放
- 保留图层、标注、线型信息
- 输出到新目录，不覆盖原文件

## 技术点

- DXF 坐标矩阵变换
- 批量文件处理与目录管理
- 版本迭代：从单文件 → 多文件 → 正规版（异常处理+日志）

## 使用示例

```bash
python batch_scaler.py --input ./drawings/ --scale 1.05 --output ./scaled/
```
## 代码文件

- [批量缩放正规版.py](https://github.com/daigong26/daigong26.github.io/blob/main/tools/batch-scaler/批量缩放正规版.py) — 主程序
