"""
KTSTOCK - ML Price Prediction
Dự đoán giá cổ phiếu bằng Machine Learning (XGBoost + Feature Engineering).
"""
from typing import Optional
import pandas as pd
import numpy as np
from loguru import logger

from src.core.analysis.technical import TechnicalAnalysis
from src.utils.decorators import timer


class PricePredictor:
    """
    Dự đoán giá cổ phiếu bằng ML.
    Sử dụng XGBoost Regressor với features từ technical analysis.
    """

    def __init__(self):
        self._model = None
        self._feature_names: list[str] = []
        self._is_trained = False

    @timer
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Tạo features từ OHLCV data.

        Args:
            df: DataFrame OHLCV (date, open, high, low, close, volume)

        Returns:
            DataFrame với features cho ML
        """
        ta = TechnicalAnalysis(df)
        featured = ta.calculate_all()

        # Thêm features bổ sung
        featured["return_1d"] = featured["close"].pct_change()
        featured["return_5d"] = featured["close"].pct_change(5)
        featured["return_10d"] = featured["close"].pct_change(10)
        featured["volatility_10d"] = featured["return_1d"].rolling(10).std()
        featured["volatility_20d"] = featured["return_1d"].rolling(20).std()
        featured["volume_ratio"] = featured["volume"] / featured["vol_sma_20"]
        featured["price_range"] = (featured["high"] - featured["low"]) / featured["close"]
        featured["gap"] = featured["open"] / featured["close"].shift(1) - 1

        # Target: return ngày tiếp theo
        featured["target"] = featured["close"].shift(-1) / featured["close"] - 1

        return featured.dropna()

    @timer
    def train(self, df: pd.DataFrame, test_size: float = 0.2) -> dict:
        """
        Train model XGBoost.

        Args:
            df: DataFrame OHLCV
            test_size: Tỷ lệ test set

        Returns:
            {"train_score", "test_score", "feature_importance"}
        """
        try:
            from xgboost import XGBRegressor
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import mean_squared_error, r2_score
        except ImportError:
            logger.error("❌ xgboost/sklearn not installed")
            return {"error": "Missing ML dependencies"}

        featured = self.prepare_features(df)

        # Chọn features
        exclude_cols = {"date", "target", "close", "open", "high", "low", "volume",
                        "chikou_span", "senkou_a", "senkou_b"}
        self._feature_names = [c for c in featured.columns if c not in exclude_cols]

        X = featured[self._feature_names].values
        y = featured["target"].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False  # Time series → không shuffle
        )

        self._model = XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )

        self._model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
        self._is_trained = True

        # Evaluate
        train_pred = self._model.predict(X_train)
        test_pred = self._model.predict(X_test)

        # Feature importance
        importance = dict(zip(self._feature_names, self._model.feature_importances_))
        top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]

        result = {
            "train_r2": round(r2_score(y_train, train_pred), 4),
            "test_r2": round(r2_score(y_test, test_pred), 4),
            "train_rmse": round(np.sqrt(mean_squared_error(y_train, train_pred)), 6),
            "test_rmse": round(np.sqrt(mean_squared_error(y_test, test_pred)), 6),
            "feature_importance": top_features,
            "num_features": len(self._feature_names),
            "train_size": len(X_train),
            "test_size": len(X_test),
        }

        logger.info(f"✅ ML Model trained | Test R²={result['test_r2']} | RMSE={result['test_rmse']}")
        return result

    @timer
    def predict(self, df: pd.DataFrame, days_ahead: int = 5) -> Optional[dict]:
        """
        Dự đoán giá tương lai.

        Args:
            df: DataFrame OHLCV gần nhất
            days_ahead: Số ngày dự đoán

        Returns:
            {"predictions": list, "current_price": float}
        """
        if not self._is_trained or self._model is None:
            logger.warning("⚠️ Model chưa được train")
            return None

        featured = self.prepare_features(df)
        if featured.empty:
            return None

        last_row = featured.iloc[-1]
        current_price = float(last_row["close"])

        predictions = []
        predicted_price = current_price

        for day in range(1, days_ahead + 1):
            try:
                X = featured[self._feature_names].iloc[-1:].values
                predicted_return = float(self._model.predict(X)[0])
                predicted_price = predicted_price * (1 + predicted_return)

                predictions.append({
                    "day": day,
                    "predicted_price": round(predicted_price, 2),
                    "predicted_return": round(predicted_return * 100, 3),
                })
            except Exception as e:
                logger.warning(f"⚠️ Prediction error for day {day}: {e}")
                break

        overall_return = (predictions[-1]["predicted_price"] / current_price - 1) * 100 if predictions else 0

        return {
            "current_price": current_price,
            "predictions": predictions,
            "overall_return": round(overall_return, 2),
            "direction": "up" if overall_return > 0 else "down",
            "model_type": "XGBoost",
        }
