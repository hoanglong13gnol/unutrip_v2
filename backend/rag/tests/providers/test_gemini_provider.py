from unittest.mock import MagicMock

from providers.gemini_provider import GeminiProvider


def test_gemini_provider_without_inner() -> None:
    out = GeminiProvider(None).generate("hello")
    assert out["ok"] is False
    assert out["error_type"] == "gemini_not_available"


def test_gemini_provider_delegates() -> None:
    inner = MagicMock()
    inner.generate.return_value = {"ok": True, "answer": "x"}
    out = GeminiProvider(inner).generate("p")
    assert out["answer"] == "x"
    inner.generate.assert_called_once_with("p")
