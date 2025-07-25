"""Auxiliary logging utilities."""

import logging
from collections.abc import Callable, Coroutine
from typing import Any, Concatenate, Literal, ParamSpec, TypeVar

_T = TypeVar("_T")  # self / instance
_P = ParamSpec("_P")  # args type
_R = TypeVar("_R")  # return type

_LogLevel = Literal["debug", "info", "warning", "error", "critical", "exception"]
"""Log level."""


_AsyncMethodType = Callable[Concatenate[_T, _P], Coroutine[Any, Any, _R]]
"""Type alias for asynchronous instance method."""

_MethodType = Callable[Concatenate[_T, _P], _R]
"""Type alias for instance method."""


def log_awaitable_method(
    logger_name: str,
    *,
    level_on_attempt: _LogLevel = "debug",
    level_on_error: _LogLevel = "error",
    use_class_repr: bool = False,
    log_kwargs: list[str] | None = None,
) -> Callable[[_AsyncMethodType[_T, _P, _R]], _AsyncMethodType[_T, _P, _R]]:
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
        log_kwargs (`Optional[list[str]]`): list of named args to add to log.

    Returns:
        `Callable[[_AsyncMethodType],_AsyncMethodType]`: \
            Wrapper for asynchronous class instance bound method.

    """

    def _log_awaitable_method(
        method: _AsyncMethodType[_T, _P, _R],
    ) -> _AsyncMethodType[_T, _P, _R]:
        logger = logging.getLogger(logger_name)

        async def _method_wrapper(self: _T, *args: _P.args, **kwargs: _P.kwargs) -> _R:
            to_log_args, to_log_kwargs = _get_args_kwargs_to_log(
                args, kwargs, log_kwargs=log_kwargs
            )
            method_repr = _get_method_repr(method, to_log_args, to_log_kwargs)
            object_repr = self.__class__.__name__ if not use_class_repr else repr(self)
            method_repr = f"`{method_repr}` method of `{object_repr}`"

            attempt_logger = getattr(logger, level_on_attempt)
            attempt_logger("Calling %s..", method_repr)
            try:
                result = await method(self, *args, **kwargs)
                attempt_logger("%s: succeeded", method_repr)
            except Exception as exc:
                exc_repr = f"Type={type(exc)}, Args={exc.args}, Message={exc}"
                error_logger = getattr(logger, level_on_error)
                error_logger("%s: failed with error: `%s`", method_repr, exc_repr)
                raise
            else:
                return result

        return _method_wrapper

    return _log_awaitable_method


def log_method(
    logger_name: str,
    *,
    level_on_attempt: _LogLevel = "debug",
    level_on_error: _LogLevel = "error",
    use_class_repr: bool = False,
    log_kwargs: list[str] | None = None,
) -> Callable[[_MethodType[_T, _P, _R]], _MethodType[_T, _P, _R]]:
    """Get logging decorator for instance method.

    Args:
        logger_name (`str`): name of logger.
        level_on_attempt (`_LogLevel`): log level for call attempt logging. \
            Default value: `debug`.
        level_on_error (`_LogLevel`): log level for call attempt fail. \
            Default value: `error`.
        use_class_repr (`bool`): Flag allowing to use `__repr__` method in logs \
            instead of class name. \
            Default value: `False.
        log_kwargs (`Optional[list[str]]`): list of named args to add to log.

    Returns:
        `Callable[[_MethodType], _MethodType]`: \
            Wrapper for asynchronous class instance bound method.

    """

    def _log_method(method: _MethodType[_T, _P, _R]) -> _MethodType[_T, _P, _R]:
        logger = logging.getLogger(logger_name)

        def _method_wrapper(self: _T, *args: _P.args, **kwargs: _P.kwargs) -> _R:
            to_log_args, to_log_kwargs = _get_args_kwargs_to_log(
                args, kwargs, log_kwargs=log_kwargs
            )
            method_repr = _get_method_repr(method, to_log_args, to_log_kwargs)
            object_repr = self.__class__.__name__ if not use_class_repr else repr(self)
            method_repr = f"`{method_repr}` method of `{object_repr}`"

            attempt_logger = getattr(logger, level_on_attempt)
            attempt_logger("Calling %s..", method_repr)
            try:
                result = method(self, *args, **kwargs)
            except Exception as exc:
                exc_repr = f"Type={type(exc)}, Args={exc.args}, Message={exc}"
                error_logger = getattr(logger, level_on_error)
                error_logger("%s: failed with error: `%s`", method_repr, exc_repr)
                raise
            else:
                attempt_logger("%s: succeeded", method_repr)
                return result

        return _method_wrapper

    return _log_method


def _get_args_kwargs_to_log(
    args: Any, kwargs: Any, log_kwargs: list[str] | None = None
) -> tuple[list[Any], dict[str, Any]]:
    list_args = list(args) if args else []
    dict_kwargs = dict(kwargs) if kwargs else {}
    filtered_dict_kwargs = (
        dict_kwargs
        if log_kwargs is None
        else {name: value for name, value in dict_kwargs.items() if name in log_kwargs}
    )
    return list_args, filtered_dict_kwargs


def _get_method_repr(
    method: _MethodType | _AsyncMethodType,
    args: list[Any],
    kwargs: dict[str, Any],
) -> str:
    method_repr = method.__name__
    method_content = []
    if args:
        method_content.append(", ".join(list(map(str, args))))
    if kwargs:
        method_content.append(
            ", ".join([f"{name}={arg}" for name, arg in kwargs.items()])
        )
    if method_content:
        method_repr += "(" + ", ".join(method_content) + ")"

    return method_repr
