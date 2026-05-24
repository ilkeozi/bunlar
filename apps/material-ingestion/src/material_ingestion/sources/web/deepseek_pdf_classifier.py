from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.request import Request, urlopen


@dataclass(slots=True)
class DeepseekPdfClassifier:
    api_key: str
    model: str = "deepseek-chat"
    timeout_seconds: int = 15
    base_url: str = "https://api.deepseek.com/v1/chat/completions"

    def is_likely_pdf(
        self,
        *,
        pdf_url: str,
        anchor_text: str,
        reason: str,
        source_page_url: str,
    ) -> bool:
        prompt = (
            "You are a strict classifier. Decide if a URL is likely a downloadable technical PDF document "
            "(datasheet/specification/SDS/TDS). Return JSON only: {\"likely_pdf\": true|false}.\n"
            f"pdf_url: {pdf_url}\n"
            f"anchor_text: {anchor_text}\n"
            f"reason: {reason}\n"
            f"source_page_url: {source_page_url}\n"
        )

        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
        }

        req = Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(req, timeout=self.timeout_seconds) as resp:  # noqa: S310
            body = resp.read().decode("utf-8", errors="ignore")

        parsed = json.loads(body)
        content = parsed["choices"][0]["message"]["content"]
        result = json.loads(content)
        return bool(result.get("likely_pdf", False))
