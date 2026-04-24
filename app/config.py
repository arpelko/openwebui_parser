import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

load_dotenv()


class Settings(BaseModel):
    litellm_api_base: str = Field(alias="LITELLM_API_BASE")
    litellm_api_key: str = Field(alias="LITELLM_API_KEY")

    llm_model_stage1: str = Field(default="openai/gpt-5-nano", alias="LLM_MODEL_STAGE1")
    llm_model_stage2: str = Field(default="openai/gpt-5-mini", alias="LLM_MODEL_STAGE2")

    chunk_size_chars: int = Field(default=18000, alias="CHUNK_SIZE_CHARS")

    llm_temperature_stage1: float = Field(default=0.1, alias="LLM_TEMPERATURE_STAGE1")
    llm_temperature_stage2: float = Field(default=0.1, alias="LLM_TEMPERATURE_STAGE2")

    llm_max_output_tokens_stage1: int = Field(default=4000, alias="LLM_MAX_OUTPUT_TOKENS_STAGE1")
    llm_max_output_tokens_stage2: int = Field(default=4000, alias="LLM_MAX_OUTPUT_TOKENS_STAGE2")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    input_dir: str = Field(default="./input", alias="INPUT_DIR")
    output_dir: str = Field(default="./output", alias="OUTPUT_DIR")
    processed_dir: str = Field(default="./processed", alias="PROCESSED_DIR")
    failed_dir: str = Field(default="./failed", alias="FAILED_DIR")


def load_settings() -> Settings:
    data = {
        "LITELLM_API_BASE": os.getenv("LITELLM_API_BASE"),
        "LITELLM_API_KEY": os.getenv("LITELLM_API_KEY"),

        "LLM_MODEL_STAGE1": os.getenv("LLM_MODEL_STAGE1"),
        "LLM_MODEL_STAGE2": os.getenv("LLM_MODEL_STAGE2"),

        "CHUNK_SIZE_CHARS": os.getenv("CHUNK_SIZE_CHARS"),

        "LLM_TEMPERATURE_STAGE1": os.getenv("LLM_TEMPERATURE_STAGE1"),
        "LLM_TEMPERATURE_STAGE2": os.getenv("LLM_TEMPERATURE_STAGE2"),

        "LLM_MAX_OUTPUT_TOKENS_STAGE1": os.getenv("LLM_MAX_OUTPUT_TOKENS_STAGE1"),
        "LLM_MAX_OUTPUT_TOKENS_STAGE2": os.getenv("LLM_MAX_OUTPUT_TOKENS_STAGE2"),

        "LOG_LEVEL": os.getenv("LOG_LEVEL"),
        "INPUT_DIR": os.getenv("INPUT_DIR"),
        "OUTPUT_DIR": os.getenv("OUTPUT_DIR"),
        "PROCESSED_DIR": os.getenv("PROCESSED_DIR"),
        "FAILED_DIR": os.getenv("FAILED_DIR"),
    }

    try:
        return Settings.model_validate(data)
    except ValidationError as e:
        raise RuntimeError(f"Asetusten validointi epäonnistui:\n{e}")