# Car Market Dashboard

Tracks zero-km car prices in Iran (listings from Bama.ir) and compares each
model's price growth with the dollar (USDT/Toman from Wallex) and 18k gold
(from tgju.org). Prices are indexed to a base of 100 and the dashboard shows a
"buy opportunity" signal for each comparison.

## Structure

```
core/        shared helpers: DB path and connection, Tehran dates, IQR filter, logging
scrapers/    bama.py (car ads), gold.py, tether.py
dashboard/   app.py (Streamlit), ai_analysis.py (AI summary)
data/        bama.db (SQLite, not in Git)
run_all.py   runs the three scrapers in order
```

## Setup (Python 3.13)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Then edit `.env`:

- `DB_PATH` - path to the SQLite database (default `data/bama.db`)
- `OPENAI_API_KEY` - key used for the AI summary (through api.gapgpt.app)

The database is not in Git. Copy `bama.db` into `data/` manually. It holds the
history of scraped ads, so back it up.

## Run (always from the project root)

```
python run_all.py                # update all data
python -m scrapers.tether        # or scrapers.gold / scrapers.bama, one at a time
streamlit run dashboard/app.py   # dashboard on http://localhost:8501
```

`run_all.py` keeps going if one updater fails and exits with code 1 if any
updater failed.

## Notes

- Dates always use Tehran time, whatever the server's timezone is.
- The live gold price endpoint currently returns 404, so today's gold row is a
  temporary copy of the latest history price and is corrected the next day.