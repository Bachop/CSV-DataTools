# CSV-DataTools

Programmed by Silver

Silver comes back...

CSV-DataTools是一个多功能CSV数据处理工具，支持数据处理、分析和提供图形界面以实现可视化功能。该工具包含两个主要模块：数据处理模块(DATAPROCESS)和串口通信模块(SERIALCOM)。

## 开发环境

- Python 3.11.8
- PyQt5
- matplotlib
- numpy

## 程序结构

```
CSV-DataTools/
├── py/
│   ├── CORE/                 # 核
│   ├── DATAPROCESS/          # 数据处理
│   │   ├── CONTROLLER/       # 控制器
│   │   ├── FUNCTIONS/        # 功能
│   │   └── UI/               # 窗口界面
│   ├── SERIALCOM/            # 串口通信
│   │   ├── CONTROLLER/       # 控制器
│   │   ├── FUNCTIONS/        # 功能
│   │   └── UI/               # 窗口界面
│   ├── SETTINGS/             # 配置
│   └── main.py               # 入口
└── icon/CSV-DataTools.ico    # 图标
```

## 功能模块介绍

### DATAPROCESS（数据处理模块）

数据处理模块支持读取、写入CSV文件，进行数据统计分析和可视化绘图。

#### 主要功能：

1. **CSV文件读写**：
   - 支持多种编码格式的CSV文件读取
   - 可通过拖拽方式打开文件
   - 支持多标签页同时处理多个文件

2. **数据编辑**：
   - 可编辑表格数据
   - 支持列管理操作

3. **数据计算**：
   - 计算数据的均值、峰峰值、差值

4. **数据可视化**：
   - 曲线、散点图绘制
   - 支持批量绘图
   - 支持多图显示

5. **特殊功能**：
   - 数据进制转换
   - 状态变量检测
   - 稳态数据差值计算

### SERIALCOM（串口通信模块）

串口通信模块为串口调试助手功能，目前仍在开发中。

#### 主要功能（计划）：

1. 串口参数配置
2. 数据收发功能
3. 数据保存与导出