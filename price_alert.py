#!/usr/bin/env python3
"""
价格告警监控系统
每小时检查BTC/ETH价格，涨跌幅超过5%时发送Telegram告警
"""
import requests
import os
import json
from datetime import datetime
from pathlib import Path

# 配置
TELEGRAM_BOT_TOKEN = "8513917405:AAGYSpK-4Kmhr92IB0ar7vrTBmS9U7zxAv8"
TELEGRAM_CHAT_ID = "6942380112"

# 价格存储文件
PRICE_FILE = Path("/Users/dostang/.openclaw/workspace/price_alerts.json")
ALERT_THRESHOLD = 5.0  # 告警阈值 5%

def load_previous_prices():
    """加载之前的价格数据"""
    if PRICE_FILE.exists():
        try:
            with open(PRICE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_prices(prices):
    """保存当前价格数据"""
    with open(PRICE_FILE, 'w') as f:
        json.dump(prices, f)

def get_crypto_prices():
    """获取BTC和ETH价格"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'bitcoin,ethereum',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_24hr_vol': 'true'
        }
        r = requests.get(url, params=params, timeout=10)
        return r.json()
    except Exception as e:
        print(f"获取价格失败: {e}")
        return None

def calculate_change(current, previous):
    """计算涨跌幅百分比"""
    if not previous or previous == 0:
        return 0
    return ((current - previous) / previous) * 100

def send_alert(coin, current_price, change_pct, direction):
    """发送价格告警到Telegram"""
    emoji = "🚀" if direction == "up" else "🔻"
    
    message = f"""
⚠️ *价格告警 - {coin}*

{emoji} *{direction.upper()} {abs(change_pct):.2f}%*

💰 当前价格: ${current_price:,.2f}
⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

#crypto #{coin}
"""
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        r = requests.post(url, params=params, timeout=10)
        if r.status_code == 200:
            print(f"✅ 告警已发送: {coin} {direction}")
            return True
        else:
            print(f"❌ 发送失败: {r.text}")
            return False
    except Exception as e:
        print(f"❌ 发送告警失败: {e}")
        return False

def check_alerts():
    """检查价格并发送告警"""
    print(f"\n{'='*50}")
    print(f"价格监控检查 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")
    
    # 获取当前价格
    prices_data = get_crypto_prices()
    if not prices_data:
        print("❌ 无法获取价格数据")
        return
    
    # 加载之前的价格
    previous_prices = load_previous_prices()
    
    current_prices = {}
    alerts_sent = []
    
    for coin in ['bitcoin', 'ethereum']:
        if coin in prices_data:
            current_price = prices_data[coin]['usd']
            current_prices[coin] = {
                'price': current_price,
                'time': datetime.now().isoformat()
            }
            
            # 检查是否有之前的价格
            prev_data = previous_prices.get(coin)
            if prev_data:
                prev_price = prev_data.get('price')
                if prev_price:
                    change_pct = calculate_change(current_price, prev_price)
                    
                    print(f"\n{coin.upper()}:")
                    print(f"  之前: ${prev_price:,.2f}")
                    print(f"  当前: ${current_price:,.2f}")
                    print(f"  涨跌: {change_pct:+.2f}%")
                    
                    # 检查是否超过阈值
                    if abs(change_pct) >= ALERT_THRESHOLD:
                        direction = "up" if change_pct > 0 else "down"
                        coin_name = "BTC" if coin == "bitcoin" else "ETH"
                        send_alert(coin_name, current_price, change_pct, direction)
                        alerts_sent.append(coin)
            else:
                print(f"\n{coin.upper()}: 首次记录价格 ${current_price:,.2f}")
    
    # 保存当前价格
    save_prices(current_prices)
    
    if alerts_sent:
        print(f"\n✅ 已发送 {len(alerts_sent)} 个告警")
    else:
        print(f"\n📊 价格波动在 {ALERT_THRESHOLD}% 范围内，无告警")

if __name__ == "__main__":
    check_alerts()
