"""
CareerCompass AI - IBM watsonx.ai Integration Module
Handles all communication with the configured foundation model
(currently meta-llama/llama-3-3-70b-instruct via IBM watsonx.ai).
"""

import logging
import json
from config import ActiveConfig
from utils import safe_json_parse

logger = logging.getLogger(__name__)

# Lazy-loaded client singleton
_watsonx_client = None


def _get_client():
    """
    Return the ibm_watsonx_ai ModelInference client, creating it on first call.
    Raises RuntimeError if credentials are missing.
    """
    global _watsonx_client
    if _watsonx_client is not None:
        return _watsonx_client

    try:
        from ibm_watsonx_ai import Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

        missing = ActiveConfig.validate()
        if missing:
            raise RuntimeError(
                f"Missing required watsonx configuration: {', '.join(missing)}. "
                "Please set these environment variables in your .env file."
            )

        credentials = Credentials(
            url=ActiveConfig.WATSONX_URL,
            api_key=ActiveConfig.WATSONX_API_KEY,
        )

        params = {
            GenParams.MAX_NEW_TOKENS: ActiveConfig.MAX_TOKENS,
            GenParams.TEMPERATURE: ActiveConfig.TEMPERATURE,
            GenParams.TOP_P: ActiveConfig.TOP_P,
            GenParams.REPETITION_PENALTY: ActiveConfig.REPETITION_PENALTY,
        }
        # TOP_K is not supported by all models on watsonx (e.g. Llama-3 family).
        # Only add it when explicitly set to a value other than the default 50.
        if ActiveConfig.TOP_K and ActiveConfig.TOP_K != 50:
            params[GenParams.TOP_K] = ActiveConfig.TOP_K

        _watsonx_client = ModelInference(
            model_id=ActiveConfig.GRANITE_MODEL_ID,
            credentials=credentials,
            project_id=ActiveConfig.WATSONX_PROJECT_ID,
            params=params,
        )

        logger.info(
            "IBM watsonx.ai client initialized. Model: %s", ActiveConfig.GRANITE_MODEL_ID
        )
        logger.info("Generation params: temp=%.2f, max_tokens=%d, top_p=%.2f",
                    ActiveConfig.TEMPERATURE, ActiveConfig.MAX_TOKENS, ActiveConfig.TOP_P)
        return _watsonx_client

    except ImportError as exc:
        logger.error("ibm-watsonx-ai SDK not installed: %s", exc)
        raise RuntimeError("IBM watsonx.ai SDK is not installed. Run: pip install ibm-watsonx-ai") from exc
    except Exception as exc:
        logger.error("Failed to initialize watsonx client: %s", exc)
        raise


def generate_text(prompt: str) -> str:
    """
    Send a prompt to the model and return the raw text response.

    Uses generate_text() which maps to the text-generation endpoint.
    The watsonx SDK handles authentication and retries.
    """
    client = _get_client()
    try:
        logger.debug("Sending prompt to model (length=%d chars)", len(prompt))
        response = client.generate_text(prompt=prompt)
        if not isinstance(response, str):
            # Some SDK versions return a dict — extract the text
            response = (
                response.get("results", [{}])[0].get("generated_text", "")
                if isinstance(response, dict)
                else str(response)
            )
        logger.debug("Received response (length=%d chars)", len(response))
        return response
    except Exception as exc:
        logger.error("Error generating text from watsonx: %s", exc)
        raise


def generate_json(prompt: str) -> dict:
    """
    Send a prompt to the Granite model, parse the response as JSON.
    Returns parsed dict or raises ValueError on parse failure.
    """
    raw = generate_text(prompt)
    parsed = safe_json_parse(raw)
    if parsed is None:
        logger.error("Model returned non-JSON response (first 800 chars): %s", raw[:800])
        raise ValueError(
            "The AI model returned an unexpected response format. "
            "This can happen with large JSON schemas — please try again."
        )
    return parsed


def health_check() -> dict:
    """
    Test the watsonx connection with a minimal prompt.
    Returns a status dict.
    """
    try:
        _get_client()
        test_prompt = 'Return only: {"status": "ok"}'
        raw = generate_text(test_prompt)
        parsed = safe_json_parse(raw)
        return {
            "status": "connected",
            "model": ActiveConfig.GRANITE_MODEL_ID,
            "response_valid": parsed is not None,
        }
    except RuntimeError as exc:
        return {"status": "misconfigured", "error": str(exc)}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def reset_client():
    """Reset the client singleton (useful for testing / re-initialization)."""
    global _watsonx_client
    _watsonx_client = None
