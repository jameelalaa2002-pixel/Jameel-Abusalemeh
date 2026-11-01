# Pharmacy Assistant Chatbot

A small Arabic chatbot for a local area. It answers three kinds of questions:

- **Medicine availability:** which pharmacies have it in stock, price, open/closed now.
- **Pharmacies:** which are open now, 24-hour ones, address and phone.
- **Doctors:** who works today / tomorrow / on a given day, clinic and phone.

> **Important:** every name, address, phone number, price and schedule in `data/` is
> **invented sample data**. Replace it with real data before anyone relies on it.
> Medicine availability changes constantly, so the bot always tells users to call first.

## Safety design

The bot only reports data from the JSON files. It deliberately does **not**:

- recommend a medicine for a symptom, or discuss doses, interactions, pregnancy or side effects
  (it redirects to the pharmacist or doctor);
- handle emergencies (it points to 911 and nothing else).

These rules are covered by tests in `tests/test_bot.py`.

## Run

No dependencies, Python 3.10+.

```bash
python app.py                      # interactive chat in the terminal
python app.py "هل بانادول متوفر؟"
python web.py                      # web UI at http://localhost:8000
python -m unittest discover -s tests
```

## Your own data

Edit the JSON files in `data/`:

| File | Content |
|---|---|
| `pharmacies.json` | name, address, phone, opening hours, `is_24h` |
| `medicines.json` | medicine names and aliases (Arabic/English), `rx` = needs prescription |
| `stock.json` | quantity and price per pharmacy, plus the `updated` date |
| `doctors.json` | specialty, keywords, clinic, phone, working days and hours |

To add a medicine: add it to `medicines.json`, then give each pharmacy a `stock` entry.

## How it works

`bot/engine.py` is a rule-based router: emergency, medical-advice refusal, doctors, medicines,
pharmacies, help. Arabic text is normalised (hamza, ya/alef maqsura, ta marbuta, diacritics, digits)
and medicine names are matched by alias, with a fuzzy fallback for typos.

## Ideas to extend

- Let pharmacies update their own stock (a small admin page or a spreadsheet import).
- Add a map link per pharmacy, and distance from the user's location.
- Replace the rule router with an LLM that only calls these functions as tools.
- Add booking requests for doctors.

## AI-use disclosure

This project was written with the assistance of Claude (Anthropic): structure, code, sample data
and tests. The author is responsible for reviewing and running it.

<!-- Author: edit this section to say what you reviewed, changed and added yourself. -->
