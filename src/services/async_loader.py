"""
KTSTOCK - Async Data Loader
Load dữ liệu đa luồng và bất đồng bộ để tối ưu tốc độ.
"""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Optional

import pandas as pd
from loguru import logger


class AsyncDataLoader:
    """
    Load dữ liệu song song với ThreadPoolExecutor và asyncio.
    Tối ưu cho việc fetch nhiều symbols cùng lúc.
    """

    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def load_parallel(
        self,
        func: Callable,
        items: list[Any],
        **kwargs,
    ) -> dict[str, Any]:
        """
        Load dữ liệu song song cho nhiều items.

        Args:
            func: Hàm fetch dữ liệu (nhận item làm tham số đầu tiên)
            items: Danh sách items cần fetch (VD: list symbols)
            **kwargs: Tham số bổ sung cho func

        Returns:
            Dict {item: result} cho mỗi item

        Example:
            loader = AsyncDataLoader()
            results = loader.load_parallel(
                connector.get_historical_data,
                ["VCB", "FPT", "VNM"],
                start_date="2024-01-01",
                end_date="2024-12-31"
            )
        """
        results = {}
        start = time.perf_counter()

        futures = {
            self._executor.submit(func, item, **kwargs): item
            for item in items
        }

        for future in as_completed(futures):
            item = futures[future]
            try:
                result = future.result(timeout=30)
                results[item] = result
            except Exception as e:
                logger.error(f"❌ Parallel load failed for {item}: {e}")
                results[item] = None

        elapsed = time.perf_counter() - start
        success_count = sum(1 for v in results.values() if v is not None)
        logger.info(
            f"⚡ Parallel load: {success_count}/{len(items)} succeeded in {elapsed:.2f}s "
            f"({self.max_workers} workers)"
        )
        return results

    def load_batch_dataframes(
        self,
        func: Callable,
        symbols: list[str],
        **kwargs,
    ) -> Optional[pd.DataFrame]:
        """
        Load và merge DataFrames song song cho nhiều symbols.

        Returns:
            DataFrame đã merge với column 'symbol', hoặc None
        """
        results = self.load_parallel(func, symbols, **kwargs)

        dfs = []
        for symbol, df in results.items():
            if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
                df = df.copy()
                df["symbol"] = symbol
                dfs.append(df)

        if dfs:
            merged = pd.concat(dfs, ignore_index=True)
            logger.info(f"📊 Merged {len(dfs)} DataFrames → {len(merged)} rows")
            return merged
        return None

    async def load_async(
        self,
        async_func: Callable,
        items: list[Any],
        **kwargs,
    ) -> dict[str, Any]:
        """
        Load dữ liệu bất đồng bộ với asyncio.

        Args:
            async_func: Async function
            items: List items
        """
        results = {}
        start = time.perf_counter()

        tasks = [
            self._wrap_async(async_func, item, results, **kwargs)
            for item in items
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.perf_counter() - start
        success_count = sum(1 for v in results.values() if v is not None)
        logger.info(f"⚡ Async load: {success_count}/{len(items)} in {elapsed:.2f}s")
        return results

    async def _wrap_async(self, func, item, results, **kwargs):
        """Wrapper cho async task với error handling."""
        try:
            result = await func(item, **kwargs)
            results[item] = result
        except Exception as e:
            logger.error(f"❌ Async load failed for {item}: {e}")
            results[item] = None

    def load_with_progress(
        self,
        func: Callable,
        items: list[str],
        progress_callback: Optional[Callable] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Load song song với progress callback (cho Streamlit progress bar).

        Args:
            func: Hàm fetch
            items: Danh sách items
            progress_callback: Callable(current, total, item) - VD: st.progress
        """
        results = {}
        total = len(items)

        futures = {
            self._executor.submit(func, item, **kwargs): item
            for item in items
        }

        for i, future in enumerate(as_completed(futures)):
            item = futures[future]
            try:
                results[item] = future.result(timeout=30)
            except Exception as e:
                logger.error(f"❌ Load error for {item}: {e}")
                results[item] = None

            if progress_callback:
                progress_callback(i + 1, total, item)

        return results

    def shutdown(self):
        """Tắt thread pool."""
        self._executor.shutdown(wait=False)

    def __del__(self):
        self.shutdown()
