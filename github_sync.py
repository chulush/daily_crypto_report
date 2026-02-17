#!/usr/bin/env python3
"""
GitHub自动同步投资报告
- 自动创建/更新报告文件
- 每日自动提交到GitHub仓库
"""
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path

# 配置 - 用户填写
GITHUB_TOKEN = "YOUR_TOKEN_HERE"  # GitHub Personal Access Token
REPO_OWNER = "chulush"         # 你的GitHub用户名
REPO_NAME = "daily_crypto_report"      # 仓库名

# 本地报告目录
REPORTS_DIR = Path("/Users/dostang/.openclaw/workspace/reports")
REPORTS_DIR.mkdir(exist_ok=True)

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

def generate_report_markdown():
    """生成Markdown格式报告"""
    btc = get_btc_price()
    eth = get_eth_price()
    nasdaq = get_nasdaq()
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    btc_price = btc.get('usd', 0) or 0
    btc_change = btc.get('usd_24h_change', 0) or 0
    eth_price = eth.get('usd', 0) or 0
    eth_change = eth.get('usd_24h_change', 0) or 0
    nasdaq_price = nasdaq.get('price', 0) or 0
    nasdaq_change = nasdaq.get('change', 0) or 0
    
    md = f"""# 每日投资报告 - {date_str}

## 加密货币

| 币种 | 价格 | 24h涨跌幅 |
|------|------|-----------|
| BTC  | ${btc_price:,.2f} | {btc_change:+.2f}% |
| ETH  | ${eth_price:,.2f} | {eth_change:+.2f}% |

## 美股

| 指数 | 价格 | 涨跌幅 |
|------|------|--------|
| 纳斯达克 | {nasdaq_price:,.2f} | {nasdaq_change:+.2f} |

## 风险提示

- 市场波动风险
- 建议分散投资

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    return md

def save_report_locally():
    """保存报告到本地"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    md = generate_report_markdown()
    
    # 保存每日报告
    report_file = REPORTS_DIR / f"report-{date_str}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(md)
    
    # 更新README
    readme_file = REPORTS_DIR / "README.md"
    readme_content = f"""# 投资报告

每日自动更新的投资分析报告。

## 最近报告

"""
    # 添加最近7天的报告链接
    for i in range(7):
        d = datetime.now() - timedelta(days=i)
        d_str = d.strftime('%Y-%m-%d')
        report_file_check = REPORTS_DIR / f"report-{d_str}.md"
        if report_file_check.exists():
            readme_content += f"- [{d_str}](./reports/report-{d_str}.md)\n"
    
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ 报告已保存到: {report_file}")
    return str(report_file)

def push_to_github():
    """推送到GitHub"""
    if GITHUB_TOKEN == "YOUR_GITHUB_TOKEN":
        print("❌ 请先配置GitHub Token")
        return False
    
    import github
    from github import Auth
    
    try:
        # 使用新认证方式
        g = github.Github(auth=Auth.Token(GITHUB_TOKEN))
        repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
        
        # 读取本地报告文件
        date_str = datetime.now().strftime('%Y-%m-%d')
        report_file = REPORTS_DIR / f"report-{date_str}.md"
        
        if not report_file.exists():
            print("❌ 报告文件不存在")
            return False
        
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 先检查仓库是否为空，如果为空先创建README
        try:
            contents = repo.get_contents("")
            if len(contents) == 0:
                raise Exception("Empty repo")
        except:
            # 仓库为空，先创建README
            try:
                repo.create_file(
                    path="README.md",
                    message="Initial commit - Investment Reports",
                    content="# 投资报告\n\n每日自动更新的加密货币和美股分析报告\n"
                )
                print("✅ 已创建初始README")
            except Exception as e:
                print(f"创建README: {e}")
        
        # 直接尝试创建文件，如果已存在会报错
        try:
            repo.create_file(
                path=f"reports/report-{date_str}.md",
                message=f"Add report {date_str}",
                content=content
            )
            print(f"✅ 报告已创建到GitHub: reports/report-{date_str}.md")
        except github.GithubException as e:
            # 如果创建失败，尝试更新
            if e.status == 422:  # Unprocessable Entity - usually means file exists
                try:
                    file = repo.get_contents(f"reports/report-{date_str}.md")
                    repo.update_file(
                        path=f"reports/report-{date_str}.md",
                        message=f"Update report {date_str}",
                        content=content,
                        sha=file.sha
                    )
                    print(f"✅ 报告已更新到GitHub: reports/report-{date_str}.md")
                except:
                    print(f"❌ 更新文件失败: {e}")
            else:
                print(f"❌ 创建文件失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub同步失败: {e}")
        return False

def sync_cname_and_readme():
    """同步CNAME和README文件"""
    import base64
    import github
    from github import Auth
    
    try:
        g = github.Github(auth=Auth.Token(GITHUB_TOKEN))
        repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
        
        # CNAME文件
        cname_content = "daily.ifamily.top\n"
        
        # 尝试更新或创建CNAME
        try:
            file = repo.get_contents("CNAME")
            repo.update_file(
                path="CNAME",
                message="Update CNAME",
                content=base64.b64encode(cname_content.encode()).decode(),
                sha=file.sha
            )
        except:
            repo.create_file(
                path="CNAME",
                message="Add CNAME",
                content=base64.b64encode(cname_content.encode()).decode()
            )
        
        # README文件
        readme_content = f"""# 投资报告 🚀

每日自动更新的加密货币和美股分析报告。

## 最新报告

- [{datetime.now().strftime('%Y-%m-%d')}](./reports/report-{datetime.now().strftime('%Y-%m-%d')}.md)

---

*本报告由自动化系统每天早上8点更新*
"""
        
        try:
            file = repo.get_contents("README.md")
            repo.update_file(
                path="README.md",
                message="Update README",
                content=base64.b64encode(readme_content.encode()).decode(),
                sha=file.sha
            )
        except:
            repo.create_file(
                path="README.md",
                message="Add README",
                content=base64.b64encode(readme_content.encode()).decode()
            )
        
        print("✅ CNAME和README已同步")
        return True
        
    except Exception as e:
        print(f"⚠️ CNAME/README同步跳过: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("开始生成并同步投资报告...")
    print("=" * 50)
    
    # 0. 同步CNAME和README
    sync_cname_and_readme()
    
    # 1. 保存本地报告
    save_report_locally()
    
    # 2. 推送到GitHub
    push_to_github()
    
    print("\n完成!")
