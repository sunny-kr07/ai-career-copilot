import time

from langchain.chat_models import init_chat_model

from core import config

# Seconds to wait before each retry. 4 attempts in total, about 17 s of waiting at most.
RETRY_DELAYS = (2, 5, 10)


def get_llm(temperature: float = 0.0, timeout: int = 90, **kwargs):
    if config.THINKING_LEVEL and "thinking_level" not in kwargs:
        kwargs["thinking_level"] = config.THINKING_LEVEL
    return init_chat_model(
        model=config.MODEL,
        model_provider=config.PROVIDER,
        temperature=temperature,
        timeout=timeout,
        max_retries=0,
        **kwargs,
    )


def as_text(msg) -> str:
    """Normalize content whether it's a string or a list of blocks."""
    c = msg.content
    if isinstance(c, str):
        return c
    parts = []
    for b in c:
        if isinstance(b, dict):
            if b.get("type") in ("thinking", "reasoning"):
                continue
            parts.append(b.get("text", ""))
        else:
            parts.append(str(b))
    return "".join(parts)


def invoke_with_retry(llm, messages, delays=RETRY_DELAYS):
    """llm.invoke with backoff, for transient API errors (500, 503, timeouts)."""
    last_error = None
    for attempt in range(len(delays) + 1):
        try:
            return llm.invoke(messages)
        except Exception as e:
            last_error = e
            if attempt < len(delays):
                time.sleep(delays[attempt])
    raise last_error


if __name__ == "__main__":
    print(as_text(get_llm().invoke("Say hello in one word.")))