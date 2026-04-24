import logging
import time
from openai import OpenAI


logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, api_key: str, api_base: str, model: str, temperature: float, max_output_tokens: int):
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base,
        )

    def call(self, text_chunk: str, title: str, chunk_idx: int, total_chunks: int) -> str | None:
        osa_info = f"(Osa {chunk_idx}/{total_chunks})" if total_chunks > 1 else ""

        system_prompt = """
Olet tekninen analyytikko ja dokumentoija.
Analysoi annettu keskustelu ja palauta vastaus TÄSMÄLLEEN näillä otsikoilla:

### [OSIO_1_YHTEENVETO]
Tiivis mutta informatiivinen Markdown-yhteenveto. Kuvaa ongelma, ratkaisu ja tärkeät huomiot.

### [OSIO_2_KOODI]
Poimi vain relevantit ja käyttökelpoisimmat koodit, komennot ja konfiguraatiot.
Jos koodia ei ole, kirjoita: Ei koodia.

### [OSIO_3_KNOWLEDGE]
Kirjoita selkeä Knowledge Base -artikkeli Markdown-muodossa.
Jos sisältö ei sovellu KB-artikkeliksi, kirjoita: Ei KB-materiaalia.
""".strip()

        user_prompt = f"Keskustelun otsikko: {title} {osa_info}\n\n{text_chunk}"

        for attempt in range(1, 4):
            try:
                logger.info("Kutsutaan mallia %s %s", self.model, osa_info)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_output_tokens,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning("LLM-kutsu epäonnistui, yritys %s/3: %s", attempt, e)
                time.sleep(2 * attempt)

        return None