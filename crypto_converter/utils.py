"""Module with utilities to be used in entire project."""

import asyncio
from contextlib import suppress


async def cancel_and_wait(*tasks: asyncio.Task | None) -> None:
    """Cancel and wait shutdown of asyncio Task instances.

    Given a sequence of asyncio.Task instances or NoneType instances,
    identify running tasks, cancel each of them and wait them to shutdown.
    Propagate all exceptions that may occur in tasks.
    """
    running_tasks = [task for task in tasks if task is not None and not task.done()]
    if running_tasks:
        for running_task in running_tasks:
            running_task.cancel()
        with suppress(asyncio.CancelledError):
            await asyncio.gather(*running_tasks)
