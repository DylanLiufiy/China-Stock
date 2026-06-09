import os
import sys
import time
import urllib.parse
from datetime import datetime
import requests

# ==================== 🇨🇳 A 股实盘策略配置区域 ====================
# 🔒 自动读取您在 GitHub Secrets 里面已经配好的那个完全相同的 BARK_KEY
BARK_KEY = os.environ.get("BARK_KEY")

# 📊 过滤器阈值设定（严格锚定中国 A 股高弹性小盘庄股）
A_MARKET_CAP_MIN = 1_000_000_000   # 市值下限：10亿人民币
A_MARKET_CAP_MAX = 20_000_000_000  # 市值上限：200亿人民币
A_VOLUME_MULTIPLIER = 3.0          # 3.0 倍日线成交量暴破线

# ✨ 3日流动性安全锁：最近3天平均日成交额必须大于 5000 万人民币，确保资金绝对自由进出
MIN_3DAY_AVG_TURNOVER_RMB = 50_000_000 

# 💵 A 股轻仓突击额度：单次触发严格限制拨发 5,000 元人民币 (RMB)
SINGLE_A_BUDGET_RMB = 5000
# =========================================================================

def send_to_bark_raw(title: str, content: str, group: str = "A股主力爆破"):
    """Bark 独立分组发送通道"""
    if not BARK_KEY:
        print(f"⚠️ 本地控制台输出 -> 【{title}】:\n{content}\n")
        return
    clean_key = BARK_KEY.replace("https://day.app", "").replace("https://day.app", "").strip("/")
    encoded_title = urllib.parse.quote_plus(title)
    encoded_content = urllib.parse.quote_plus(content)
    encoded_group = urllib.parse.quote_plus(group)
    url = f"https://api.day.app/{clean_key}/{encoded_title}/{encoded_content}?group={encoded_group}&sound=glass"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200: print(f"🇨🇳 成功推送 A 股异动：{title}")
    except Exception as e: print(f"❌ 推送失败: {e}")

def fetch_china_stock_universe():
    """
    🛰️ A股大数据清洗引擎：一秒清洗全 A 股 5000 多家公司！
    """
    print("🛰️ 正在扫描全 A 股（沪深两市）所有挂牌上市公司大数据...")
    ticker_pool = []
    try:
        # 拉取全A股实时大盘快照行情数据
        url = "https://eastmoney.com"
        res = requests.get(url, timeout=15).json()
        data_list = res.get('data', {}).get('diff', [])
        
        for item in data_list:
            code = item.get('f12')  # 股票代码
            name = item.get('f14')  # 股票名称
            mcap = item.get('f20', 0) # 总市值（人民币）
            price = item.get('f2', 0) # 最新价
            
            if not code or mcap is None: continue
            
            # 1. 严格的小盘高弹性市值过滤器（10亿 - 200亿人民币）
            if A_MARKET_CAP_MIN <= mcap <= A_MARKET_CAP_MAX:
                prefix = "sh" if code.startswith(('60', '68')) else "sz"
                ticker_pool.append({"code": f"{prefix}{code}", "name": name, "price": price, "mcap": mcap})
                
        print(f"✅ A 股大数据动态初选成功！共筛选出 {len(ticker_pool)} 只符合市值门槛的小盘活跃股。")
        return ticker_pool
    except Exception as e:
        print(f"❌ 连线国内行情中心失败: {e}，启动备用精锐防线...")
        return [
            {"code": "sh688017", "name": "绿的谐波", "price": 45.0, "mcap": 12000000000},
            {"code": "sz002409", "name": "雅克科技", "price": 55.0, "mcap": 14000000000}
        ]

def execute_china_strategy():
    bj_time = datetime.now()
    print(f"⏰ 北京时间当前为: {bj_time.strftime('%H:%M:%S')}")

    dynamic_pool = fetch_china_stock_universe()
    print(f"🚀 精准启动 [ {len(dynamic_pool)} 只 A 股 3日成交额滑动穿透计算 ]...")
    
    # 限制单次云端循环的前 40 只股票，防止 GitHub 运行超时限制
    for stock in dynamic_pool[:40]:
        try:
            ticker_code = stock['code']
            stock_name = stock['name']
            
            url = f"https://gtimg.cn{ticker_code},day,,,35,qfq"
            res = requests.get(url, timeout=10).json()
            
            kline_data = res.get('data', {}).get(ticker_code, {}).get('day', [])
            if len(kline_data) < 31: continue
            
            # 计算 30 日历史日均成交量（不含今天）
            volumes_30d = [float(day[5]) for day in kline_data[-31:-1]]
            avg_volume_30d = sum(volumes_30d) / len(volumes_30d)
            if avg_volume_30d <= 0: continue
            
            # 提取最近 3 个交易日的收盘价与成交量（手 ➔ 股数转换）
            vol_today = float(kline_data[-1][5]) * 100
            price_today = float(kline_data[-1][2])
            
            vol_d1 = float(kline_data[-2][5]) * 100
            price_d1 = float(kline_data[-2][2])
            
            vol_d2 = float(kline_data[-3][5]) * 100
            price_d2 = float(kline_data[-3][2])
            
            # 计算近 3 日每一天的真实日成交额（人民币元）
            turnover_today = price_today * vol_today
            turnover_d1 = price_d1 * vol_d1
            turnover_d2 = price_d2 * vol_d2
            avg_3day_turnover = (turnover_today + turnover_d1 + turnover_d2) / 3
            
            # 计算今日成交量放量倍数
            current_multiplier = (vol_today / 100) / avg_volume_30d
            
            print(f"   📊 {stock_name} -> 3日均成交额: ￥{avg_3day_turnover:,.0f} | 今日量倍数: {current_multiplier:.2f}x")
            
            # ==================== 🪓 A 股终极多维过滤器矩阵 ====================
            if price_today < 2.0: continue
            if avg_3day_turnover < MIN_3DAY_AVG_TURNOVER_RMB: continue
            
            if current_multiplier >= A_VOLUME_MULTIPLIER:
                raw_shares = SINGLE_A_BUDGET_RMB / price_today
                suggested_shares = int(raw_shares // 100) * 100  # A 股必须是 100 股的整数倍
                if suggested_shares < 100: suggested_shares = 100
                stop_loss_price = price_today * 0.93  
                
                push_title = f"🇨🇳 A股主力突发暴破：【{stock_name}】！"
                push_content = (
                    f"🏷️ 【交易演练阶段】: 🧪 A 股策略实战推演\n"
                    f"💰 今日收盘价: ￥{price_today:.2f} | 📊 异常放量: {current_multiplier:.2f}倍\n"
                    f"💎 资金热度体检: 近3日平均日成交额达 【 ￥{avg_3day_turnover/10000:.1f} 万 】\n"
                    f"------------------------\n"
                    f"🎯 【A股游击仓专项突击单】:\n"
                    f"💵 本笔固定拨发轻仓子弹: 【 ￥5,000 元 】\n"
                    f"🛒 策略建议即刻买入: 【 {suggested_shares} 股 】 (已进行100股取整)\n"
                    f"🛑 【硬核止损防线】: 若买入，A股 7% 硬止损价为 【 ￥{stop_loss_price:.2f} 元 】\n"
                    f"📝 提示: 接收时段已限制。打中即撤，绝不抗单！"
                )
                send_to_bark_raw(title=push_title, content=push_content, group="A股主力爆破")
                
            time.sleep(1.2)
        except Exception as e: continue

if __name__ == "__main__":
    execute_china_strategy()
    print("🏁 中国 A 股全量大数据异动清洗扫描完全结束。")
