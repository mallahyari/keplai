from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class KeplAISettings(BaseSettings):
    model_config = {"env_prefix": "KEPLAI_", "populate_by_name": True}

    # Fuseki / Docker
    fuseki_image: str = "stain/jena-fuseki"
    fuseki_port: int = 3030
    fuseki_dataset: str = "keplai"
    fuseki_container_name: str = "keplai-fuseki"
    fuseki_admin_password: str = "keplai-admin"

    # Namespaces
    entity_namespace: str = "http://keplai.io/entity/"
    ontology_namespace: str = "http://keplai.io/ontology/"

    # Named graphs
    metadata_graph: str = "http://keplai.io/graph/metadata"
    data_graph: str = "http://keplai.io/graph/data"
    graph_base_uri: str = "http://keplai.io/graph/"

    # Reasoner
    reasoner: str = "OWL"

    # AI / LLM — reads OPENAI_API_KEY (no KEPLAI_ prefix)
    openai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("OPENAI_API_KEY", "KEPLAI_OPENAI_API_KEY"),
    )
    openai_model: str = Field(
        default="gpt-4o",
        validation_alias=AliasChoices("OPENAI_MODEL", "KEPLAI_OPENAI_MODEL"),
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        validation_alias=AliasChoices("EMBEDDING_MODEL", "KEPLAI_EMBEDDING_MODEL"),
    )
    embedding_dim: int = 1536

    # Entity Disambiguation
    disambiguation_threshold: float = Field(
        default=0.90,
        validation_alias=AliasChoices("DISAMBIGUATION_THRESHOLD", "KEPLAI_DISAMBIGUATION_THRESHOLD"),
    )

    # Qdrant
    qdrant_path: str | None = None  # None = in-memory
