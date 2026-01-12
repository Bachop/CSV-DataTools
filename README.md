# *CSV-DataTools* 数据处理工具

基于 *Python* 开发的多功能 *CSV* 数据处理工具，支持数据处理、分析和提供图形界面以实现可视化功能。

*Programmed by [@Bachop](https://github.com/Bachop)*.
<!--<br>*Click* **[HERE](#更新日志)** *to view Date-based-Changelog*.--->

---

## 开发环境

- *Python 3.11.8*
- *PyQt5*
- *matplotlib*
- *numpy*

---

## 程序结构

```
CSV-DataTools/
├── icon/
│   └── CSV-DataTools.ico     # 图标
├── py/
│   ├── CORE/                 # 核
│   ├── DATAPROCESS/          # 数据处理
│   │   ├── CONTROLLER/
│   │   ├── FUNCTIONS/
│   │   └── UI/
│   ├── SETTINGS/             # 配置
│   └── main.py               # 入口
└── *files                    # 根目录文件
```

---

## 功能介绍

### DATAPROCESS   数据处理

创建、读取、写入 *CSV* 文件，进行数据统计分析和可视化绘图。

#### 主要功能：

1. ***CSV* 文件读写**：
   - 通过导入、拖拽方式打开文件
   - 支持多种编码格式的 *CSV* 文件读取
   - 支持 *CSV* 文件创建
   - 多标签页支持同时编辑多个文件


2. **数据编辑**：
   - 可编辑表格数据
   - 支持数据进制转换
   - 支持行、列管理操作
   - 支持筛选
      - 常规行筛选
      - 导入CSV格式的条件值文件以筛选条件值所在行

3. **统计量计算**：
   - 计算数据的均值、峰峰值、差值（不同列）
   - 支持批量计算

4. **数据可视化**：
   - 曲线、散点图绘制
   - 支持批量绘图

5. **特殊功能**（部分功能针对特定文件编写）：
   - *UID* 检索差值计算
      - 计算同一序列号在不同状态下数据的差值
   - 状态变量检测
      - 检测状态变量为特定值时对应传感器值的变化情况
   - 稳态数据差值计算
     - 计算传感器触发前后两种稳态的差值

---

**[README.md](#csv-datatools-逗号分隔值文件数据处理工具)** *Written by [@Bachop](https://github.com/Bachop "@Bachop"), Formally, 6th January 2026.*
<!--<br>Modified on DAY MONTH YEAR*--->