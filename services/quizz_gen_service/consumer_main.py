import asyncio
import signal
from .generator_consumer import run_consumer


async def main() -> None:
    stop_event = asyncio.Event()

    def _handler(*_: object) -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handler)
        except NotImplementedError:
            # Windows fallback: ignore signal handlers
            pass

    await run_consumer(stop_event)


if __name__ == "__main__":
    asyncio.run(main())
