from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "UeesTask"
    secret_key: str = "cambiar-esta-clave-en-produccion"
    database_url: str = (
        "postgresql+psycopg://ueestask:ueestask_dev_2026@localhost:5432/ueestask"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
