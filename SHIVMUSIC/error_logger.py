"""Central Telegram error reporting for every bot client in this project.

The reporter is deliberately kept independent from the application's logger so
that a failure while sending an error report cannot create an error-reporting
loop.
"""

import asyncio
import contextvars
import html
import inspect
import logging
import sys
import threading
import traceback
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Optional

import config
from pyrogram import Client


MAX_TELEGRAM_MESSAGE_LENGTH = 3900
ERROR_LEVEL = logging.ERROR
_current_client: contextvars.ContextVar[Any] = contextvars.ContextVar(
    "shivmusic_error_client", default=None
)
_reporting_error: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "shivmusic_reporting_error", default=False
)
_main_client: Any = None
_logging_handler_installed = False
_global_hooks_installed = False
_loop_handlers: set[int] = set()


def _safe_text(value: Any, limit: int = 600) -> str:
    """Convert arbitrary values into bounded, Telegram-safe text."""
    try:
        text = str(value)
    except Exception:
        text = "<unprintable>"
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    return text


def _escape(value: Any, limit: int = 600) -> str:
    return html.escape(_safe_text(value, limit), quote=True)


def _client_label(client: Any) -> str:
    """Return a useful bot/account label without making network calls."""
    if client is None:
        return "Unknown client"

    label = getattr(client, "error_logger_name", None)
    me = getattr(client, "me", None)
    bot_id = getattr(client, "id", None) or getattr(me, "id", None)
    username = getattr(client, "username", None) or getattr(me, "username", None)
    name = getattr(client, "name", None) or getattr(me, "first_name", None)

    parts = []
    if label:
        parts.append(_safe_text(label, 120))
    if name:
        parts.append(_safe_text(name, 120))
    if username:
        parts.append("@" + _safe_text(username.lstrip("@"), 120))
    if bot_id:
        parts.append(f"ID: {bot_id}")
    return " | ".join(dict.fromkeys(parts)) or client.__class__.__name__


def _source_details(callback: Any = None) -> str:
    if callback is None:
        return "Unavailable"

    try:
        file_name = inspect.getsourcefile(callback) or inspect.getfile(callback)
        line_number = inspect.getsourcelines(callback)[1]
        return f"{file_name}:{line_number}"
    except (OSError, TypeError, IOError):
        return _safe_text(callback, 300)


def _update_details(update: Any) -> str:
    if update is None:
        return "No update context"

    details = [type(update).__name__]
    for attribute, title in (
        ("id", "Update ID"),
        ("message_id", "Message ID"),
        ("chat", "Chat"),
        ("from_user", "User"),
    ):
        try:
            value = getattr(update, attribute, None)
            if attribute == "chat" and value is not None:
                value = getattr(value, "id", value)
            elif attribute == "from_user" and value is not None:
                value = getattr(value, "id", value)
            if value is not None:
                details.append(f"{title}: {_safe_text(value, 180)}")
        except Exception:
            continue

    for attribute in ("text", "caption", "data"):
        try:
            value = getattr(update, attribute, None)
            if value:
                details.append(f"{attribute.title()}: {_safe_text(value, 400)}")
                break
        except Exception:
            continue
    return " | ".join(details)


def _exception_traceback(exception: BaseException) -> str:
    try:
        return "".join(
            traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
        ).strip()
    except Exception:
        return f"{type(exception).__name__}: {_safe_text(exception)}"


def _chunks(text: str, size: int = MAX_TELEGRAM_MESSAGE_LENGTH):
    if not text:
        yield "Unknown error"
        return
    for start in range(0, len(text), size):
        yield text[start : start + size]


async def report_exception(
    client: Any,
    exception: BaseException,
    *,
    context: str = "Unhandled exception",
    callback: Any = None,
    update: Any = None,
) -> None:
    """Send one professionally formatted exception report to the error group."""
    target = client or _current_client.get() or _main_client
    if target is None:
        return

    logger_id = getattr(config, "ERROR_LOGGER_ID", -1004392214389)
    if not logger_id:
        return

    # Avoid recursively reporting a failure caused by the logger itself.
    if _reporting_error.get():
        return
    report_token = _reporting_error.set(True)

    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        trace = _exception_traceback(exception)
        header = (
            "🚨 <b>SHIVMUSIC ERROR ALERT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Time:</b> <code>{_escape(timestamp)}</code>\n"
            f"<b>Bot / account:</b> <code>{_escape(_client_label(target), 500)}</code>\n"
            f"<b>Context:</b> <code>{_escape(context, 500)}</code>\n"
            f"<b>Source:</b> <code>{_escape(_source_details(callback), 500)}</code>\n"
            f"<b>Update:</b> <code>{_escape(_update_details(update), 800)}</code>\n"
            f"<b>Error:</b> <code>{_escape(type(exception).__name__, 180)}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<b>Traceback:</b>\n<pre>"
        )
        footer = "</pre>"

        # Telegram has a 4096-character limit. Split only the traceback body
        # so every individual message remains valid HTML.
        escaped_trace = html.escape(trace, quote=True)
        body_size = max(500, MAX_TELEGRAM_MESSAGE_LENGTH - len(header) - len(footer) - 80)
        trace_parts = list(_chunks(escaped_trace, body_size))
        messages = []
        for index, part in enumerate(trace_parts, 1):
            part_marker = (
                f"\n\n<i>Traceback part {index}/{len(trace_parts)}</i>"
                if len(trace_parts) > 1
                else ""
            )
            messages.append(header + part + footer + part_marker)

        for message in messages:
            try:
                await target.send_message(
                    chat_id=logger_id,
                    text=message,
                    parse_mode="html",
                    disable_web_page_preview=True,
                )
            except Exception as send_error:
                # Never use LOGGER.error here: the logging bridge would call
                # this function again. stderr is the safe last-resort path.
                print(
                    "SHIVMUSIC error logger could not send report: "
                    f"{type(send_error).__name__}: {send_error}",
                    file=sys.stderr,
                )
                break
    finally:
        _reporting_error.reset(report_token)


async def _report_log_record(client: Any, record: logging.LogRecord) -> None:
    if getattr(record, "_shivmusic_error_report", False):
        return

    if record.exc_info and record.exc_info[1] is not None:
        exception = record.exc_info[1]
    else:
        exception = RuntimeError(record.getMessage())

    await report_exception(
        client,
        exception,
        context=f"Python logger: {record.name}",
    )


def _schedule(coroutine: Any) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    if loop.is_running():
        loop.create_task(coroutine)


class TelegramErrorLogHandler(logging.Handler):
    """Forward ERROR/CRITICAL log records to the configured Telegram group."""

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno < ERROR_LEVEL:
            return
        client = _current_client.get() or _main_client
        if client is not None:
            _schedule(_report_log_record(client, record))


def install_logging_handler() -> None:
    global _logging_handler_installed
    if _logging_handler_installed:
        return

    root = logging.getLogger()
    root.addHandler(TelegramErrorLogHandler())
    _logging_handler_installed = True


def install_global_error_hooks() -> None:
    """Install asyncio, process, and thread fallbacks once per process."""
    global _global_hooks_installed
    if _global_hooks_installed:
        return
    _global_hooks_installed = True

    original_excepthook = sys.excepthook

    def process_exception_hook(
        exception_type: type, exception: BaseException, exception_traceback: Any
    ) -> None:
        client = _current_client.get() or _main_client
        if client is not None:
            _schedule(
                report_exception(
                    client,
                    exception,
                    context="Process-level uncaught exception",
                )
            )
        original_excepthook(exception_type, exception, exception_traceback)

    sys.excepthook = process_exception_hook

    if hasattr(threading, "excepthook"):
        original_thread_hook = threading.excepthook

        def thread_exception_hook(args: Any) -> None:
            client = _current_client.get() or _main_client
            if client is not None:
                _schedule(
                    report_exception(
                        client,
                        args.exc_value,
                        context=f"Thread-level uncaught exception: {args.thread.name}",
                    )
                )
            original_thread_hook(args)

        threading.excepthook = thread_exception_hook


def install_asyncio_exception_handler(loop: Optional[asyncio.AbstractEventLoop] = None):
    loop = loop or asyncio.get_running_loop()
    if id(loop) in _loop_handlers:
        return
    _loop_handlers.add(id(loop))
    previous_handler = loop.get_exception_handler()

    def exception_handler(active_loop: asyncio.AbstractEventLoop, context: dict):
        exception = context.get("exception")
        if exception is None:
            exception = RuntimeError(context.get("message", "Unhandled asyncio exception"))
        client = context.get("client") or _current_client.get() or _main_client
        if client is not None:
            _schedule(
                report_exception(
                    client,
                    exception,
                    context="Asyncio background task",
                )
            )
        if previous_handler:
            previous_handler(active_loop, context)
        else:
            active_loop.default_exception_handler(context)

    loop.set_exception_handler(exception_handler)


def register_error_client(client: Any, label: Optional[str] = None) -> None:
    """Register a Telegram client and activate all process-level fallbacks."""
    global _main_client
    if label:
        client.error_logger_name = label
    if _main_client is None:
        _main_client = client
    install_logging_handler()
    install_global_error_hooks()
    try:
        install_asyncio_exception_handler()
    except RuntimeError:
        pass


def guard_handler(handler: Any) -> Any:
    """Wrap a Pyrogram handler callback so no update exception is lost."""
    callback = getattr(handler, "callback", None)
    if callback is None or getattr(callback, "_shivmusic_error_guard", False):
        return handler

    @wraps(callback)
    async def guarded_callback(client: Any, update: Any, *args: Any, **kwargs: Any):
        token = _current_client.set(client)
        try:
            result = callback(client, update, *args, **kwargs)
            if inspect.isawaitable(result):
                return await result
            return result
        except asyncio.CancelledError:
            raise
        except Exception as exception:
            await report_exception(
                client,
                exception,
                context="Pyrogram update handler",
                callback=callback,
                update=update,
            )
            return None
        finally:
            _current_client.reset(token)

    guarded_callback._shivmusic_error_guard = True
    handler.callback = guarded_callback
    return handler


class ErrorLoggingClient(Client):
    """Pyrogram client that reports handler failures with bot identity."""

    def __init__(self, *args: Any, error_logger_name: Optional[str] = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        if error_logger_name:
            self.error_logger_name = error_logger_name

    def add_handler(self, handler: Any, group: int = 0):
        return super().add_handler(guard_handler(handler), group)

    async def start(self, *args: Any, **kwargs: Any):
        result = await super().start(*args, **kwargs)
        register_error_client(self, getattr(self, "error_logger_name", None))
        return result