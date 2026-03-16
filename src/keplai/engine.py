from __future__ import annotations

import logging
import time

import docker
import httpx
from docker.errors import NotFound, DockerException

from keplai.config import KeplAISettings
from keplai.exceptions import EngineError

logger = logging.getLogger(__name__)


class JenaEngine:
    """Manages the Apache Jena Fuseki Docker container lifecycle."""

    def __init__(self, settings: KeplAISettings | None = None) -> None:
        self.settings = settings or KeplAISettings()
        self._client: docker.DockerClient | None = None
        self._container = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Pull the Fuseki image (if needed), generate config, and start the container."""
        try:
            self._client = docker.from_env()
        except DockerException as exc:
            raise EngineError(
                "Cannot connect to Docker. Is Docker installed and running?"
            ) from exc

        # Pull image
        logger.info("Pulling Fuseki image %s …", self.settings.fuseki_image)
        try:
            self._client.images.pull(self.settings.fuseki_image)
        except DockerException as exc:
            raise EngineError(f"Failed to pull image {self.settings.fuseki_image}: {exc}") from exc

        # Reuse existing container if it exists
        try:
            existing = self._client.containers.get(self.settings.fuseki_container_name)
            if existing.status != "running":
                logger.info("Starting existing container %s", self.settings.fuseki_container_name)
                existing.start()
            self._container = existing
        except NotFound:
            self._container = self._create_container()

        self._wait_until_ready()
        logger.info("Fuseki is ready at %s", self.endpoint)

    def stop(self) -> None:
        """Stop the container (data persists via Docker volume)."""
        if self._container is not None:
            logger.info("Stopping Fuseki container …")
            self._container.stop()

    def is_healthy(self) -> bool:
        """Return True if Fuseki responds to a ping."""
        try:
            r = httpx.get(f"{self.endpoint}/$/ping", timeout=5)
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    @property
    def endpoint(self) -> str:
        return f"http://localhost:{self.settings.fuseki_port}"

    @property
    def dataset_url(self) -> str:
        return f"{self.endpoint}/{self.settings.fuseki_dataset}"

    @property
    def sparql_url(self) -> str:
        return f"{self.dataset_url}/sparql"

    @property
    def update_url(self) -> str:
        return f"{self.dataset_url}/update"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _create_container(self):
        """Create and start a new Fuseki container."""
        volume_name = f"{self.settings.fuseki_container_name}-data"

        logger.info("Creating Fuseki container %s on port %s …",
                     self.settings.fuseki_container_name, self.settings.fuseki_port)

        container = self._client.containers.run(
            self.settings.fuseki_image,
            detach=True,
            name=self.settings.fuseki_container_name,
            ports={"3030/tcp": self.settings.fuseki_port},
            volumes={
                volume_name: {"bind": "/fuseki", "mode": "rw"},
            },
            environment={
                "FUSEKI_DATASET_1": self.settings.fuseki_dataset,
                "ADMIN_PASSWORD": self.settings.fuseki_admin_password,
            },
        )
        return container

    def _wait_until_ready(self, timeout: int = 60, interval: float = 1.0) -> None:
        """Poll Fuseki until it responds or timeout is reached."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.is_healthy():
                return
            time.sleep(interval)
        raise EngineError(
            f"Fuseki did not become ready within {timeout}s at {self.endpoint}"
        )
