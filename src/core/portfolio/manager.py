"""
KTSTOCK - Portfolio Manager
Quản lý danh mục đầu tư + Tối ưu Markowitz.
"""
from typing import Optional
import pandas as pd
import numpy as np
from loguru import logger

from src.data.database.connection import get_db
from src.utils.decorators import timer


class PortfolioManager:
    """Quản lý danh mục đầu tư."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.db = get_db()

    def create_portfolio(self, name: str, description: str = "", initial_capital: float = 0) -> int:
        """Tạo portfolio mới. Returns portfolio_id."""
        return self.db.execute_insert(
            "INSERT INTO portfolios (user_id, name, description, initial_capital) VALUES (?, ?, ?, ?)",
            (self.user_id, name, description, initial_capital)
        )

    def get_portfolios(self) -> list[dict]:
        """Lấy danh sách portfolios của user."""
        return self.db.execute(
            "SELECT * FROM portfolios WHERE user_id = ? ORDER BY created_at DESC",
            (self.user_id,)
        )

    def add_position(self, portfolio_id: int, symbol: str, quantity: float, avg_price: float, notes: str = "") -> int:
        """Thêm vị thế mới."""
        return self.db.execute_insert(
            """INSERT INTO positions (portfolio_id, symbol, quantity, avg_price, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (portfolio_id, symbol.upper(), quantity, avg_price, notes)
        )

    def update_position(self, position_id: int, quantity: float, avg_price: float):
        """Cập nhật vị thế."""
        self.db.execute_write(
            "UPDATE positions SET quantity = ?, avg_price = ? WHERE id = ?",
            (quantity, avg_price, position_id)
        )

    def close_position(self, position_id: int):
        """Đóng vị thế."""
        from datetime import datetime
        self.db.execute_write(
            "UPDATE positions SET closed_at = ? WHERE id = ?",
            (datetime.now().isoformat(), position_id)
        )

    def get_positions(self, portfolio_id: int, include_closed: bool = False) -> list[dict]:
        """Lấy danh sách vị thế."""
        query = "SELECT * FROM positions WHERE portfolio_id = ?"
        if not include_closed:
            query += " AND closed_at IS NULL"
        return self.db.execute(query, (portfolio_id,))

    @timer
    def get_portfolio_summary(self, portfolio_id: int, current_prices: dict[str, float] = None) -> dict:
        """
        Tổng hợp portfolio.

        Args:
            portfolio_id: ID portfolio
            current_prices: Dict {symbol: current_price}

        Returns:
            {"total_value", "total_cost", "profit_loss", "profit_loss_pct", "positions"}
        """
        positions = self.get_positions(portfolio_id)
        if not positions:
            return {"total_value": 0, "total_cost": 0, "profit_loss": 0, "positions": []}

        current_prices = current_prices or {}
        total_cost = 0
        total_value = 0
        enriched = []

        for pos in positions:
            qty = pos["quantity"]
            avg = pos["avg_price"]
            cost = qty * avg
            total_cost += cost

            current = current_prices.get(pos["symbol"], avg)
            value = qty * current
            total_value += value

            pnl = value - cost
            pnl_pct = (pnl / cost * 100) if cost > 0 else 0

            enriched.append({
                **pos,
                "current_price": current,
                "market_value": round(value, 0),
                "cost_basis": round(cost, 0),
                "profit_loss": round(pnl, 0),
                "profit_loss_pct": round(pnl_pct, 2),
                "weight": 0,  # sẽ tính sau
            })

        # Tính weight
        for p in enriched:
            p["weight"] = round(p["market_value"] / total_value * 100, 2) if total_value > 0 else 0

        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

        return {
            "total_value": round(total_value, 0),
            "total_cost": round(total_cost, 0),
            "profit_loss": round(total_pnl, 0),
            "profit_loss_pct": round(total_pnl_pct, 2),
            "positions": enriched,
            "num_positions": len(enriched),
        }


class PortfolioOptimizer:
    """
    Tối ưu danh mục đầu tư theo Markowitz (Modern Portfolio Theory).
    """

    @staticmethod
    @timer
    def optimize(
        returns_df: pd.DataFrame,
        num_portfolios: int = 5000,
        risk_free_rate: float = 0.04,
    ) -> dict:
        """
        Tối ưu hóa portfolio bằng Monte Carlo simulation.

        Args:
            returns_df: DataFrame daily returns (mỗi cột là 1 symbol)
            num_portfolios: Số portfolio mô phỏng
            risk_free_rate: Lãi suất phi rủi ro (4%)

        Returns:
            {"optimal_weights", "efficient_frontier", "max_sharpe", "min_volatility"}
        """
        num_assets = len(returns_df.columns)
        symbols = list(returns_df.columns)
        mean_returns = returns_df.mean() * 252  # Annualized
        cov_matrix = returns_df.cov() * 252

        results = np.zeros((3, num_portfolios))
        weights_record = []

        for i in range(num_portfolios):
            weights = np.random.random(num_assets)
            weights /= weights.sum()
            weights_record.append(weights)

            port_return = np.dot(weights, mean_returns)
            port_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe = (port_return - risk_free_rate) / port_std if port_std > 0 else 0

            results[0, i] = port_return * 100
            results[1, i] = port_std * 100
            results[2, i] = sharpe

        # Max Sharpe portfolio
        max_sharpe_idx = results[2].argmax()
        max_sharpe_weights = weights_record[max_sharpe_idx]

        # Min Volatility portfolio
        min_vol_idx = results[1].argmin()
        min_vol_weights = weights_record[min_vol_idx]

        return {
            "symbols": symbols,
            "max_sharpe": {
                "weights": {s: round(w * 100, 2) for s, w in zip(symbols, max_sharpe_weights)},
                "return": round(results[0, max_sharpe_idx], 2),
                "risk": round(results[1, max_sharpe_idx], 2),
                "sharpe": round(results[2, max_sharpe_idx], 3),
            },
            "min_volatility": {
                "weights": {s: round(w * 100, 2) for s, w in zip(symbols, min_vol_weights)},
                "return": round(results[0, min_vol_idx], 2),
                "risk": round(results[1, min_vol_idx], 2),
                "sharpe": round(results[2, min_vol_idx], 3),
            },
            "efficient_frontier": {
                "returns": results[0].tolist(),
                "risks": results[1].tolist(),
                "sharpes": results[2].tolist(),
            },
            "num_simulations": num_portfolios,
        }
