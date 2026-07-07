"""
Central place for configuration. Nothing in this project should hardcode
a hostname, port, or credential — everything comes from the environment
so the same code runs on your laptop, a teammate's laptop, or a container
without edits. See .env.example for the variables this expects.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()  # reads a local .env file if present; no-op if it isn't


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    name: str
    user: str
    password: str

    @property
    def sqlalchemy_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings(
        host=os.getenv("EAIDA_DB_HOST", "localhost"),
        port=int(os.getenv("EAIDA_DB_PORT", "5432")),
        name=os.getenv("EAIDA_DB_NAME", "eaida"),
        user=os.getenv("EAIDA_DB_USER", "postgres"),
        password=os.getenv("EAIDA_DB_PASSWORD", "postgres"),
    )
