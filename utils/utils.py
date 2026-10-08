import logging
import os
from typing import Dict

import structlog
from dotenv import load_dotenv
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Load environment variables from a .env file
load_dotenv()


# Configure the standard Python logger to use RichHandler for colored output
custom_theme = Theme(
    {
        "info": "green",
        "warning": "yellow",
        "error": "bold red",
        "debug": "cyan",
    }
)

# Rich console used for manual prints from agents
CONSOLE = Console(theme=custom_theme)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[
        RichHandler(
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            markup=True,
            show_time=True,
            log_time_format="%H:%M:%S",
            show_level=True,
            show_path=True,
            enable_link_path=True,
            console=CONSOLE,
        )
    ],
)


# Configure structlog for structured logging
structlog.configure(
    processors=[
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.KeyValueRenderer(key_order=["event"]),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


def create_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Create and return a structured logger with the specified name.

    Args:
        name (str): The name of the logger.

    Returns:
        structlog.stdlib.BoundLogger: The configured structured logger.
    """
    return structlog.get_logger(name)


# Shared resilience policy for LLM calls: exponential backoff + jitter on
# transient errors (rate limits, 5xx). Applied via apply_retry() as the
# OUTERMOST layer so it does not hide model methods like with_structured_output.
_LLM_RETRY_KWARGS = dict(stop_after_attempt=5, wait_exponential_jitter=True)


def get_llm_instance(t: float = 0.0) -> ChatGoogleGenerativeAI:
    """
    Configure and return the base chat model.

    Returns the raw ``ChatGoogleGenerativeAI`` (not a retry wrapper) so callers
    can still use ``with_structured_output()`` or pass it to ``create_agent()``.
    Wrap the final runnable with :func:`apply_retry` to add resilience.

    Args:
        t (float, optional): Temperature setting for the model. Defaults to 0.0.

    Returns:
        ChatGoogleGenerativeAI: Configured base LLM instance.
    """
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=t,
        google_api_key=google_api_key,
    )


def apply_retry(runnable: Runnable) -> Runnable:
    """
    Wrap a runnable with exponential backoff + jitter on transient LLM errors.

    Must be applied as the OUTERMOST layer — i.e. AFTER ``with_structured_output()`` —
    otherwise the underlying model methods are no longer reachable.

    Args:
        runnable (Runnable): The runnable to make resilient (a chat model or a
            structured-output runnable).

    Returns:
        Runnable: The runnable wrapped with the shared retry policy.
    """
    return runnable.with_retry(**_LLM_RETRY_KWARGS)


if __name__ == "__main__":
    # Test logger
    logger = create_logger("test")
    logger.info("Logger initialized successfully")

    try:
        # Minimal test prompt, adjust as needed
        llm = get_llm_instance()
        resp = llm.invoke("ping")
        logger.info("LLM instance created and test call successful", response=resp)
    except Exception as e:

        logger.error("Failed to instantiate LLM or hit rate limit", error=str(e))
        raise RuntimeError("LLM instantiation failed or rate limit reached") from e
