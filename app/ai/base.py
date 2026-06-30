from abc import ABC
from abc import abstractmethod


class AIClient(ABC):
    """
    Abstract AI client interface.
    """

    @abstractmethod
    def generate_post(
        self,
        prompt: str,
        system_prompt: str,
    ) -> dict:
        raise NotImplementedError