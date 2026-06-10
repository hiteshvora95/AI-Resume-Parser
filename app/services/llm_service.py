import asyncio
from typing import Optional

import tiktoken
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from openai import APIConnectionError, APITimeoutError, AuthenticationError, InternalServerError, RateLimitError

from app.core.logger import get_logger
from app.models import ResumeExtraction
from app.services.prompts import RESUME_EXTRACTION_PROMPT
from config.variables import OPENAI_API_KEY, OPENAI_MODEL

logger = get_logger(__name__)


MAX_RETRIES = 3
BASE_RETRY_DELAY = 2
MAX_TOKENS = 12000
REQUEST_TIMEOUT = 60


class LLMClient:
    """LLM client for structured resume extraction using LangChain and OpenAI."""

    def __init__(self) -> None:
        self._llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0,
            timeout=REQUEST_TIMEOUT,
            max_retries=0,
        )
        self._encoding = tiktoken.encoding_for_model(OPENAI_MODEL)

    def _truncate_to_token_limit(self, text: str) -> str:
        """Truncate text to MAX_TOKENS if it exceeds the token limit."""
        tokens = self._encoding.encode(text)
        if len(tokens) > MAX_TOKENS:
            logger.warning(f"Resume text truncated: {len(tokens)} → {MAX_TOKENS} tokens")
            return self._encoding.decode(tokens[:MAX_TOKENS])
        logger.info(f"Resume token count: {len(tokens)}")
        return text

    async def _call(self, resume_text: str) -> ResumeExtraction:
        """Send resume text to the LLM and return structured output."""
        chain = self._llm.with_structured_output(ResumeExtraction)
        result = await chain.ainvoke([
            SystemMessage(content=RESUME_EXTRACTION_PROMPT),
            HumanMessage(content=f"Extract information from this resume:\n\n{resume_text}"),
        ])
        logger.info("LLM response received")
        return result

    async def _call_with_retry(self, resume_text: str) -> ResumeExtraction:
        """Retry the LLM call on timeout and server errors with exponential backoff."""
        last_error: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return await self._call(resume_text)

            except (APITimeoutError, InternalServerError) as e:
                last_error = e
                wait = BASE_RETRY_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    f"LLM transient error on attempt {attempt}/{MAX_RETRIES} — "
                    f"retrying in {wait}s — Error: {e}"
                )
                await asyncio.sleep(wait)

        logger.error(f"LLM failed after {MAX_RETRIES} attempts: {last_error}")
        raise TimeoutError(f"LLM service failed after {MAX_RETRIES} retries — please try again")

    async def parse_resume(self, resume_text: str) -> ResumeExtraction:
        """Truncate to token limit if needed, call the LLM with retry, and return structured resume data."""
        resume_text = self._truncate_to_token_limit(resume_text)
        logger.info(f"Calling LLM — model={OPENAI_MODEL}")

        try:
            return await self._call_with_retry(resume_text)

        except RateLimitError:
            logger.warning("LLM rate limit hit — propagating to caller")
            raise

        except AuthenticationError:
            logger.error("LLM authentication failed — invalid API key")
            raise ValueError("Invalid API key provided for LLM service")

        except APIConnectionError:
            logger.error("Cannot reach LLM API")
            raise ConnectionError("LLM service is currently unreachable")

        except OutputParserException as e:
            logger.error(f"LangChain failed to parse LLM output: {e}")
            raise RuntimeError("Failed to parse resume — unexpected LLM response format")


llm_client = LLMClient()
