import os
import sys
import time
import urllib.parse
from datetime import datetime, timedelta
import requests
import yfinance as yf

# ==================== 🇨🇳 A 股实盘策略配置区域 ====================
BARK_KEY = os.environ.get("BARK_KEY")

# 🎯 A 股硬科技最核心精锐池（完全剔除在雅虎容易返回空数据的非标债转股，锁定最纯净的12只正股）
A_STOCK_POOL = [
    "688017.SS", "688536.SS", "688981.SS", "688256.SS", 
    "688072.SS", "688012.SS", "603986.SS", "603501.SS",
    "002371.SZ", "300666.SZ", "002409.SZ", "600584.SS"
]

A_VOLUME_MULTIPLIER = 3.0          # 3.0 倍单日日线成交量暴破线
MIN_TODAY_TURNOVER_RMB = 50_000_000 # 单日成交额流动性锁：今天一天的总成交额必须大于 5000 万人民币

# 💵 A 股轻仓突击额度：单次严格限制拨发 5,000 元人民币 (RMB)
SINGLE_A_BUDGET_RMB = 5000
# =========================================================================

def send_to_bark_raw(title: str, content: str, group: str = "A股主力爆破"):
    """Bark 独立分组发送通道"""
    if not BARK_KEY:
        print(f"⚠️ 本地控制台输出 -> 【{title}】:\n{content}\n", flush=True)
        return
    clean_key = BARK_KEY.replace("https://day.app", "").replace("https://day.app", "").strip("/")
    encoded_title = urllib.parse.quote_plus(title)
    encoded_content = urllib.parse.quote_plus(content)
    encoded_group = urllib.parse.quote_plus(group)
    url = f"https://api.day.app/{clean_key}/{encoded_title}/{encoded_content}?group={encoded_group}&sound=glass"
    try: requests.get(url, timeout=15)
    except Exception as e: print(f"❌ 推送失败: {e}", flush=True)

def execute_china_strategy():
    bj_time = datetime.utcnow() + timedelta(hours=8)
    bj_hour = bj_time.hour
    # ✨ ✨ 核心修复：加入 flush=True，拒绝被 Linux 系统吞掉缓存，必须零延迟直接打印！
    print(f"⏰ 北京时间实时完美校准为: {bj_time.strftime('%H:%M:%S')}", flush=True)

    if not (8 <= bj_hour < 22):
        print("💤 当前不在中国 A 股允许推送时段，雷达转为后台日志静音模式。", flush=True)
        return

    print(f"🚀 精准启动 [ {len(A_STOCK_POOL)} 只 A 股核心真金池【单日3倍放量】实时穿透 ]...", flush=True)
    
    for ticker_symbol in A_STOCK_POOL:
        try:
            # ✨ 核心修复：即时输出，绝不憋在缓冲区
            print(f"⏳ [数据链路连接] 正在向海外节点调取 A 股历史矩阵: {ticker_symbol} ...", flush=True)
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="35d")
            
            # 容错：如果该股票今天雅虎接口返回空矩阵，直接优雅跳过
            if hist is None or hist.empty or len(hist) < 31: 
                print(f"   ⚠️ 标的 {ticker_symbol} 雅虎暂未结算完整日线，系统自动加速略过。", flush=True)
                continue
                
            past_30_days_volume = hist['Volume'].iloc[-31:-1]
            avg_volume_30d = past_30_days_volume.mean()
            if avg_volume_30d <= 0: continue
            
            price_today = hist['Close'].iloc[-1]
            vol_today = hist['Volume'].iloc[-1]
            turnover_today = price_today * vol_today
            current_multiplier = vol_today / avg_volume_30d
            
            # ✨ ✨ 终极彻底修复：在 IF 过滤之前，零延时强行把真实数据喷射到控制台屏幕上！
            print(f"   📊 【实盘数据体检卡】 -> 股票: {ticker_symbol} | 今日单日总成交额: ￥{turnover_today:,.0f} | 今日真实放量倍数: {current_multiplier:.2f}x", flush=True)
            
            if price_today < 2.0: continue 
            if turnover_today < MIN_TODAY_TURNOVER_RMB: continue
            
            if current_multiplier >= A_VOLUME_MULTIPLIER:
                raw_shares = SINGLE_A_BUDGET_RMB / price_today
                suggested_shares = int(raw_shares // 100) * 100  
                if suggested_shares < 100: suggested_shares = 100
                stop_loss_price = price_today * 0.93  
                
                stock_name = ticker.info.get("shortName", ticker_symbol)
                
                push_title = f"🇨🇳 A股单日暴破警报：【{stock_name}】！"
                push_content = (
                    f"🏷️ 【交易演练阶段】: 🧪 A 股单日物量突破\n"
                    f"💰 今日收盘价: ￥{price_today:.2f} | 📊 今日突发异动放量: {current_multiplier:.2f}倍\n"
                    f"🔥 今日单日总换手成交额达到: 【 ￥{turnover_today/10000:.1f} 万 】\n"
                    f"------------------------\n"
                    f"🎯 【A股单日雷达突击单】:\n"
                    f"💵 本笔固定拨发轻仓子弹: 【 ￥5,000 元 】\n"
                    f"🛒 策略建议即刻买入: 【 {suggested_shares} 股 】 (100股整手取整)\n"
                    f"🛑 【硬核止损防线】: 若买入，A股 7% 硬止损价为 【 ￥{stop_loss_price:.2f} 元 】\n"
                    f"📝 提示: 100% 实时结算数据。破位必须严格执行止损！"
                )
                send_to_bark_raw(title=push_title, content=push_content, group="A股单日主力爆破")
                
            time.sleep(1.5) # 稳健防封锁延时
        except Exception as e: 
            print(f"   ❌ 标的 {ticker_symbol} 运行时发生内部阻塞扰动: {e}", flush=True)
            continue

if __name__ == "__main__":
    execute_china_strategy()
    print("🏁 中国 A 股单日异动清洗扫描完全结束。", flush=True)
