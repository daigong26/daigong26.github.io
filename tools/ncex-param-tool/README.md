# 宏山激光 NCEX 工艺参数修改工具

## 解决什么现场问题

宏山 NCEX 系统换材料/换厚度时，需要批量修改功率、速度、气压等 10+ 个参数，手工修改 50 个文件耗时 2 小时且易错，无修改留痕。

## 功能

- 读取 NCEX 工艺文件，解析参数结构
- 按规则批量替换指定参数（如：功率 3000→3500）
- 修改前自动备份原文件
- 生成修改日志，记录谁、何时、改了什么

## 技术点

- Python 文件读写与正则解析
- 参数映射表管理（材料-厚度-参数对应关系）
- 批量文件遍历与异常处理

## 使用示例

```bash
python ncex_param_tool.py --input-dir ./nc_files/ --param 功率=3500 --material 碳钢
## 代码文件

- [宏山激光_ncex_工艺参数修改工具_v11.2最终版无折叠.py](https://github.com/daigong26/daigong26.github.io/blob/main/tools/ncex-param-tool/宏山激光_ncex_工艺参数修改工具_v11.2最终版无折叠.py) — 最终版
