from abc import ABC, abstractmethod


class BaseAdapter(ABC):

    @abstractmethod
    def extract(self, source_path: str) -> dict:
        pass