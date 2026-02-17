#!/usr/bin/env python3
"""快速发送投资报告"""
import requests
import os
from datetime import datetime

# 配置
TELEGRAM_BOT_TOKEN = "8513917405:AAGYSpK-4Kmhr92IB0ar7vrTBmS9U7zxAv8"
TELEGRAM_CHAT_ID = "6942380112"

def get_btc_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {'ids': 'bitcoin', 'vs_currencies': 'usd', 'include_24hr_change': 'true'}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        return data.get('bitcoin', {})
    except Exception as e:
        return {'error': str(e)}

def get_eth_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {'ids': 'ethereum', 'vs_currencies': 'usd', 'include_24hr_change': 'true'}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        return data.get('ethereum', {})
    except Exception as e:
        return {'error': str(e)}

def get_nasdaq():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EIXIC"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        result = data.get('chart', {}).get('result', [])
        if result:
            meta = result[0].get('meta', {})
            price = meta.get('regularMarketPrice', 0)
            prev = meta.get('previousClose', price)
            return {'price': price, 'change': price - prev, 'prev': prev}
    except Exception as e:
        return {'error': str(e)}
    return {'error': 'Unknown'}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    try:
        r = requests.post(url, params=params, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"发送失败: {e}")
        return False

# 生成报告
report = []
report.append(f"📊 *每日投资报告* - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
report.append("\n🪙 *加密货币*")

btc = get_btc_price()
if 'error' not in btc:
    report.append(f"- BTC: ${btc.get('usd', 'N/A'):,} ({btc.get('usd_24h_change', 0):+.2f}%)")
else:
    report.append(f"- BTC: 获取失败")

eth = get_eth_price()
if 'error' not in eth:
    report.append(f"- ETH: ${eth.get('usd', 'N/A'):,} ({eth.get('usd_24h_change', 0):+.2f}%)")
else:
    report.append(f"- ETH: 获取失败")

report.append("\n📈 *美股*")
nasdaq = get_nasdaq()
if 'error' not in nasdaq:
    change_pct = (nasdaq['change'] / nasdaq['prev']) * 100 if nasdaq['prev'] else 0
    report.append(f"- 纳斯达克: {nasdaq.get('price', 'N/A'):,} ({nasdaq.get('change', 0):+.2f}, {change_pct:+.2f}%)")
else:
    report.append(f"- 纳斯达克: 获取失败")

report.append("\n⚠️ *风险提示*")
report.append("- 市场波动风险")
report.append("- 建议分散投资")

message = "\n".join(report)
print(message)
print("\n发送中...")

if send_telegram(message):
    print("✅ 报告已发送到Telegram!")
else:
    print("❌ 发送失败")
