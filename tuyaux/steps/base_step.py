from abc import ABC, abstractmethod
from typing import Optional, Generic, ParamSpec, TypeVar
from enum import Flag, auto
from tuyaux.context import ContextT, InVar, OutVar


P = ParamSpec("P")
R = TypeVar("R")


class StatusEnum(Flag):
    UNKNOWN = auto()
    RUNNING = auto()
    COMPLETE = auto()
    SKIPPED = auto()
    CONDITION_FAILED = auto()
    ERROR = auto()
    OK = COMPLETE | SKIPPED
    KO = ERROR | CONDITION_FAILED


class BaseStep(ABC, Generic[ContextT]):
    NAME = "Base Step"
    STYLES: dict[StatusEnum, dict[str, str]] = {
        StatusEnum.UNKNOWN: {"shape": "box", "color": "black", "style": "rounded"},
        StatusEnum.RUNNING: {
            "shape": "box",
            "color": "blue",
            "style": "rounded",
        },
        StatusEnum.COMPLETE: {
            "shape": "box",
            "color": "green",
            "style": "rounded",
            "bgcolor": "lightgreen",
        },
        StatusEnum.SKIPPED: {"shape": "box", "color": "grey", "style": "rounded"},
        StatusEnum.ERROR: {"shape": "box", "color": "red", "style": "rounded"},
        StatusEnum.CONDITION_FAILED: {
            "shape": "box",
            "color": "orange",
            "style": "rounded",
        },
    }
    DEFAULT_STYLE: dict[str, str] = {}
    COMMENT = ""

    def __init__(self, name: Optional[str] = None, comment: str = "") -> None:
        super().__init__()
        self.name = name if name is not None else self.NAME
        self.comment = comment or self.COMMENT
        self._status = StatusEnum.UNKNOWN
        self._id = id(self)
        self._str_id = str(self._id)
        self.error: Optional[BaseException] = None

    @abstractmethod
    def run(self, ctx: ContextT):
        ...

    @property
    def id(self) -> int:
        return self._id

    @property
    def str_id(self) -> str:
        return self._str_id

    @property
    def status(self) -> StatusEnum:
        return self._status

    def unknown(self):
        self._status = StatusEnum.UNKNOWN

    def running(self):
        self._status = StatusEnum.RUNNING

    def completed(self):
        self._status = StatusEnum.COMPLETE

    def skipped(self):
        self._status = StatusEnum.SKIPPED

    def errored(self, err: BaseException):
        self._status = StatusEnum.ERROR
        self.error = err

    def style(self) -> dict[str, str]:
        return self.STYLES.get(self._status, self.DEFAULT_STYLE)

    def label(self) -> str:
        return (
            f"{self.__class__.__name__}: {self.name}"
            f"{'\n' if self.comment else ''}{self.comment}"
        )

    # TODO: adjust these methods depending on the usage (add recursive type checks?)
    # Do not hesitate to reimplate in your classes to avoid parsing the obj dict and
    # directly store your Input/Outputs in an object attribute

    def inputs(self) -> tuple[InVar, ...]:
        return tuple(
            value for value in self.__dict__.values() if isinstance(value, InVar)
        )

    def outputs(self) -> tuple[OutVar, ...]:
        return tuple(
            value for value in self.__dict__.values() if isinstance(value, OutVar)
        )
