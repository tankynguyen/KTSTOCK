"""
KTSTOCK - Fundamental Analysis Engine
Phân tích cơ bản: định giá, chỉ số tài chính, DCF, so sánh ngành.
"""
from typing import Optional
import pandas as pd
import numpy as np
from loguru import logger

from src.utils.decorators import timer


class FundamentalAnalysis:
    """
    Engine phân tích cơ bản cổ phiếu.
    Tính toán các chỉ số tài chính và định giá.
    """

    # =========================================
    # Chỉ số định giá
    # =========================================
    @staticmethod
    def pe_ratio(price: float, eps: float) -> Optional[float]:
        """P/E - Giá trên lợi nhuận."""
        if eps and eps != 0:
            return round(price / eps, 2)
        return None

    @staticmethod
    def pb_ratio(price: float, book_value_per_share: float) -> Optional[float]:
        """P/B - Giá trên giá trị sổ sách."""
        if book_value_per_share and book_value_per_share != 0:
            return round(price / book_value_per_share, 2)
        return None

    @staticmethod
    def ps_ratio(market_cap: float, revenue: float) -> Optional[float]:
        """P/S - Giá trên doanh thu."""
        if revenue and revenue != 0:
            return round(market_cap / revenue, 2)
        return None

    @staticmethod
    def peg_ratio(pe: float, earnings_growth: float) -> Optional[float]:
        """PEG - P/E trên tăng trưởng lợi nhuận."""
        if earnings_growth and earnings_growth != 0 and pe:
            return round(pe / (earnings_growth * 100), 2)
        return None

    @staticmethod
    def ev_ebitda(enterprise_value: float, ebitda: float) -> Optional[float]:
        """EV/EBITDA."""
        if ebitda and ebitda != 0:
            return round(enterprise_value / ebitda, 2)
        return None

    # =========================================
    # Chỉ số hiệu quả
    # =========================================
    @staticmethod
    def roe(net_income: float, equity: float) -> Optional[float]:
        """ROE - Lợi nhuận trên vốn chủ sở hữu."""
        if equity and equity != 0:
            return round(net_income / equity * 100, 2)
        return None

    @staticmethod
    def roa(net_income: float, total_assets: float) -> Optional[float]:
        """ROA - Lợi nhuận trên tổng tài sản."""
        if total_assets and total_assets != 0:
            return round(net_income / total_assets * 100, 2)
        return None

    @staticmethod
    def roic(nopat: float, invested_capital: float) -> Optional[float]:
        """ROIC - Lợi nhuận trên vốn đầu tư."""
        if invested_capital and invested_capital != 0:
            return round(nopat / invested_capital * 100, 2)
        return None

    # =========================================
    # Chỉ số tài chính
    # =========================================
    @staticmethod
    def debt_to_equity(total_debt: float, equity: float) -> Optional[float]:
        """D/E - Nợ trên vốn chủ sở hữu."""
        if equity and equity != 0:
            return round(total_debt / equity, 2)
        return None

    @staticmethod
    def current_ratio(current_assets: float, current_liabilities: float) -> Optional[float]:
        """Tỷ lệ thanh toán hiện hành."""
        if current_liabilities and current_liabilities != 0:
            return round(current_assets / current_liabilities, 2)
        return None

    @staticmethod
    def gross_margin(gross_profit: float, revenue: float) -> Optional[float]:
        """Biên lợi nhuận gộp (%)."""
        if revenue and revenue != 0:
            return round(gross_profit / revenue * 100, 2)
        return None

    @staticmethod
    def net_margin(net_income: float, revenue: float) -> Optional[float]:
        """Biên lợi nhuận ròng (%)."""
        if revenue and revenue != 0:
            return round(net_income / revenue * 100, 2)
        return None

    # =========================================
    # DCF Valuation (Định giá chiết khấu dòng tiền)
    # =========================================
    @timer
    def dcf_valuation(
        self,
        free_cash_flows: list[float],
        growth_rate: float = 0.05,
        terminal_growth: float = 0.02,
        discount_rate: float = 0.10,
        shares_outstanding: float = 1.0,
        projection_years: int = 5,
    ) -> dict:
        """
        Định giá DCF (Discounted Cash Flow).

        Args:
            free_cash_flows: Dòng tiền tự do lịch sử
            growth_rate: Tỷ lệ tăng trưởng dự kiến
            terminal_growth: Tỷ lệ tăng trưởng vĩnh viễn
            discount_rate: Tỷ lệ chiết khấu (WACC)
            shares_outstanding: Số lượng cổ phiếu lưu hành
            projection_years: Số năm dự phóng

        Returns:
            {"intrinsic_value", "projected_fcf", "terminal_value", "total_pv"}
        """
        if not free_cash_flows:
            return {"intrinsic_value": 0, "error": "No FCF data"}

        last_fcf = free_cash_flows[-1]

        # Dự phóng FCF tương lai
        projected = []
        pv_sum = 0
        for year in range(1, projection_years + 1):
            fcf = last_fcf * (1 + growth_rate) ** year
            pv = fcf / (1 + discount_rate) ** year
            projected.append({"year": year, "fcf": round(fcf, 0), "pv": round(pv, 0)})
            pv_sum += pv

        # Terminal Value
        terminal_fcf = projected[-1]["fcf"] * (1 + terminal_growth)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth)
        pv_terminal = terminal_value / (1 + discount_rate) ** projection_years

        total_pv = pv_sum + pv_terminal
        intrinsic_value = total_pv / shares_outstanding if shares_outstanding > 0 else 0

        return {
            "intrinsic_value": round(intrinsic_value, 0),
            "total_pv": round(total_pv, 0),
            "pv_fcf": round(pv_sum, 0),
            "pv_terminal": round(pv_terminal, 0),
            "terminal_value": round(terminal_value, 0),
            "projected_fcf": projected,
            "assumptions": {
                "growth_rate": growth_rate,
                "terminal_growth": terminal_growth,
                "discount_rate": discount_rate,
                "projection_years": projection_years,
            },
        }

    # =========================================
    # Phân tích tổng hợp
    # =========================================
    @timer
    def analyze(
        self,
        current_price: float,
        financial_data: dict,
    ) -> dict:
        """
        Phân tích cơ bản tổng hợp.

        Args:
            current_price: Giá hiện tại
            financial_data: Dict chứa dữ liệu tài chính

        Returns:
            Dict chứa tất cả chỉ số và đánh giá
        """
        eps = financial_data.get("eps", 0)
        bvps = financial_data.get("book_value_per_share", 0)
        revenue = financial_data.get("revenue", 0)
        net_income = financial_data.get("net_income", 0)
        total_assets = financial_data.get("total_assets", 0)
        equity = financial_data.get("equity", 0)
        total_debt = financial_data.get("total_debt", 0)
        gross_profit = financial_data.get("gross_profit", 0)
        market_cap = financial_data.get("market_cap", 0)

        pe = self.pe_ratio(current_price, eps)
        pb = self.pb_ratio(current_price, bvps)

        result = {
            "valuation": {
                "pe_ratio": pe,
                "pb_ratio": pb,
                "ps_ratio": self.ps_ratio(market_cap, revenue),
            },
            "profitability": {
                "roe": self.roe(net_income, equity),
                "roa": self.roa(net_income, total_assets),
                "gross_margin": self.gross_margin(gross_profit, revenue),
                "net_margin": self.net_margin(net_income, revenue),
            },
            "financial_health": {
                "debt_to_equity": self.debt_to_equity(total_debt, equity),
                "current_ratio": self.current_ratio(
                    financial_data.get("current_assets", 0),
                    financial_data.get("current_liabilities", 0),
                ),
            },
        }

        # Đánh giá
        score = 0
        notes = []

        if pe and 0 < pe < 15:
            score += 1
            notes.append("P/E thấp → có thể undervalued")
        elif pe and pe > 30:
            score -= 1
            notes.append("P/E cao → có thể overvalued")

        roe_val = result["profitability"]["roe"]
        if roe_val and roe_val > 15:
            score += 1
            notes.append("ROE tốt (>15%)")

        de = result["financial_health"]["debt_to_equity"]
        if de is not None and de < 1:
            score += 1
            notes.append("Nợ/Vốn CSH thấp")
        elif de is not None and de > 2:
            score -= 1
            notes.append("Nợ/Vốn CSH cao")

        result["assessment"] = {
            "score": score,
            "rating": "Tốt" if score >= 2 else ("Trung bình" if score >= 0 else "Yếu"),
            "notes": notes,
        }

        return result
