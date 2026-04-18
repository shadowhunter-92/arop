from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://arop:arop_dev@localhost:5432/arop"
    arop_master_key: str = "changeme"
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Risk mitigation: data privacy defaults
    # hash_payloads=True means prompts/responses are stored as SHA-256 hashes only.
    # Set store_raw=True (opt-in) to also persist plaintext in request_body/response_body.
    # Enterprises can keep hash_payloads=True and store_raw=False to prevent sensitive
    # data from ever leaving their network perimeter even in a cloud-hosted setup.
    hash_payloads: bool = True
    store_raw: bool = False

    # Optional: S3-compatible URL for storing raw payloads in customer-owned storage.
    # When set alongside store_raw=True, raw content is uploaded here instead of the DB.
    raw_storage_url: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
