from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable

class BaseTool(ABC):
    """
    Base class for all tools.
    Can be subclassed to create custom tools, or instantiated directly with name, description, and run_func.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        run_func: Optional[Callable[..., Any]] = None,
    ):
        if name:
            self._name = name
        if description:
            self._description = description
        if run_func:
            self._run_func = run_func

    @property
    def name(self) -> str:
        return getattr(self, "_name", "UnnamedTool")

    @property
    def description(self) -> str:
        return getattr(self, "_description", "")

    async def run(self, *args, **kwargs) -> Any:
        run_func = getattr(self, "_run_func", None)
        if run_func:
            return await run_func(*args, **kwargs)
        else:
            raise NotImplementedError("Subclasses must implement run()")

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "description": self.description
        }
