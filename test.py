import numpy as np
import matplotlib.pyplot as plt

# 示例数据（替换为你的实际数据）
data = [23, 25, 28, 29, 30, 31, 32, 33, 35, 36, 37, 38, 40, 42, 45]

# 计算统计量
mean = np.mean(data)
std_dev = np.std(data)  # 默认计算总体标准差（ddof=0）
print(f"均值: {mean:.2f}")
print(f"标准差: {std_dev:.2f}")

# 生成正态分布曲线数据
x = np.linspace(mean - 3*std_dev, mean + 3*std_dev, 100)
y = (1 / (std_dev * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean) / std_dev) ** 2)

# 绘制图形
plt.figure(figsize=(10, 6))
plt.hist(data, bins=15, density=True, alpha=0.6, color='skyblue', label='数据直方图')
plt.plot(x, y, 'r', linewidth=2, label='正态分布曲线')
plt.axvline(mean, color='g', linestyle='--', label=f'均值: {mean:.2f}')

# 添加标注
plt.title('数据分布与正态分布曲线', fontsize=14)
plt.xlabel('数值', fontsize=12)
plt.ylabel('概率密度', fontsize=12)
plt.legend()
plt.grid(alpha=0.3)

# 显示图形
plt.show()