# Open WebUI Export Parser

Production-tyylinen työkalu Open WebUI -vientien käsittelyyn LiteLLM-proxyn kautta.

## Ominaisuudet

- Lukee `input/`-kansiosta JSON-viennit
- Tukee `messages` ja `chat.messages` -rakenteita
- Suodattaa todennäköiset base64-liitteet
- Pilkkoo pitkät keskustelut viestirajoja kunnioittaen
- Lähettää chunkit LiteLLM-proxylle
- Tallentaa:
  - yhteenvedot
  - koodit
  - knowledge base -sisällön
  - metadata-tiedot
  - raw-vastaukset
  - virhelokit

## Asennus

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt