# 成功 Alpha 表达式范例
以下 alpha 曾在平台获得 GOOD 或以上 grade，供参考结构和风格。

##
name: network_dependence
expr: rank(-ts_mean(pv13_ustomergraphrank_hub_rank, 504))
说明: 长期低Hub Score代表客户合作伙伴集中度高、公司被替换风险低，为股票正向因子
setting: delay=1, decay=5, neutralization=INDUSTRY, universe=TOP3000

##
name: social_sentiment_volatility
expr: rank(-ts_std_dev(ts_backfill(snt_social_value, 60), 60))
说明: 情绪长期无波动预示未来表现弱势，取负向排名构建空头倾向因子
setting: delay=1, decay=4, neutralization=INDUSTRY, universe=TOP3000

##
name: growth_valuation_rank
expr: rank(ts_zscore(growth_valuation_model_score, 126))
说明: 增长估值模型得分的中期Z-score排名，做多排名提升的股票
setting: delay=1, decay=4, neutralization=INDUSTRY, universe=TOP3000

##
name: valuation_estimate_diff
expr: rank(growth_valuation_actual - growth_valuation_predicted)
说明: 实际估值超预期为正向信号，做多超预期、做空不及预期股票
setting: delay=1, decay=5, neutralization=INDUSTRY, universe=TOP3000

##
name: intrinsic_value_undervalued
expr: rank(-ts_corr(intrinsic_value, market_value, 252))
说明: 内在价值与市场价值相关性越低，股票低估可能性越高，为正向信号
setting: delay=1, decay=6, neutralization=INDUSTRY, universe=TOP3000

# 成功 Alpha 表达式范例
以下全部 1–101 号公式化 Alpha 源自《101 Formulaic Alphas》，完全对齐 WorldQuant BRAIN 语法、统一命名/表达式/说明/配置，可直接复制使用。
统一全局配置：delay=1，decay=3，neutralization=INDUSTRY，universe=TOP3000

##
name: alpha_01
expr: rank(ts_argmax(signedpower(cond(returns < 0, stddev(returns, 20), close), 2), 5)) - 0.5)
说明: 涨跌分段取值+幂次变换，取5日极值时序排名，短期反转信号

##
name: alpha_02
expr: -1 * correlation(rank(delta(log(volume), 2)), rank((close - open) / open), 6)
说明: 成交量二阶差分、日内涨跌幅秩相关，负向构建量价背离因子

##
name: alpha_03
expr: -1 * correlation(rank(open), rank(volume), 10)
说明: 开盘价与成交量10日秩相关反向打分，捕捉筹码分歧

##
name: alpha_04
expr: -1 * ts_rank(rank(low), 9)
说明: 9日时序排名低价序列，纯价格维度短期均值回归

##
name: alpha_05
expr: rank(open - ts_mean(vwap, 10)) * (-1 * abs(rank(close - vwap)))
说明: 开盘相对10日均价偏离，叠加收盘价相对VWAP偏离约束

##
name: alpha_06
expr: -1 * correlation(open, volume, 10)
说明: 开盘价与成交量10日时序相关，反向做空高相关标的

##
name: alpha_07
expr: cond(adv20 < volume, -1 * ts_rank(abs(delta(close, 7)), 60) * sign(delta(close, 7)), -1)
说明: 放量场景下用7日价格波动与涨跌符号构建强弱信号

##
name: alpha_08
expr: -1 * rank(ts_mean(open, 5) * ts_mean(returns, 5) - delay(ts_mean(open, 5) * ts_mean(returns, 5), 10))
说明: 5日开盘与收益乘积，10日滞后差分，捕捉趋势衰减

##
name: alpha_09
expr: cond(ts_min(delta(close, 1), 5) > 0, delta(close, 1), cond(ts_max(delta(close, 1), 5) < 0, delta(close, 1), -1 * delta(close, 1)))
说明: 5日价格涨跌区间判断，极端行情顺势，震荡反向

##
name: alpha_10
expr: rank(cond(ts_min(delta(close, 1), 4) > 0, delta(close, 1), cond(ts_max(delta(close, 1), 4) < 0, delta(close, 1), -1 * delta(close, 1))))
说明: 4日短期价格区间过滤，横截面排名标准化

##
name: alpha_11
expr: (rank(ts_max(vwap - close, 3)) + rank(ts_min(vwap - close, 3))) * rank(delta(volume, 3))
说明: 3日VWAP价差极值+成交量变化，日内资金行为捕捉

##
name: alpha_12
expr: sign(delta(volume, 1)) * (-1 * delta(close, 1))
说明: 单日量能方向反向匹配价格涨跌，量价反转

##
name: alpha_13
expr: -1 * rank(covariance(rank(close), rank(volume), 5))
说明: 5日价量秩协方差反向排名，压制同步波动标的

##
name: alpha_14
expr: -1 * rank(delta(returns, 3)) * correlation(open, volume, 10)
说明: 3日收益差分结合开盘量相关，复合趋势因子

##
name: alpha_15
expr: -1 * ts_sum(rank(correlation(rank(high), rank(volume), 3)), 3)
说明: 3日高价与量秩相关滚动求和，短期资金情绪

##
name: alpha_16
expr: -1 * rank(covariance(rank(high), rank(volume), 5))
说明: 高价与成交量秩协方差反向打分，博弈情绪因子

##
name: alpha_17
expr: (-1 * rank(ts_rank(close, 10))) * rank(delta(delta(close, 1), 1)) * rank(ts_rank(volume / adv20, 5))
说明: 价格时序排名、二阶价格差分、相对放量三维复合

##
name: alpha_18
expr: -1 * rank(stddev(abs(close - open), 5) + (close - open) + correlation(close, open, 10))
说明: 日内振幅波动+价差+开合相关性，综合反转

##
name: alpha_19
expr: -1 * sign((close - delay(close, 7)) + delta(close, 7)) * (1 + rank(ts_sum(returns, 250)))
说明: 7日价格偏离符号+长期收益排名，强弱趋势结合

##
name: alpha_20
expr: (-1 * rank(open - delay(high, 1))) * rank(open - delay(close, 1)) * rank(open - delay(low, 1))
说明: 开盘相对昨日高低收三维偏离，超短期情绪信号

##
name: alpha_21
expr: cond(ts_mean(close, 8) + stddev(close, 8) < ts_mean(close, 2), -1, cond(ts_mean(close, 2) < ts_mean(close, 8) - stddev(close, 8), 1, cond(volume / adv20 >= 1, 1, -1)))
说明: 长短周期价格均值波动对比，叠加相对放量过滤

##
name: alpha_22
expr: -1 * delta(correlation(high, volume, 5), 5) * rank(stddev(close, 20))
说明: 量价相关度变化+长期价格波动，波动率择时

##
name: alpha_23
expr: cond(ts_mean(high, 20) < high, -1 * delta(high, 2), 0)
说明: 价格突破20日高位时，做高价位回落反转

##
name: alpha_24
expr: cond(delta(ts_mean(close, 100), 100) / delay(close, 100) <= 0.05, -1 * (close - ts_min(close, 100)), -1 * delta(close, 3))
说明: 百年价格均值平稳区间用区间偏离，否则短期价格差分

##
name: alpha_25
expr: rank(-1 * returns * adv20 * vwap * (high - close))
说明: 收益、日均成交、均价、日内回落幅度多因子相乘

##
name: alpha_26
expr: -1 * ts_max(correlation(ts_rank(volume, 5), ts_rank(high, 5), 5), 3)
说明: 量价时序秩相关3日极值，压制高位同步标的

##
name: alpha_27
expr: cond(rank(ts_mean(correlation(rank(volume), rank(vwap), 6), 2)) > 0.5, -1, 1)
说明: 量价相关度横截面分位数二分，高低分化打分

##
name: alpha_28
expr: scale(correlation(adv20, low, 5) + (high + low) / 2 - close)
说明: 低价与流动性相关+中枢价格偏离，标准化缩放

##
name: alpha_29
expr: min(product(rank(rank(scale(log(ts_min(rank(rank(-1 * rank(delta(close, 5)))), 2))))), 1) + ts_rank(delay(-1 * returns, 6), 5)
说明: 多层嵌套秩变换+对数平滑+滞后收益时序排名

##
name: alpha_30
expr: (1 - rank(sign(close-delay(close,1)) + sign(delay(close,1)-delay(close,2)) + sign(delay(close,2)-delay(close,3)))) * ts_sum(volume,5) / ts_sum(volume,20)
说明: 三日价格趋势符号叠加，相对成交量加权

##
name: alpha_31
expr: rank(rank(rank(decay_linear(-1 * rank(rank(delta(close, 10))), 10)))) + rank(-1 * delta(close, 3)) + sign(scale(correlation(adv20, low, 12)))
说明: 线性衰减+多层秩+流动性相关符号，多周期融合

##
name: alpha_32
expr: scale(ts_mean(close,7) - close) + 20 * scale(correlation(vwap, delay(close,5), 230))
说明: 短期价格均值偏离+长周期量价滞后相关

##
name: alpha_33
expr: rank(-1 * (1 - open / close))
说明: 开合价格比值反向排名，日内折价溢价因子

##
name: alpha_34
expr: rank(1 - rank(stddev(returns,2)/stddev(returns,5))) + (1 - rank(delta(close,1)))
说明: 短期波动率比值+一阶价格差分，波动结构反转

##
name: alpha_35
expr: ts_rank(volume,32) * (1 - ts_rank(close+high-low,16)) * (1 - ts_rank(returns,32))
说明: 长周期量、价格形态、收益三维时序排名共振

##
name: alpha_36
expr: 2.21*rank(correlation(close-open,delay(volume,1),15)) + 0.7*rank(open-close) + 0.73*rank(ts_rank(delay(-1*returns,6),5)) + rank(abs(correlation(vwap,adv20,6))) + 0.6*rank((ts_mean(close,200)-open)*(close-open))
说明: 多组量价相关与价格偏离加权线性复合

##
name: alpha_37
expr: rank(correlation(delay(open-close,1), close, 200)) + rank(open-close)
说明: 长周期价差相关+即时开合价差，长短结合

##
name: alpha_38
expr: -1 * rank(ts_rank(close,10)) * rank(close/open)
说明: 价格时序排名+开合比值，趋势与溢价结合反转

##
name: alpha_39
expr: -1 * rank(delta(close,7) * (1 - rank(decay_linear(volume/adv20,9)))) * (1 + rank(ts_sum(returns,250)))
说明: 7日价格变化、放量衰减、长期收益排名三重约束

##
name: alpha_40
expr: -1 * rank(stddev(high,10)) * correlation(high,volume,10)
说明: 高价波动与量相关，高波动同步放量反向压制

##
name: alpha_41
expr: sqrt(high * low) - vwap
说明: 高低价几何均值相对均价偏离，价格中枢偏离

##
name: alpha_42
expr: rank(vwap - close) / rank(vwap + close)
说明: 日内收盘价相对均价偏离，delay0 日内反转

##
name: alpha_43
expr: ts_rank(volume/adv20,20) * ts_rank(-1*delta(close,7),8)
说明: 相对放量时序排名+中期价格反向趋势

##
name: alpha_44
expr: -1 * correlation(high, rank(volume), 5)
说明: 高价与成交量秩相关反向，博弈资金行为

##
name: alpha_45
expr: -1 * (rank(ts_mean(delay(close,5),20)) * correlation(close,volume,2) * rank(correlation(ts_mean(close,5),ts_mean(close,20),2)))
说明: 多重短周期价量相关嵌套复合

##
name: alpha_46
expr: cond((ts_mean(delay(close,20),10)-ts_mean(delay(close,10),10)) < -0.1, 1, -1*(close-delay(close,1)))
说明: 长期价格斜率对比，趋势破位反向

##
name: alpha_47
expr: rank(1/close)*volume/adv20 * (high*rank(high-close)/(ts_mean(high,5)/5)) - rank(vwap-delay(vwap,5))
说明: 估值倒数、流动性、日内强弱、均价滞后偏离多因子

##
name: alpha_48
expr: indneutralize(correlation(delta(close,1),delta(delay(close,1),1),250)*delta(close,1)/close,subindustry) / ts_sum(delta(close,1)/delay(close,1)^2,250)
说明: 子行业中性化，长周期价格波动相关性，delay0 因子

##
name: alpha_49
expr: cond((ts_mean(delay(close,20),10)-ts_mean(delay(close,10),10)) < -0.1, 1, -1*(close-delay(close,1)))
说明: 均线斜率拐点判断，超跌反转

##
name: alpha_50
expr: -1 * ts_max(rank(correlation(rank(volume), rank(vwap),5)),5)
说明: 量价均价秩相关5日极值，反向排名

##
name: alpha_51
expr: cond((ts_mean(delay(close,20),10)-ts_mean(delay(close,10),10)) < -0.05, 1, -1*(close-delay(close,1)))
说明: 放宽斜率阈值，适配弱震荡行情反转

##
name: alpha_52
expr: (-1*ts_min(low,5)+delay(ts_min(low,5),5)) * rank((ts_sum(returns,240)-ts_sum(returns,20))/220) * ts_rank(volume,5)
说明: 低价周期差值、长短收益差、短期量排名共振

##
name: alpha_53
expr: -1 * delta(((close-low)-(high-close))/(close-low),9)
说明: 日内多空力量比值9日差分，情绪边际变化

##
name: alpha_54
expr: -1 * ((low-close)*open^5) / ((low-high)*close^5)
说明: 高低价差与价格幂次结构，日内强弱极致分化

##
name: alpha_55
expr: -1 * correlation(rank((close-ts_min(low,12))/(ts_max(high,12)-ts_min(low,12))), rank(volume),6)
说明: 12日价格区间位置与成交量秩相关反向

##
name: alpha_56
expr: -1 * (rank(ts_sum(returns,10)/ts_sum(ts_sum(returns,2),3)) * rank(returns * cap))
说明: 收益结构比值+市值加权收益，大小盘分化因子

##
name: alpha_57
expr: -1 * (close-vwap) / decay_linear(rank(ts_argmax(close,30)),2)
说明: 价格均价偏离，叠加30日价格高点线性衰减

##
name: alpha_58
expr: -1 * ts_rank(decay_linear(correlation(indneutralize(vwap,sector),volume,3.92795),7.89291),5.50322)
说明: 行业中性化VWAP量相关，线性衰减+时序排名

##
name: alpha_59
expr: -1 * ts_rank(decay_linear(correlation(indneutralize(0.728317*vwap+0.271683*vwap,industry),volume,4.25197),16.2289),8.19648)
说明: 行业中性化加权均价，长周期衰减量价相关

##
name: alpha_60
expr: -1 * (2 * scale(rank(((close-low)-(high-close))/(high-low)*volume)) - scale(rank(ts_argmax(close,10))))
说明: 日内多空占比加权量能，结合短期价格高点

##
name: alpha_61
expr: cond(rank(vwap-ts_min(vwap,16.1219)) < rank(correlation(vwap,adv180,17.9282)), -1, 1)
说明: 长期均价低位偏离与流动性相关度二分打分

##
name: alpha_62
expr: cond(rank(correlation(vwap,ts_sum(adv20,22.4101),9.91009)) < rank(rank(open)+rank(open) < rank((high+low)/2)+rank(high)), -1, 1)
说明: 均价流动性相关与价格秩结构对比打分

##
name: alpha_63
expr: (rank(decay_linear(delta(indneutralize(close,industry),2.25164),8.22237)) - rank(decay_linear(correlation(0.318108*vwap+0.681892*open,ts_sum(adv180,37.2467),13.557),12.2883))) * -1
说明: 行业中性价格差分衰减，混合价量相关衰减差值

##
name: alpha_64
expr: cond(rank(correlation(0.178404*open+0.821596*low,ts_sum(adv120,12.7054),16.6208)) < rank(delta(0.178404*(high+low)/2+0.821596*vwap,3.69741)), -1, 1)
说明: 高低开盘混合价格，长期流动性相关对比短期价格变化

##
name: alpha_65
expr: cond(rank(correlation(0.00817205*open+0.99182795*vwap,ts_sum(adv60,8.6911),6.40374)) < rank(open-ts_min(open,13.635)), -1, 1)
说明: 微权重开盘混合均价，相对开盘低位偏离对比

##
name: alpha_66
expr: (rank(decay_linear(delta(vwap,3.51013),7.23052)) + ts_rank(decay_linear((0.96633*low+0.03367*low-vwap)/(open-(high+low)/2),11.4157),6.72611)) * -1
说明: 均价差分衰减+日内价格结构比值衰减复合

##
name: alpha_67
expr: (rank(high-ts_min(high,2.14593))^rank(correlation(indneutralize(vwap,sector),indneutralize(adv20,subindustry),6.02936))) * -1
说明: 板块中性量价相关，叠加高价低位偏离幂次

##
name: alpha_68
expr: cond(ts_rank(correlation(rank(high),rank(adv15),8.91644),13.9333) < rank(delta(0.518371*close+0.481629*low,1.06157)), -1, 1)
说明: 短期流动性与高价秩相关，对比混合低价变化

##
name: alpha_69
expr: (rank(ts_max(delta(indneutralize(vwap,industry),2.72412),4.79344))^ts_rank(correlation(0.490655*close+0.509345*vwap,adv20,4.92416),9.0615)) * -1
说明: 行业中性均价波动极值，结合混合价量相关

##
name: alpha_70
expr: (rank(delta(vwap,1.29456))^ts_rank(correlation(indneutralize(close,industry),adv50,17.8256),17.9171)) * -1
说明: 均价短期变化与长期行业中性量相关幂次复合

##
name: alpha_71
expr: max(ts_rank(decay_linear(correlation(ts_rank(close,3.43976),ts_rank(adv180,12.0647),18.0175),4.20501),15.6948), ts_rank(decay_linear(rank((low+open-vwap-vwap)^2),16.4662),4.4388))
说明: 双路径衰减时序排名，取最大值合成信号

##
name: alpha_72
expr: rank(decay_linear(correlation((high+low)/2,adv40,8.93345),10.1519)) / rank(decay_linear(correlation(ts_rank(vwap,3.72469),ts_rank(volume,18.5188),6.86671),2.95011))
说明: 价格中枢流动性相关 / 均价成交量时序相关比值

##
name: alpha_73
expr: max(rank(decay_linear(delta(vwap,4.72775),2.91864)), ts_rank(decay_linear(delta(0.147155*open+0.852845*low,2.03608)/ (0.147155*open+0.852845*low)*-1,3.33829),16.7411)) * -1
说明: 均价波动与混合低价趋势反向，双因子取最大

##
name: alpha_74
expr: cond(rank(correlation(close,ts_sum(adv30,37.4843),15.1365)) < rank(correlation(rank(0.0261661*high+0.9738339*vwap),rank(volume),11.4791)), -1, 1)
说明: 长期流动相关性对比高价均价混合秩相关

##
name: alpha_75
expr: cond(rank(correlation(vwap,volume,4.24304)) < rank(correlation(rank(low),rank(adv50),12.4413)), -1, 1)
说明: 短周期量价相关 vs 长期低价流动性秩相关

##
name: alpha_76
expr: max(rank(decay_linear(delta(vwap,1.24383),11.8259)), ts_rank(decay_linear(ts_rank(correlation(indneutralize(low,sector),adv81,8.14941),19.569),17.1543),19.383)) * -1
说明: 慢速衰减均价变化+板块中性低价流动相关

##
name: alpha_77
expr: min(rank(decay_linear(((high+low)/2+high)-(vwap+high),20.0451)), rank(decay_linear(correlation((high+low)/2,adv40,3.1614),5.64125)))
说明: 价格结构偏离与量相关衰减，取最小值保守信号

##
name: alpha_78
expr: rank(correlation(0.352233*low+0.647767*vwap,ts_sum(adv40,19.7428),6.83313))^rank(correlation(rank(vwap),rank(volume),5.77492))
说明: 低价均价混合流动相关，叠加量价秩相关幂次

##
name: alpha_79
expr: cond(rank(delta(indneutralize(0.60733*close+0.39267*open,sector),1.23438)) < rank(correlation(ts_rank(vwap,3.60973),ts_rank(adv150,9.18637),14.6644)), -1, 1)
说明: 板块中性开合混合价格变化，对比长期流动时序相关

##
name: alpha_80
expr: (rank(sign(delta(indneutralize(0.868128*open+0.131872*high,industry),4.04545)))^ts_rank(correlation(high,adv10,5.11456),5.53756)) * -1
说明: 行业中性价格变化符号，结合短期高价流动性相关

##
name: alpha_81
expr: cond(rank(log(product(rank(rank(correlation(vwap,ts_sum(adv10,49.6054),8.47743))^4),14.9655))) < rank(correlation(rank(vwap),rank(volume),5.07914)), -1, 1)
说明: 多阶秩相关乘积对数平滑，量价秩相关对比

##
name: alpha_82
expr: max(rank(decay_linear(delta(open,1.46063),14.8717)), ts_rank(decay_linear(correlation(indneutralize(volume,sector),0.634196*open+0.365804*open,17.4842),6.92131),13.4283)) * -1
说明: 开盘慢速波动+板块中性量相关衰减复合

##
name: alpha_83
expr: (rank(delay(((high-low)/(ts_mean(close,5)/5)),2)) * rank(rank(volume))) / (((high-low)/(ts_mean(close,5)/5))/(vwap-close))
说明: 日内波动比值滞后，量能排名与价格偏离比值

##
name: alpha_84
expr: signedpower(ts_rank(vwap-ts_max(vwap,15.3217),20.7127),delta(close,4.96796))
说明: 均价相对高位偏离时序排名，以中期价格变化为幂次

##
name: alpha_85
expr: rank(correlation(0.876703*high+0.123297*close,adv30,9.61331))^rank(correlation(ts_rank((high+low)/2,3.70596),ts_rank(volume,10.1595),7.11408))
说明: 高价收盘混合流动相关，价格中枢量时序相关幂次

##
name: alpha_86
expr: cond(ts_rank(correlation(close,ts_sum(adv20,14.7444),6.00049),20.4195) < rank(open+close-vwap-open), -1, 1)
说明: 短期流动相关时序排名，对比开盘收盘均价结构

##
name: alpha_87
expr: max(rank(decay_linear(delta(0.369701*close+0.630299*vwap,1.91233),2.65461)), ts_rank(decay_linear(abs(correlation(indneutralize(adv81,industry),close,13.4132)),4.89768),14.4535)) * -1
说明: 混合价波动衰减+行业中性流动相关绝对值衰减

##
name: alpha_88
expr: min(rank(decay_linear(rank(open)+rank(low)-rank(high)-rank(close),8.06882)), ts_rank(decay_linear(correlation(ts_rank(close,8.44728),ts_rank(adv60,20.6966),8.01266),6.65053),2.61957))
说明: 多空秩差值衰减+长期价流相关时序排名

##
name: alpha_89
expr: ts_rank(decay_linear(correlation(0.967285*low+0.032715*low,adv10,6.94279),5.51607),3.79744) - ts_rank(decay_linear(delta(indneutralize(vwap,industry),3.48158),10.1466),15.3012)
说明: 低价流动相关衰减 减 行业中性均价波动衰减

##
name: alpha_90
expr: (rank(close-ts_max(close,4.66719))^ts_rank(correlation(indneutralize(adv40,subindustry),low,5.38375),3.21856)) * -1
说明: 价格相对高点偏离，子行业中性流动低价相关幂次

##
name: alpha_91
expr: (ts_rank(decay_linear(decay_linear(correlation(indneutralize(close,industry),volume,9.74928),16.398),3.83219),4.8667) - rank(decay_linear(correlation(vwap,adv30,4.01303),2.6809))) * -1
说明: 双层线性衰减行业中性量相关，减去均价流动相关

##
name: alpha_92
expr: min(ts_rank(decay_linear(cond((high+low)/2+close < low+open,1,0),14.7221),18.8683), ts_rank(decay_linear(correlation(rank(low),rank(adv30),7.58555),6.94024),6.80584))
说明: 日内结构条件衰减+低价流动秩相关衰减，取最小

##
name: alpha_93
expr: ts_rank(decay_linear(correlation(indneutralize(vwap,industry),adv81,17.4193),19.848),7.54455) / rank(decay_linear(delta(0.524434*close+0.475566*vwap,2.77377),16.2664))
说明: 行业中性均价流动相关 / 混合价波动衰减排名

##
name: alpha_94
expr: (rank(vwap-ts_min(vwap,11.5783))^ts_rank(correlation(ts_rank(vwap,19.6462),ts_rank(adv60,4.02992),18.0926),2.70756)) * -1
说明: 均价相对低位偏离，叠加长周期均价流动时序相关

##
name: alpha_95
expr: cond(rank(open-ts_min(open,12.4105)) < ts_rank(correlation((high+low)/2,ts_sum(adv40,19.1351),12.8742)^5,11.7584), -1, 1)
说明: 开盘低位偏离对比价格中枢流动相关高次幂

##
name: alpha_96
expr: max(ts_rank(decay_linear(correlation(rank(vwap),rank(volume),3.83878),4.16783),8.38151), ts_rank(decay_linear(ts_argmax(correlation(ts_rank(close,7.45404),ts_rank(adv60,4.13242),3.65459),12.6556),14.0365),13.4143)) * -1
说明: 量价秩相关衰减+价流相关极值时序排名复合

##
name: alpha_97
expr: (rank(decay_linear(delta(indneutralize(0.721001*low+0.278999*vwap,industry),3.3705),20.4523)) - ts_rank(decay_linear(ts_rank(correlation(ts_rank(low,7.87871),ts_rank(adv60,17.255),4.97547),18.5925),15.7152),6.71659)) * -1
说明: 行业中性混合低价波动衰减 减 低价流动相关时序衰减

##
name: alpha_98
expr: rank(decay_linear(correlation(vwap,ts_sum(adv5,26.4719),4.58418),7.18088)) - rank(decay_linear(ts_rank(ts_argmin(correlation(rank(open),rank(adv15),20.8187),8.62571),6.95668),8.07206))
说明: 短周期均价流动相关衰减 减 开盘流动相关极小值时序

##
name: alpha_99
expr: cond(rank(correlation((high+low)/2,ts_sum(adv60,19.8975),8.8136)) < rank(correlation(low,volume,6.28259)), -1, 1)
说明: 长期价格中枢流动相关 vs 短期低价量相关

##
name: alpha_100
expr: -1 * (1.5 * scale(indneutralize(indneutralize(rank(cond(((close-low)-(high-close))/(high-low)*volume)),subindustry),subindustry)) - scale(indneutralize(correlation(close,rank(adv20),5)-rank(ts_argmin(close,30)),subindustry))) * (volume/adv20)
说明: 双重子行业中性化，日内强弱+流动性+价格极值复合

##
name: alpha_101
expr: (close - open) / ((high - low) + 0.001)
说明: 日内开合价差/全日波动幅度，经典日内趋势原始因子
