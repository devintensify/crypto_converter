"""Auxiliary logging utilities."""

import logging
from collections.abc import Awaitable, Callable
from typing import Any, Concatenate, Literal, ParamSpec, TypeVar

_T = TypeVar("_T")  # self / instance
_P = ParamSpec("_P")  # args type
_R = TypeVar("_R")  # return type

_LogLevel = Literal["debug", "info", "warning", "error", "critical", "exception"]
"""Log level."""


_AsyncMethodType = Callable[Concatenate[_T, _P], Awaitable[_R]]
"""Type alias for asynchronous instance method."""


def log_awaitable_method(
    logger_name: str,
    *,
    level_on_attempt: _LogLevel = "debug",
    level_on_error: _LogLevel = "error",
    use_class_repr: bool = False,
) -> Any:
    """Get logging decorator for asynchronous instance method.

    Args:
        logger_name (`str`): name of logger.
        level_on_attempt (`_LogLevel`): log level for call attempt logging. \
            Default value: `debug`.
        level_on_error (`_LogLevel`): log level for call attempt fail. \
            Default value: `error`.
        use_class_repr (`bool`): Flag allowing to use `__repr__` method in logs \
            instead of class name. \
            Default value: `False.

    Returns:
        `Callable[[_AsyncMethodType],_AsyncMethodType]`: \
            Wrapper for asynchronous class instance bound method.

    """

    def _log_awaitable_method(
        method: _AsyncMethodType[_T, _P, _R],
    ) -> _AsyncMethodType[_T, _P, _R]:
        logger = logging.getLogger(logger_name)

        async def _method_wrapper(self: _T, *args: _P.args, **kwargs: _P.kwargs) -> _R:
            method_name = method.__name__
            object_repr = self.__class__.__name__ if not use_class_repr else repr(self)
            method_repr = f"`{method_name}` method of `{object_repr}`"

            attempt_logger = getattr(logger, level_on_attempt)
            attempt_logger("Calling %s..", method_repr)
            try:
                result = await method(self, *args, **kwargs)
                attempt_logger("%s: succeeded", method_repr)
            except Exception as exc:
                error_logger = getattr(logger, level_on_error)
                error_logger("%s: failed with error: `%s`", method_repr, str(exc))
                raise
            else:
                return result

        return _method_wrapper

    return _log_awaitable_method
