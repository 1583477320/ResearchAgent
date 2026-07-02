from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict


class Settings(BaseSettings):
    # 默认 LLM 配置
    llm_provider: str = "deepseek"
    llm_api_key: str = ""
    llm_api_base_url: str = ""
    llm_model_name: str = "deepseek-chat"
    
    # DeepSeek 配置
    deepseek_api_base_url: str = "https://api.deepseek.com/v1"
    deepseek_api_key: str = ""
    deepseek_model_name: str = "deepseek-chat"
    
    # Qwen 配置
    qwen_api_base_url: str = "https://api.qwenlm.com/v1"
    qwen_api_key: str = ""
    qwen_model_name: str = "qwen3-7b-chat"
    
    # OpenAI 配置（预留）
    openai_api_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model_name: str = "gpt-4o-mini"
    
    # 其他配置
    arxiv_api_url: str = "https://export.arxiv.org/api/query"
    log_level: str = "INFO"
    
    # 预留：多个 LLM 配置映射
    llm_configs: Dict[str, Dict[str, str]] = {
        "deepseek": {
            "api_key": "",
            "api_base_url": "https://api.deepseek.com/v1",
            "model_name": "deepseek-chat"
        },
        "qwen": {
            "api_key": "",
            "api_base_url": "https://api.qwenlm.com/v1",
            "model_name": "qwen3-7b-chat"
        },
        "openai": {
            "api_key": "",
            "api_base_url": "https://api.openai.com/v1",
            "model_name": "gpt-4o-mini"
        }
    }
    
    # Agent 专属 LLM 配置（预留，默认全部使用 default）
    agent_llm_mapping: Dict[str, str] = {
        "planner": "default",
        "researcher": "default",
        "reader": "default",
        "classification": "default",
        "gap": "default",
        "solution": "default",
        "experiment": "default",
        "writer": "default"
    }
    
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
