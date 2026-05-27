from abc import ABC, abstractmethod


class SchoolAnalyzer(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def analyze(self, mcp_json: dict) -> dict:
        pass
