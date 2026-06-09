import os
import sys
import time
import urllib.parse
from datetime import datetime, timedelta
import requests
import yfinance as yf

# ==================== 🇨🇳 A 股实盘策略配置区域 ====================
BARK_KEY = os.environ.get("BARK_KEY")

# 🎯 专门针对海外服务器定制的 A 股核心硬科技瓶颈股自选池
A_STOCK_POOL = [
    "688017.SS", "688536.SS", "688981.SS", "688256.SS", 
    "688072.SS", "688012.SS", "603986.SS", "603501.SS",
    "002371.SZ", "300666.SZ", "002409.SZ", "300376.SZ",
    "600584.SS", "002049.SZ", "688126.SS", "300782.SZ"
]

A_VOLUME_MULTIPLIER = 3.0          # ✨ 3.0 倍单日日线成交量暴破线
MIN_TODAY_TURNOVER_RMB = 50_000_000 # 🛡️ 单日成交额流动性锁：今天一天的总成交额必须大于 5000 万人民币

# 💵 A 股轻仓突击额度：单次严格限制拨发 5,000 元人民币 (RMB)
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
    try: requests.get(url, timeout=15)
    except Exception as e: print(f"❌ 推送失败: {e}")

def execute_china_strategy():
    # 强制加上 timedelta(hours=8)，完美校准北京时间
    bj_time = datetime.utcnow() + timedelta(hours=8)
    bj_hour = bj_time.hour
    print(f"⏰ 北京时间实时完美校准为: {bj_time.strftime('%H:%M:%S')}")

    # ⏱️ A股专用时间锁
    if not (8 <= bj_hour < 22):
        print("💤 当前不在中国 A 股允许推送时段，雷达转为后台日志静音模式。")
        return

    print(f"🚀 精准启动 [ {len(A_STOCK_POOL)} 只 A 股核心真金池【单日3倍放量】穿透过滤 ]...")
    
    for ticker_symbol in A_STOCK_POOL:
        try:
            print(f"⏳ 正在深度检索 A 股量价数据: {ticker_symbol} ...")
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="35d")
            if len(hist) < 31: continue
                
            # 计算 30 日历史日均成交量（不含今天）
            past_30_days_volume = hist['Volume'].iloc[-31:-1]
            avg_volume_30d = past_30_days_volume.mean()
            if avg_volume_30d <= 0: continue
            
            # ✨ 核心降维：只抓取最纯粹的今日收盘价与今日成交量
            price_today = hist['Close'].iloc[-1]
            vol_today = hist['Volume'].iloc[-1]
            
            # ✨ 计算【今日这一天的真实总成交额】（今日成交额 = 今日价格 * 今日成交量）
            turnover_today = price_today * vol_today
            
            # 计算今日单日成交量放量倍数
            current_multiplier = vol_today / avg_volume_30d
            
            # ✨ 强制透明化输出：把今天的真实成绩单打在控制台上
            print(f"   📊 现场体检结果 -> 代码: {ticker_symbol} | 今日单日总成交额: ￥{turnover_today:,.0f} | 今日真实放量倍数: {current_multiplier:.2f}x")
            
            # ==================== 🪓 A 股终极单日过滤器矩阵 ====================
            if price_today < 2.0: continue # 过滤仙股
            
            # 🛡️ 安全线：今天一天的交易额必须突破 5000 万人民币，直接洗掉没人要的僵尸死鱼
            if turnover_today < MIN_TODAY_TURNOVER_RMB: continue
            
            # ⚡ 冲锋判定：今天单日成交量成功跨过 3.0 倍爆破红线！
            if current_multiplier >= A_VOLUME_MULTIPLIER:
                raw_shares = SINGLE_A_BUDGET_RMB / price_today
                suggested_shares = int(raw_shares // 100) * 100  # A 股必须是 100 股的整数倍
                if suggested_shares < 100: suggested_shares = 100
                stop_loss_price = price_today * 0.93  
                
                stock_name = ticker.info.get("shortName", ticker_symbol)
                
                push_title = f"🇨🇳 A股单日暴破警报：【{stock_name}】！"
                push_content = (
                    f"🏷️ 【交易演练阶段】: 🧪 A 股单日爆发策略推演\n"
                    f"💰 今日收盘价: ￥{price_today:.2f} | 📊 今日突发异动放量: {current_multiplier:.2f}倍\n"
                    f"🔥 今日单日总换手成交额达到: 【 ￥{turnover_today/10000:.1f} 万 】\n"
                    f"------------------------\n"
                    f"🎯 【A股单日雷达突击单】:\n"
                    f"💵 本笔固定拨发轻仓子弹: 【 ￥5,000 元 】\n"
                    f"🛒 策略建议即刻买入: 【 {suggested_shares} 股 】 (100股整手取整)\n"
                    f"🛑 【硬核止损防线】: 若买入，A股 7% 硬止损价为 【 ￥{stop_loss_price:.2f} 元 】\n"
                    f"📝 提示: 已切回纯粹单日3倍逻辑。数据全部为今天最实时结算，破位必须严格执行止损！"
                )
                send_to_bark_raw(title=push_title, content=push_content, group="A股单日主力爆破")
                
            time.sleep(1.2)
        except Exception as e: continue

if __name__ == "__main__":
    execute_china_strategy()
    print("🏁 中国 A 股单日异动清洗扫描完全结束。")
