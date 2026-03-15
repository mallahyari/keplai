from keplai.graph import KeplAI

_instance: KeplAI | None = None


def set_graph(graph: KeplAI) -> None:
    global _instance
    _instance = graph


def get_graph() -> KeplAI:
    if _instance is None:
        raise RuntimeError("KeplAI engine has not been started yet.")
    return _instance
