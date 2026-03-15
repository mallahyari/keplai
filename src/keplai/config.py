from pydantic_settings import BaseSettings


class KeplAISettings(BaseSettings):
    model_config = {"env_prefix": "KEPLAI_"}

    # Fuseki / Docker
    fuseki_image: str = "stain/jena-fuseki"
    fuseki_port: int = 3030
    fuseki_dataset: str = "keplai"
    fuseki_container_name: str = "keplai-fuseki"
    fuseki_admin_password: str = "keplai-admin"

    # Namespaces
    entity_namespace: str = "http://keplai.io/entity/"
    ontology_namespace: str = "http://keplai.io/ontology/"

    # Reasoner
    reasoner: str = "OWL"

    # AI / LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    # Entity Disambiguation
    disambiguation_threshold: float = 0.90

    # Qdrant
    qdrant_path: str | None = None  # None = in-memory
