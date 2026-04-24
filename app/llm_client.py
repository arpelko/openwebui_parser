import logging
import time
from typing import Optional

from openai import OpenAI


logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(
        self,
        api_key: str,
        api_base: str,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ):
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base,
        )

    def call_stage1(
        self,
        text_chunk: str,
        title: str,
        chunk_idx: int,
        total_chunks: int,
    ) -> Optional[str]:
        """
        Stage 1:
        - analysoi yksi chunk
        - palauta 3 osiota:
          1) yhteenveto
          2) koodi
          3) knowledge
        """

        osa_info = f"(Osa {chunk_idx}/{total_chunks})" if total_chunks > 1 else ""

        system_prompt = """
Olet tekninen analyytikko ja dokumentoija.

Analysoi annettu keskustelun osa ja palauta vastaus TÄSMÄLLEEN näillä otsikoilla:

### [OSIO_1_YHTEENVETO]
Tiivis mutta informatiivinen Markdown-yhteenveto. Kuvaa ongelma, ratkaisu ja tärkeät huomiot.

### [OSIO_2_KOODI]
Poimi kaikki relevantit ja käyttökelpoiset koodit, komennot ja konfiguraatiot.
Jos koodia ei ole, kirjoita: Ei koodia.

### [OSIO_3_KNOWLEDGE]
Kirjoita tästä osasta mahdollisimman hyödyllinen Knowledge Base -luonnos Markdown-muodossa.
Jos sisältö ei sovellu KB-artikkeliksi, kirjoita: Ei KB-materiaalia.

Tärkeää:
- Älä hävitä olennaista teknistä tietoa.
- Mieluummin säilytä hieman liikaa kuin liian vähän.
- Säilytä konkreettiset komennot, konfiguraatiot, ratkaisuaskeleet ja koodiesimerkit.
- Jos samasta asiasta on useita yksityiskohtia, sisällytä ne mieluummin kuin tiivistä liikaa.
""".strip()

        user_prompt = f"Keskustelun otsikko: {title} {osa_info}\n\n{text_chunk}"

        for attempt in range(1, 4):
            try:
                logger.info(
                    "Stage1: kutsutaan mallia %s %s",
                    self.model,
                    osa_info,
                )

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
                logger.warning(
                    "Stage1 LLM-kutsu epäonnistui, yritys %s/3, malli=%s, chunk=%s/%s: %s",
                    attempt,
                    self.model,
                    chunk_idx,
                    total_chunks,
                    e,
                )
                time.sleep(2 * attempt)

        return None

    def call_stage2_consolidation(
        self,
        base_title: str,
        section_type: str,
        parts: list[str],
    ) -> Optional[str]:
        """
        Stage 2:
        - yhdistää saman keskustelun useat osat
        - poistaa päällekkäisyyksiä
        - tuottaa yhden final-version
        """

        section_instruction = self._section_instruction(section_type)

        system_prompt = f"""
Olet tekninen toimittaja ja dokumentaation yhtenäistäjä.

Saat useita saman aiheen osittaisia Markdown-versioita. Tehtäväsi on:
1. yhdistää ne yhdeksi lopulliseksi versioksi
2. poistaa päällekkäinen sisältö
3. säilyttää teknisesti hyödyllinen tieto
4. ratkaista ristiriidat järkevästi
5. tuottaa yksi selkeä lopputulos ilman viittauksia osiin

Lisäohje:
{section_instruction}

Palauta vain lopullinen Markdown-sisältö.
""".strip()

        formatted_parts = []
        for idx, content in enumerate(parts, start=1):
            formatted_parts.append(f"## Osa {idx}\n\n{content}")

        user_prompt = (
            f"# Aihe\n{base_title}\n\n# Yhdistettävät osat\n\n"
            + "\n\n---\n\n".join(formatted_parts)
        )

        for attempt in range(1, 4):
            try:
                logger.info(
                    "Stage2: kutsutaan mallia %s, osio=%s, osia=%s",
                    self.model,
                    section_type,
                    len(parts),
                )

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
                logger.warning(
                    "Stage2 konsolidointi epäonnistui, yritys %s/3, malli=%s, osio=%s: %s",
                    attempt,
                    self.model,
                    section_type,
                    e,
                )
                time.sleep(2 * attempt)

        return None

    def _section_instruction(self, section_type: str) -> str:
        if section_type == "yhteenveto":
            return (
                "Tee yksi tiivis mutta kattava yhteenveto. "
                "Poista toisteisuus. "
                "Säilytä tärkeimmät päätelmät, ratkaisut ja huomiot."
            )

        if section_type == "koodi":
            return (
                "Yhdistä relevantit ja toimivimmat koodit, komennot ja konfiguraatiot. "
                "Poista duplikaatit. "
                "Jos useita versioita samasta ratkaisusta esiintyy, "
                "suosi täydellisintä ja selkeintä versiota."
            )

        if section_type == "kb":
            return (
                "Kirjoita yksi yhtenäinen Knowledge Base -artikkeli. "
                "Poista toisteisuus, säilytä hyödylliset ohjeet ja rakenna sisältö loogisesti."
            )

        return "Yhdistä sisältö yhdeksi selkeäksi lopputulokseksi."