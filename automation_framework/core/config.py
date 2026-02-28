# automation_framework/core/config.py
# Revision No: 001
# Goals: Define configuration settings for the automation framework.
# Type of Code Response: Add new code

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)


@dataclass
class AutomationConfig:
    """Configuration settings for automation framework."""
    openai_api_key: str = "asdasd"
    openai_base_url: str = "http://0.0.0.0:8080/v1"
    llm_provider: str = "openai"
    max_retries: int = 3
    timeout: int = 30
    screenshot_dir: Path = Path("/var/lib/automation/screenshots")
    log_dir: Path = Path("/var/log/automation")
    debug: bool = False
    max_concurrent_actions: int = 5
    database_url: str = "sqlite:///./automation.db"
    models_dir: Optional[Path] = Path("./models")
    openai_key: str = "asdasd"
    BASE_URL: str = "http://0.0.0.0:8080/v1"
    mlx_model: str = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"
    mlx_max_output_tokens: int = 512
    mlx_temperature: float = 0.2

    @classmethod
    def from_env(cls) -> "AutomationConfig":
        """Create config from environment variables."""
        try:
            return cls(
                openai_api_key=os.getenv("OPENAI_API_KEY", "asdas"),
                openai_base_url=os.getenv("OPENAI_BASE_URL", "http://0.0.0.0:8080/v1"),
                llm_provider=os.getenv("LLM_PROVIDER", "openai"),
                max_retries=int(os.getenv("MAX_RETRIES", "3")),
                timeout=int(os.getenv("TIMEOUT", "30")),
                screenshot_dir=Path(os.getenv("SCREENSHOT_DIR", "/var/lib/automation/screenshots")),
                log_dir=Path(os.getenv("LOG_DIR", "/var/log/automation")),
                debug=os.getenv("DEBUG", "false").lower() == "true",
                max_concurrent_actions=int(os.getenv("MAX_CONCURRENT_ACTIONS", "5")),
                database_url=os.getenv("DATABASE_URL", "sqlite:///./automation.db"),
                models_dir=Path(os.getenv("MODELS_DIR", "./models")),
                mlx_model=os.getenv("MLX_MODEL", "mlx-community/Meta-Llama-3-8B-Instruct-4bit"),
                mlx_max_output_tokens=int(os.getenv("MLX_MAX_OUTPUT_TOKENS", "512")),
                mlx_temperature=float(os.getenv("MLX_TEMPERATURE", "0.2")),
            )
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid environment variable: {e}")
            raise

    @classmethod
    def from_yaml(cls, path: Path) -> "AutomationConfig":
        """Create config from YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        try:
            with open(path) as f:
                data = yaml.safe_load(f)

            return cls(
                openai_api_key=data.get("openai_api_key"),
                openai_base_url=data.get("openai_base_url", "http://0.0.0.0:8080/v1"),
                llm_provider=data.get("llm_provider", "openai"),
                max_retries=data.get("max_retries", 3),
                timeout=data.get("timeout", 30),
                screenshot_dir=Path(data.get("screenshot_dir", "/var/lib/automation/screenshots")),
                log_dir=Path(data.get("log_dir", "/var/log/automation")),
                debug=data.get("debug", False),
                max_concurrent_actions=data.get("max_concurrent_actions", 5),
                database_url=data.get("database_url", "sqlite:///./automation.db"),
                models_dir=Path(data.get("models_dir", "./models")),
                mlx_model=data.get("mlx_model", "mlx-community/Meta-Llama-3-8B-Instruct-4bit"),
                mlx_max_output_tokens=data.get("mlx_max_output_tokens", 512),
                mlx_temperature=data.get("mlx_temperature", 0.2),
            )
        except (ValueError, TypeError, AttributeError) as e:
            logger.error(f"Invalid config file format: {e}")
            raise

# Dependencies: os, typing, dataclasses, pathlib, yaml, logging
# Required Actions: None
# CLI Commands: None
# Is the script complete? Yes
# Is the code chunked version? No
# Is the code finished and commit-ready? Yes
# Are there any gaps that should be fixed in the next iteration? No
# Goals for the file in the following code block in case it's incomplete: N/A
