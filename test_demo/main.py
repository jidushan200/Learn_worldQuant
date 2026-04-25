import json
import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def main():
    alpha_id = 'YPWoZ7nA'

    sess = requests.Session()
    sess.auth = HTTPBasicAuth('kongkong3307@163.com', 'zkm94031607')
    retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    sess.mount('https://', HTTPAdapter(max_retries=retry))

    print('正在登录...')
    resp = sess.post('https://api.worldquantbrain.com/authentication', timeout=60)
    if resp.status_code >= 400:
        print(f'登录失败: {resp.text}')
        return
    print('登录成功！\n')

    url = f'https://api.worldquantbrain.com/alphas/{alpha_id}/recordsets/yearly-stats'
    resp = sess.get(url, timeout=60)
    data = resp.json()

    props = [p['name'] for p in data['schema']['properties']]
    records = [dict(zip(props, row)) for row in data['records']]

    # ---- 计算 Aggregate Data ----
    years = len(records)
    avg_sharpe = sum(r['sharpe'] for r in records) / years
    avg_turnover = sum(r['turnover'] for r in records) / years
    avg_fitness = sum(r['fitness'] for r in records) / years
    avg_returns = sum(r['returns'] for r in records) / years
    max_drawdown = max(r['drawdown'] for r in records)
    avg_margin = sum(r['margin'] for r in records) / years

    print('=' * 90)
    print('Aggregate Data')
    print(f'  Sharpe: {avg_sharpe:.2f}    Turnover: {avg_turnover * 100:.2f}%    '
          f'Fitness: {avg_fitness:.2f}    Returns: {avg_returns * 100:.2f}%    '
          f'Drawdown: {max_drawdown * 100:.2f}%    Margin: {avg_margin * 10000:.2f}‱')
    print('=' * 90)

    # ---- 年度明细表 ----
    header = f'{"Year":<8}{"Sharpe":>8}{"Turnover":>12}{"Fitness":>10}{"Returns":>12}{"Drawdown":>12}{"Margin":>12}{"Long Count":>14}{"Short Count":>14}'
    print(header)
    print('-' * 90)

    for r in records:
        print(f'{r["year"]:<8}'
              f'{r["sharpe"]:>8.2f}'
              f'{r["turnover"] * 100:>11.2f}%'
              f'{r["fitness"]:>10.2f}'
              f'{r["returns"] * 100:>11.2f}%'
              f'{r["drawdown"] * 100:>11.2f}%'
              f'{r["margin"] * 10000:>11.2f}‱'
              f'{r["longCount"]:>14}'
              f'{r["shortCount"]:>14}')

    print('=' * 90)


if __name__ == '__main__':
    main()