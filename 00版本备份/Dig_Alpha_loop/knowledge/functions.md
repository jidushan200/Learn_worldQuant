## ⚠️ 生成 Alpha 表达式的核心规则

### 1. 可选参数一律不写，只用默认值
hump(x) ✅       hump(x, 0.01) ❌
rank(x) ✅       rank(x, 2) ❌（rate=2是默认值）
scale(x) ✅      scale(x, 1, 1, 1) ❌

### 2. 必填参数必须写满
ts_mean(x, d) ✅    ts_mean(x) ❌
ts_corr(x, y, d) ✅  ts_corr(x, y) ❌
if_else(a, b, c) ✅   if_else(a, b) ❌

### 3. 常用函数参数速查
1个必填：abs, rank, reverse, log, sign, sqrt, inverse, 
         scale, normalize, zscore, hump, is_nan, not
2个必填：add, subtract, multiply, divide, power,
         ts_mean, ts_sum, ts_rank, ts_std_dev, 
         ts_zscore, ts_delay, ts_delta, ts_decay_linear,
         ts_arg_max, ts_arg_min, ts_product,
         group_rank, group_neutralize, group_mean,
         and, or
3个必填：ts_corr, ts_covariance, ts_regression, 
         if_else, trade_when

### 4. 输出格式要求
- 表达式中不要加任何空格（防止被输入框截断）
- 生成后必须自行验证：开括号数量 == 闭括号数量
- 表达式总长度尽量控制在 300 字符以内

## 函数参数数量速查（严格遵守，写错直接报错）

### 1个参数的函数（绝对不能多传）
rank(x)
reverse(x)
hump(x)
abs(x)
log(x)
sign(x)
sigmoid(x)
scale(x)

### 2个参数的函数
add(x, y)
subtract(x, y)
multiply(x, y)
divide(x, y)
max(x, y)
min(x, y)
power(x, y)
less(x, y)
greater(x, y)
ts_rank(x, n)
ts_sum(x, n)
ts_mean(x, n)
ts_std_dev(x, n)
ts_zscore(x, n)
ts_min(x, n)
ts_max(x, n)
ts_delay(x, n)
ts_delta(x, n)
ts_skewness(x, n)
ts_kurtosis(x, n)
ts_product(x, n)
ts_arg_max(x, n)
ts_arg_min(x, n)
ts_decay_linear(x, n)
ts_decay_exp_window(x, n)
group_rank(x, group)
group_neutralize(x, group)
group_mean(x, group)
group_sum(x, group)

### 3个参数的函数
ts_regression(y, x, n)
ts_covariance(x, y, n)
ts_correlation(x, y, n)
if_else(condition, true_val, false_val)  
clamp(x, lower, upper)

### ⚠️ 核心原则
- 多传一个参数 → 直接报 Invalid number of inputs
- 少传一个参数 → 直接报错
- 不确定就查这张表，不要猜