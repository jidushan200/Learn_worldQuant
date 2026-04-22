# 查询范围配置
SEARCH_SCOPE = {
    'region':         'USA',
    'delay':          '1',
    'universe':       'TOP3000',
    'instrumentType': 'EQUITY'
}

# 所有目标数据集 id
DATASET_IDS = {
    'fundamental6': 'Company_Fundamental_Data_for_Equity',
    'pv13':         'Relationship_Data_for_Equity',
    'news12':       'US_News_Data',
    'analyst4':     'Analyst_Estimate_Data_for_Equity',
    'option8':      'Volatility_Data',
    'socialmedia12':'Sentiment_Data_for_Equity',
}

# 只保留的字段类型
FIELD_TYPE = 'MATRIX'

# 输出目录
OUTPUT_DIR = 'Datasets'