"""Custom exception hierarchy for KeplAI."""


class KeplAIError(Exception):
    """Base exception for all KeplAI errors."""


class EngineError(KeplAIError):
    """Raised when the graph engine (Fuseki/Docker) fails."""


class ExtractionError(KeplAIError):
    """Raised when AI triple extraction fails."""


class QueryError(KeplAIError):
    """Raised when a SPARQL or NL query fails."""


class DisambiguationError(KeplAIError):
    """Raised when entity disambiguation fails."""


class OntologyImportError(KeplAIError):
    """Raised when ontology file/URL import fails."""


class OntologyConflictError(KeplAIError):
    """Raised when a label matches properties/classes in multiple ontologies."""


class OntologyNotFoundError(KeplAIError):
    """Raised when a referenced ontology does not exist."""
