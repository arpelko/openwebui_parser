import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError


load_dotenv()


class Settings(BaseModel):
    litellm_api_base: str = Field(alias="LITELLM_API_BASE")
    litellm_api_key: str = Field(alias="LITELLM_API_KEY")
    llm_model: str = Field(default="openai/gpt-5-mini", alias="LLM_MODEL")
    chunk_size_chars: int = Field(default=18000, alias="CHUNK_SIZE_CHARS")
    llm_temperature: float = Field(default=0.1, alias="LLM_TEMPERATURE")
    llm_max_output_tokens: int = Field(default=4000, alias="LLM_MAX_OUTPUT_TOKENS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    input_dir: str = Field(default="./input", alias="INPUT_DIR")
    output_dir: str = Field(default="./output", alias="OUTPUT_DIR")


def load_settings() -> Settings:
    data = {
        "LITELLM_API_BASE": os.getenv("LITELLM_API_BASE"),
        "LITELLM_API_KEY": os.getenv("LITELLM_API_KEY"),
        "LLM_MODEL": os.getenv("LLM_MODEL"),
        "CHUNK_SIZE_CHARS": os.getenv("CHUNK_SIZE_CHARS"),
        "LLM_TEMPERATURE": os.getenv("LLM_TEMPERATURE"),
        "LLM_MAX_OUTPUT_TOKENS": os.getenv("LLM_MAX_OUTPUT_TOKENS"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL"),
        "INPUT_DIR": os.getenv("INPUT_DIR"),
        "OUTPUT_DIR": os.getenv("OUTPUT_DIR"),
    }

    try:
        return Settings.model_validate(data)
    except ValidationError as e:
        raise RuntimeError(f"Asetusten validointi epäonnistui:\n{e}")