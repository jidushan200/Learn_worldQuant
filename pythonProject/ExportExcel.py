import os
import glob
import pandas as pd
import numpy as np


def 获取最新CSV文件(目录路径):
    """
    获取指定目录中最新的 CSV 文件路径
    :param 目录路径: 目标文件夹路径
    :return: 最新的 CSV 文件路径或 None（如果没有 CSV 文件）
    """
    # 搜索目录中的所有 CSV 文件
    csv文件列表 = glob.glob(os.path.join(目录路径, "*.csv"))

    if not csv文件列表:
        print(f"目录 '{目录路径}' 中没有找到 CSV 文件。")
        return None

    # 按最后修改时间排序，获取最新的文件
    最新文件 = max(csv文件列表, key=os.path.getmtime)
    return 最新文件


def 计算ATR并生成信号(文件路径, 输出路径):
    """
    计算 ATR 和加仓信号，并将结果保存到新的 CSV 文件
    :param 文件路径: 输入 CSV 文件路径
    :param 输出路径: 输出 CSV 文件路径
    """
    print(f"开始加载文件: {文件路径}")

    # 加载 CSV 文件
    try:
        数据 = pd.read_csv(文件路径)
        print(f"文件 {文件路径} 成功加载！")
    except Exception as e:
        print(f"加载文件失败: {e}")
        return

    # 检查是否包含必要的列
    必需列 = {'Date', 'Price', 'High', 'Low'}
    if not 必需列.issubset(数据.columns):
        print(f"文件 {文件路径} 缺少必要的列：{必需列 - set(数据.columns)}")
        return

    # 确保列名没有多余的空格
    数据.columns = 数据.columns.str.strip()

    # 重命名列以符合计算规范
    数据.rename(columns={'Price': '收盘价'}, inplace=True)

    # 转换相关列为数值类型
    for 列名 in ['收盘价', 'High', 'Low', 'Open']:
        if 列名 in 数据.columns:
            数据[列名] = 数据[列名].replace(',', '', regex=True)  # 移除可能的逗号分隔符
            数据[列名] = pd.to_numeric(数据[列名], errors='coerce')  # 转换为浮点型，无法转换的值将变为 NaN

    # 检查是否有 NaN，并提示用户
    if 数据[['收盘价', 'High', 'Low']].isnull().any().any():
        print("警告：数据中存在无法转换为数值的值，请检查输入文件！")
        print(数据[数据[['收盘价', 'High', 'Low']].isnull().any(axis=1)])  # 打印有问题的行

    # 计算真实波幅 (TR)
    print("开始计算真实波幅 (TR)...")
    数据['前一日收盘价'] = 数据['收盘价'].shift(1)  # 前一日收盘价
    数据['最高-最低'] = 数据['High'] - 数据['Low']  # 当日最高价减最低价
    数据['最高-前收盘'] = abs(数据['High'] - 数据['前一日收盘价'])  # 当日最高价减前一日收盘价
    数据['最低-前收盘'] = abs(数据['Low'] - 数据['前一日收盘价'])  # 当日最低价减前一日收盘价
    数据['真实波幅'] = 数据[['最高-最低', '最高-前收盘', '最低-前收盘']].max(axis=1)

    # 计算 14 日平均 ATR
    print("开始计算 14 日平均 ATR...")
    N = 14
    数据['ATR'] = 数据['真实波幅'].rolling(window=N).mean()

    # 计算最近 20 日的最高价 (Rolling High)
    print("开始计算最近 20 日最高价 (Rolling High)...")
    数据['20日最高价'] = 数据['High'].rolling(window=20).max()

    # 计算回撤（与最近 20 日最高价的差值）
    print("开始计算回撤和回撤ATR比...")
    数据['回撤'] = 数据['20日最高价'] - 数据['收盘价']

    # 计算回撤ATR比（回撤除以 ATR）
    数据['回撤ATR比'] = 数据['回撤'] / 数据['ATR']

    # 生成加仓信号
    print("开始生成加仓信号...")
    数据['加仓信号'] = np.where(数据['回撤ATR比'] >= 2, '加仓', '')

    # 打印处理后的数据供检查
    print("数据处理完成，预览结果：")
    print(数据[['Date', '收盘价', 'High', 'Low', 'ATR', '回撤', '回撤ATR比', '加仓信号']].tail(10))

    # 添加指标解释到文件底部
    解释数据 = pd.DataFrame({
        'Date': ['指标解释:'],
        '收盘价': ['收盘价：当天的最终价格'],
        'High': ['High：当天的最高价格'],
        'Low': ['Low：当天的最低价格'],
        'ATR': ['ATR：14天平均真实波幅'],
        '回撤': ['回撤：当前价格与最近20天最高点的差值'],
        '回撤ATR比': ['回撤ATR比：回撤值与ATR的比值'],
        '加仓信号': ['加仓信号：当回撤ATR比 >= 2 时触发加仓信号']
    })

    数据 = pd.concat([数据, 解释数据], ignore_index=True)

    # 保存结果到新的 CSV 文件
    try:
        数据.to_csv(输出路径, index=False, encoding='utf-8-sig')
        print(f"ATR 和信号计算完成，结果已保存到: {输出路径}")
    except Exception as e:
        print(f"保存文件失败: {e}")


# 主程序
if __name__ == "__main__":
    # 指定目标文件夹
    目录路径 = r"F:\Cal_Prince"  # 替换为您的实际目录路径

    # 动态查找目录中最新的 CSV 文件
    最新CSV文件路径 = 获取最新CSV文件(目录路径)

    if 最新CSV文件路径:
        # 打印最新文件名（动态获取）
        最新CSV文件名 = os.path.basename(最新CSV文件路径)
        print(f"最新的 CSV 文件是: {最新CSV文件名}")

        # 指定输出文件路径
        输出文件路径 = os.path.join(目录路径, "ATR和信号结果.csv")

        # 调用计算函数
        计算ATR并生成信号(最新CSV文件路径, 输出文件路径)
    else:
        print("未找到 CSV 文件，请检查目录路径或文件内容。")