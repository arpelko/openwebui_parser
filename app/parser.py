import re
from app.models import ParsedSections


SECTION_PATTERN = re.compile(
    r"### \[OSIO_1_YHTEENVETO\](.*?)### \[OSIO_2_KOODI\](.*?)### \[OSIO_3_KNOWLEDGE\](.*)",
    re.DOTALL,
)


def parse_sections(llm_response: str | None) -> ParsedSections:
    if not llm_response:
        return ParsedSections()

    match = SECTION_PATTERN.search(llm_response)
    if not match:
        return ParsedSections(yhteenveto=llm_response.strip())

    return ParsedSections(
        yhteenveto=match.group(1).strip(),
        koodi=match.group(2).strip(),
        kb=match.group(3).strip(),
    )