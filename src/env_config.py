"""
Environment Configuration Module
Loads and validates environment variables with sensible defaults
"""

import os
from typing import Optional, List
from pathlib import Path


class EnvConfig:
    """Environment configuration with validation"""

    def __init__(self):
        """Initialize configuration from environment variables"""
        self.load_dotenv()
        self.validate_required()

    @staticmethod
    def load_dotenv():
        """Load environment variables from .env file if it exists"""
        try:
            from dotenv import load_dotenv
            env_path = Path(__file__).parent.parent / '.env'
            if env_path.exists():
                load_dotenv(env_path)
        except ImportError:
            # python-dotenv not installed, skip
            pass

    def validate_required(self):
        """Validate that required environment variables are set"""
        required_vars = []

        # Check critical variables
        if not self.jwt_secret_key or self.jwt_secret_key == "your-secret-key-change-this-in-production-use-env-var":
            if self.environment == "production":
                required_vars.append("JWT_SECRET_KEY")

        if not self.anthropic_api_key or self.anthropic_api_key.startswith("sk-ant-your"):
            required_vars.append("ANTHROPIC_API_KEY")

        if required_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(required_vars)}. "
                f"Please set them in .env file or environment."
            )

    # JWT Authentication
    @property
    def jwt_secret_key(self) -> str:
        return os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production-use-env-var")

    @property
    def jwt_algorithm(self) -> str:
        return os.getenv("JWT_ALGORITHM", "HS256")

    @property
    def access_token_expire_minutes(self) -> int:
        return int(os.getenv("SESSION_EXPIRE_MINUTES", "30"))

    # API Configuration
    @property
    def anthropic_api_key(self) -> str:
        return os.getenv("ANTHROPIC_API_KEY", "")

    # Database Configuration
    @property
    def database_url(self) -> str:
        return os.getenv("DATABASE_URL", "sqlite:///data/applications.db")

    # Application Settings
    @property
    def environment(self) -> str:
        return os.getenv("ENVIRONMENT", "development")

    @property
    def debug(self) -> bool:
        return os.getenv("DEBUG", "true").lower() == "true"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    # Server Configuration
    @property
    def host(self) -> str:
        return os.getenv("HOST", "0.0.0.0")

    @property
    def port(self) -> int:
        return int(os.getenv("PORT", "8000"))

    # Security Settings
    @property
    def cors_origins(self) -> List[str]:
        origins = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000"
        )
        return [origin.strip() for origin in origins.split(",")]

    # Rate Limiting
    @property
    def rate_limit_register(self) -> str:
        return os.getenv("RATE_LIMIT_REGISTER", "5/hour")

    @property
    def rate_limit_login(self) -> str:
        return os.getenv("RATE_LIMIT_LOGIN", "10/minute")

    @property
    def rate_limit_search(self) -> str:
        return os.getenv("RATE_LIMIT_SEARCH", "20/hour")

    @property
    def rate_limit_apply(self) -> str:
        return os.getenv("RATE_LIMIT_APPLY", "10/hour")

    @property
    def rate_limit_upload(self) -> str:
        return os.getenv("RATE_LIMIT_UPLOAD", "10/hour")

    # Job Application Settings
    @property
    def max_applications_per_day(self) -> int:
        return int(os.getenv("MAX_APPLICATIONS_PER_DAY", "20"))

    @property
    def auto_submit(self) -> bool:
        return os.getenv("AUTO_SUBMIT", "false").lower() == "true"

    @property
    def headless(self) -> bool:
        return os.getenv("HEADLESS", "true").lower() == "true"

    # File Upload Limits
    @property
    def max_resume_size_mb(self) -> int:
        return int(os.getenv("MAX_RESUME_SIZE_MB", "10"))

    @property
    def max_resume_size_bytes(self) -> int:
        return self.max_resume_size_mb * 1024 * 1024

    @property
    def allowed_resume_extensions(self) -> List[str]:
        extensions = os.getenv("ALLOWED_RESUME_EXTENSIONS", ".pdf,.docx,.doc,.txt")
        return [ext.strip() for ext in extensions.split(",")]

    # Logging
    @property
    def log_level(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO")

    @property
    def log_file(self) -> Optional[str]:
        return os.getenv("LOG_FILE", "logs/app.log")

    def __repr__(self) -> str:
        """String representation (hide sensitive values)"""
        return (
            f"EnvConfig("
            f"environment={self.environment}, "
            f"debug={self.debug}, "
            f"host={self.host}, "
            f"port={self.port}"
            f")"
        )


# Global instance
env_config = EnvConfig()
