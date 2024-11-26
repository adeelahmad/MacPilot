# automation_framework/utils/decorators.py
# Revision No: 001
# Goals: Implement decorator utilities.
# Type of Code Response: Add new code

import functools
import logging
import time
import traceback
from typing import Any, Callable, Coroutine
import asyncio

from core.config import AutomationConfig

logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0):
    """Retry decorator with exponential backoff."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (2 ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}"
                        )
                        await asyncio.sleep(wait_time)  # Use asyncio.sleep
            if last_exception:
                raise last_exception  # Reraise the last exception
            return None  # Should not reach here, but added for type hinting

        return wrapper

    return decorator


def log_execution(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
    """Log function execution with timing."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.2f}s: {e}\nTraceback:\n{traceback.format_exc()}")
            raise

    return wrapper


def validate_config(required_keys: list[str]):
    """Validate required configuration keys exist."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            if not hasattr(self, 'config') or not isinstance(self.config, AutomationConfig):
                raise ValueError("Instance must have AutomationConfig")

            missing_keys = [
                key for key in required_keys
                if not hasattr(self.config, key) or getattr(self.config, key) is None
            ]
            if missing_keys:
                raise ValueError(f"Missing or None required config keys: {missing_keys}")

            return await func(self, *args, **kwargs)

        return wrapper

    return decorator


def measure_performance(logger: logging.Logger):
    """Measure and log function performance metrics."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            start_time = time.time()
            start_memory = process.memory_info().rss

            try:
                result = await func(*args, **kwargs)

                end_time = time.time()
                end_memory = process.memory_info().rss
                duration = end_time - start_time
                memory_diff = end_memory - start_memory

                logger.info(
                    f"Performance metrics for {func.__name__}:\n"
                    f"Duration: {duration:.2f}s\n"
                    f"Memory usage: {memory_diff / 1024 / 1024:.2f}MB"
                )

                return result
            except Exception as e:
                end_time = time.time()
                logger.error(
                    f"Error in {func.__name__} after {end_time - start_time:.2f}s: {str(e)}"
                )
                raise

        return wrapper

    return decorator

# Dependencies: functools, logging, time, traceback, typing, ..core.config, asyncio, psutil, os
# Required Actions: None
# CLI Commands: None
# Is the script complete? Yes
# Is the code chunked version? No
# Is the code finished and commit-ready? Yes
# Are there any gaps that should be fixed in the next iteration? No
# Goals for the file in the following code block in case it's incomplete: N/A
