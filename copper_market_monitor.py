#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
铜期货与SCCO股价实时监控脚本
使用Yahoo Finance API获取实时数据，并计算SCCO相对铜价的溢价率

溢价率公式：(SCCO股价 × 总股本) × 4.2 / 900亿 / 铜期货价格
"""

import time
import os
from datetime import datetime

import yfinance as yf

# 配置
COPPER_TICKER = "HG=F"  # 纽约铜期货
SCCO_TICKER = "SCCO"    # 南方铜业
UPDATE_INTERVAL = 60    # 更新间隔（秒）

# 溢价率计算常数
# 4.2：经验倍数，反映SCCO铜资源的开采年限折算因子
PREMIUM_MULTIPLIER = 4.2
# 900亿：参考基准值（单位：元），代表行业内铜资源的基准估值锚点（约900亿元）
PREMIUM_DIVISOR = 900 * 1e8     # 900亿 = 9e10


class CopperMarketMonitor:
    """铜市场实时监控器"""

    def fetch_info(self, ticker: str) -> dict:
        """通过 Yahoo Finance 获取股票/期货的实时信息"""
        try:
            t = yf.Ticker(ticker)
            info = t.info
            return info
        except Exception as e:
            print(f"获取 {ticker} 数据失败: {e}")
            return {}

    def display_copper_futures(self, info: dict) -> float | None:
        """显示铜期货数据，返回当前价格（美元/磅）"""
        if not info:
            print("❌ 无法获取铜期货数据")
            return None

        current = info.get("regularMarketPrice")
        change_pct = info.get("regularMarketChangePercent", 0)
        previous = info.get("previousClose")
        day_high = info.get("dayHigh")
        day_low = info.get("dayLow")
        week52_high = info.get("fiftyTwoWeekHigh")
        week52_low = info.get("fiftyTwoWeekLow")

        change_color = "🟢" if change_pct >= 0 else "🔴"

        print("\n" + "=" * 60)
        print("🟤 纽约铜期货 (HG=F) - COMEX")
        print("=" * 60)
        print(f"当前价格:    ${current:.4f} /磅")
        print(f"涨跌幅度:    {change_color} {change_pct:+.2f}%")
        if previous is not None:
            print(f"昨收价格:    ${previous:.4f}")
        if day_high is not None:
            print(f"今日最高:    ${day_high:.4f}")
        if day_low is not None:
            print(f"今日最低:    ${day_low:.4f}")
        if week52_high is not None:
            print(f"52周最高:    ${week52_high:.2f}")
        if week52_low is not None:
            print(f"52周最低:    ${week52_low:.2f}")

        return current

    def display_scco_stock(self, info: dict) -> tuple[float | None, float | None]:
        """显示SCCO股票数据，返回 (当前股价, 总股本)"""
        if not info:
            print("❌ 无法获取SCCO数据")
            return None, None

        current = info.get("regularMarketPrice")
        change_pct = info.get("regularMarketChangePercent", 0)
        previous = info.get("previousClose")
        day_high = info.get("dayHigh")
        day_low = info.get("dayLow")
        market_cap = info.get("marketCap")
        trailing_pe = info.get("trailingPE")
        dividend_yield = info.get("dividendYield")
        beta = info.get("beta")
        shares_outstanding = info.get("sharesOutstanding")

        change_color = "🟢" if change_pct >= 0 else "🔴"

        print("\n" + "=" * 60)
        print("🏭 南方铜业公司 (SCCO) - NYSE")
        print("=" * 60)
        print(f"当前股价:    ${current:.2f}")
        print(f"涨跌幅度:    {change_color} {change_pct:+.2f}%")
        if previous is not None:
            print(f"昨收价格:    ${previous:.2f}")
        if day_high is not None:
            print(f"今日最高:    ${day_high:.2f}")
        if day_low is not None:
            print(f"今日最低:    ${day_low:.2f}")
        if market_cap is not None:
            print(f"市值:        ${market_cap / 1e9:.2f}B")
        if trailing_pe is not None:
            print(f"市盈率:      {trailing_pe:.2f}")
        if dividend_yield is not None:
            print(f"股息率:      {dividend_yield * 100:.2f}%")
        if beta is not None:
            print(f"Beta系数:    {beta:.3f}")
        if shares_outstanding is not None:
            print(f"总股本:      {shares_outstanding:,.0f} 股")

        return current, shares_outstanding

    def calculate_premium(
        self,
        scco_price: float,
        shares_outstanding: float,
        copper_price: float,
    ) -> float:
        """
        计算SCCO相对铜价的溢价率

        公式：(SCCO股价 × 总股本) × 4.2 / 900亿 / 铜期货价格
        """
        market_cap = scco_price * shares_outstanding
        premium_ratio = market_cap * PREMIUM_MULTIPLIER / PREMIUM_DIVISOR / copper_price
        return premium_ratio

    def display_premium(
        self,
        scco_price: float | None,
        shares_outstanding: float | None,
        copper_price: float | None,
    ) -> None:
        """显示SCCO相对铜价的溢价率"""
        if None in (scco_price, shares_outstanding, copper_price):
            return

        premium_ratio = self.calculate_premium(scco_price, shares_outstanding, copper_price)

        print("\n" + "=" * 60)
        print("📊 SCCO 相对铜价溢价率")
        print("=" * 60)
        print(f"  公式: (SCCO股价 × 总股本) × {PREMIUM_MULTIPLIER} / 900亿 / 铜期货价格")
        print(f"  SCCO股价:     ${scco_price:.2f}")
        print(f"  总股本:       {shares_outstanding:,.0f} 股")
        print(f"  铜期货价格:   ${copper_price:.4f}/磅")
        market_cap = scco_price * shares_outstanding
        print(f"  SCCO市值:     ${market_cap / 1e9:.2f}B")
        print(f"  溢价率:       {premium_ratio:.4f}  ({premium_ratio * 100:.2f}%)")

    def run_once(self) -> None:
        """执行单次数据获取和显示"""
        # 获取数据
        copper_info = self.fetch_info(COPPER_TICKER)
        scco_info = self.fetch_info(SCCO_TICKER)

        # 清屏
        os.system("clear" if os.name != "nt" else "cls")

        # 显示标题
        print("\n" + "█" * 60)
        print("█" + " " * 20 + "铜市场实时监控" + " " * 20 + "█")
        print("█" * 60)
        print(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 显示各板块数据并收集计算所需数值
        copper_price = self.display_copper_futures(copper_info)
        scco_price, shares_outstanding = self.display_scco_stock(scco_info)

        # 显示溢价率
        self.display_premium(scco_price, shares_outstanding, copper_price)

        print("\n" + "=" * 60)
        print(f"⏱️  下次更新: {UPDATE_INTERVAL}秒后 | 按Ctrl+C退出")
        print("=" * 60)

    def run_continuous(self) -> None:
        """持续监控模式"""
        print("\n启动实时监控模式...")
        print(f"更新间隔: {UPDATE_INTERVAL}秒")
        print("按 Ctrl+C 停止监控\n")

        try:
            while True:
                self.run_once()
                time.sleep(UPDATE_INTERVAL)
        except KeyboardInterrupt:
            print("\n\n监控已停止")


def main() -> None:
    monitor = CopperMarketMonitor()

    # 单次运行（用于测试）
    print("\n单次数据获取模式:")
    monitor.run_once()

    # 持续监控模式（取消注释以启用）
    # monitor.run_continuous()


if __name__ == "__main__":
    main()
