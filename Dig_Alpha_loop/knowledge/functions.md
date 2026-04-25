我已为你**分类整理、格式优化**所有操作符，清晰呈现**操作符、类别、描述、参数/备注**，便于直接查阅、复制使用：

# 操作符完整整理表
## 一、算术操作符 (Arithmetic)
| 操作符 | 类别 | 描述 | 参数/备注 |
|--------|------|------|-----------|
| abs(x) | Arithmetic | 返回数字的绝对值，去除负号 | - |
| add(x, y, filter=false), x + y | Arithmetic | 将两个或多个输入逐元素相加 | filter=true：求和前将 NaN 视为 0 |
| densify(x) | Arithmetic | 将包含许多分桶的分组字段转换为仅包含现有分桶的较少数量，提升计算效率 | - |
| divide(x, y), x / y | Arithmetic | 执行除法运算：x 除以 y | - |
| inverse(x) | Arithmetic | 返回输入的倒数：1 / x | - |
| log(x) | Arithmetic | 计算输入值的自然对数 | 常用于对正值数据进行变换 |
| max(x, y, ...) | Arithmetic | 返回所有输入中的最大值 | 至少需要两个输入 |
| min(x, y, ...) | Arithmetic | 返回所有输入中的最小值 | 至少需要两个输入 |
| multiply(x, y, ..., filter=false), x * y | Arithmetic | 将两个或多个输入逐元素相乘 | filter=true：乘法前将 NaN 视为 0 |
| power(x, y) | Arithmetic | 计算 x 的 y 次幂 | - |
| reverse(x) | Arithmetic | 返回输入的相反数：-x | - |
| sign(x) | Arithmetic | 返回数字的符号 | 正数+1，负数-1，零0；NaN 返回 NaN |
| signed_power(x, y) | Arithmetic | 计算 x 的 y 次幂，同时保留 x 的符号 | - |
| sqrt(x) | Arithmetic | 返回 x 的非负平方根 | 等同于 power(x, 0.5)；保留符号用 signed_power(x, 0.5) |
| subtract(x, y, filter=false), x - y | Arithmetic | 从左到右执行减法：x - y - … | 支持两个及以上输入；filter=true：减法前将 NaN 视为 0 |

---

## 二、逻辑操作符 (Logical)
| 操作符 | 类别 | 描述 | 参数/备注 |
|--------|------|------|-----------|
| and(input1, input2) | Logical | 两个输入均为1（真）返回1，否则返回0（假） | - |
| if_else(input1, input2, input3) | Logical | 条件判断：条件为真返回input2，为假返回input3 | - |
| input1 < input2 | Logical | input1 小于 input2 返回1，否则返回0 | - |
| input1 <= input2 | Logical | input1 小于等于 input2 返回1，否则返回0 | - |
| input1 == input2 | Logical | input1 与 input2 相等返回1，否则返回0 | - |
| input1 > input2 | Logical | input1 大于 input2 返回1，否则返回0 | - |
| input1 >= input2 | Logical | input1 大于等于 input2 返回1，否则返回0 | - |
| input1 != input2 | Logical | input1 与 input2 不相等返回1，否则返回0 | - |
| is_nan(input) | Logical | 输入为 NaN 返回1，否则返回0 | - |
| not(x) | Logical | 逻辑否定：x=1返回0，x=0返回1 | - |
| or(input1, input2) | Logical | 任一输入为1（真）返回1，否则返回0 | - |

---

## 三、时间序列操作符 (Time Series)
| 操作符 | 类别 | 描述 | 参数/备注 |
|--------|------|------|-----------|
| days_from_last_change(x) | Time Series | 计算变量最近一次数值变化以来的天数 | - |
| hump(x, hump=0.01) | Time Series | 限制输入变化幅度，降低换手率 | - |
| kth_element(x, d, k, ignore="NaN") | Time Series | 过去d天时间序列返回第K个值 | 可忽略指定值，常用于回填缺失数据 |
| last_diff_value(x, d) | Time Series | 返回过去d天内与当前值不同的最近有效值 | - |
| ts_arg_max(x, d) | Time Series | 过去d天最大值出现至今的天数 | 今日最大值=0，昨日=1，依此类推 |
| ts_arg_min(x, d) | Time Series | 过去d天最小值出现至今的天数 | 今日最小值=0，昨日=1，依此类推 |
| ts_av_diff(x, d) | Time Series | 当前值 - 过去d天均值 | 计算均值时忽略 NaN |
| ts_backfill(x, lookback=d, k=1) | Time Series | 用指定回溯窗口内最近有效值替换缺失值 | 改善数据覆盖，降低缺失值风险 |
| ts_corr(x, y, d) | Time Series | 计算过去d天x、y的皮尔逊相关系数 | 衡量变量联动程度 |
| ts_count_nans(x, d) | Time Series | 统计过去d天内缺失值（NaN）数量 | - |
| ts_covariance(y, x, d) | Time Series | 计算过去d天两个变量的协方差 | - |
| ts_decay_linear(x, d, dense=false) | Time Series | 对时间序列应用线性衰减，平滑数据 | 降低旧数据/缺失值影响 |
| ts_delay(x, d) | Time Series | 返回变量x在d天前的值 | 访问历史数据 |
| ts_delta(x, d) | Time Series | 当前值 - d天前值 | 衡量数据变化/动量 |
| ts_mean(x, d) | Time Series | 计算x过去d天的简单平均值 | - |
| ts_product(x, d) | Time Series | 过去d天x值的乘积 | 用于几何平均、复利计算 |
| ts_quantile(x, d, driver="gaussian") | Time Series | 滚动排名+逆累积分布函数转换 | 归一化/重塑数据分布 |
| ts_rank(x, d, constant=0) | Time Series | 过去d天内变量值排名，返回当前排名 | 可加常数，用于归一化 |
| ts_regression(y, x, d, lag=0, rettype=0) | Time Series | 返回回归函数相关参数 | - |
| ts_scale(x, d, constant=0) | Time Series | 将时间序列缩放到0-1范围 | 可添加常数偏移 |
| ts_std_dev(x, d) | Time Series | 计算x过去d天的标准差 | 衡量数据偏离均值程度 |
| ts_step(1) | Time Series | 返回按日递增的计数器 | - |
| ts_sum(x, d) | Time Series | 对过去d天x的值求和 | - |
| ts_zscore(x, d) | Time Series | 计算时间序列Z分数 | 标准化、比较时序值 |

---

## 四、截面操作符 (Cross Sectional)
| 操作符 | 类别 | 描述 | 参数/备注 |
|--------|------|------|-----------|
| normalize(x, useStd=false, limit=0.0) | Cross Sectional | 截面数据去均值，可选除以标准差并限制范围 | 计算时忽略 NaN |
| quantile(x, driver=gaussian, sigma=1.0) | Cross Sectional | 排序位移+统计分布转换，减少异常值 | 支持高斯/柯西/均匀分布 |
| rank(x, rate=2) | Cross Sectional | 全工具值排名，返回0.0-1.0均匀分布值 | 归一化数据，降低异常值影响 |
| scale(x, scale=1, longscale=1, shortscale=1) | Cross Sectional | 缩放输入，使绝对值总和等于指定账面规模 | 可分别设置多空头缩放比例 |
| winsorize(x, std=4) | Cross Sectional | 限制数据在指定标准差范围内 | 减少极端异常值影响 |
| zscore(x) | Cross Sectional | 计算截面Z分数 | 衡量值与组均值的偏离程度 |

---

## 五、向量操作符 (Vector)
| 操作符 | 类别 | 描述 | 参数/备注 |
|--------|------|------|-----------|
| vec_avg(x) | Vector | 向量字段所有元素计算均值 | 将向量数据转为单个矩阵值 |
| vec_sum(x) | Vector | 计算向量字段所有值的总和 | - |

---

## 六、转换操作符 (Transformational)
| 操作符 | 类别 | 描述 | 参数/备注 |
|--------|------|------|-----------|
| bucket(...) | Transformational | 根据数据字段排名创建自定义分桶 | 可配合分组运算符使用 |
| trade_when(x, y, z) | Transformational | 满足条件时更改Alpha值，否则保持原值 | 退出条件可赋值NaN平仓 |

---

## 七、分组操作符 (Group)
| 操作符 | 类别 | 描述 | 参数/备注 |
|--------|------|------|-----------|
| group_backfill(x, group, d, std=4.0) | Group | 组内用缩尾均值填充缺失值 | 默认标准差4.0 |
| group_mean(x, weight, group) | Group | 计算指定组内数据的调和平均值 | - |
| group_neutralize(x, group) | Group | 组内Alpha值中性化（减去组均值） | 支持行业/板块/国家等分组 |
| group_rank(x, group) | Group | 组内元素排名，赋值0.0-1.0 | 同组内数据对比 |
| group_scale(x, group) | Group | 组内值归一化到0-1范围 | 跨组数据可比 |
| group_zscore(x, group) | Group | 计算组内Z分数 | 组内相对值对比 |

### 总结
1. 按**7大类别**完整归类所有操作符，结构清晰无遗漏
2. 保留原始**描述、参数、备注**，格式统一易读
3. 可直接用于文档、查询、代码注释等场景