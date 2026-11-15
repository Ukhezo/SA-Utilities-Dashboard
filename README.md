# SA Utilities Dashboard

[![tests](https://github.com/Ukhezo/SA-Utilities-Dashboard/actions/workflows/tests.yml/badge.svg)](https://github.com/Ukhezo/SA-Utilities-Dashboard/actions/workflows/tests.yml)

A South African dashboard that shows **live weather** for any city or town and the **latest load-shedding stage and upcoming outages**, built with HTML, CSS, JavaScript, Python and GitHub Actions.

**Live site: [ukhezo.github.io/SA-Utilities-Dashboard](https://ukhezo.github.io/SA-Utilities-Dashboard/)**

## Features

- **Weather search:** current temperature, feels-like, humidity, wind and a 5-day outlook for any South African city or town.
- **Load-shedding status:** the national stage, the next stage change and the upcoming outages for one area, with "happening now" highlighted.
- **Automatic updates:** a scheduled GitHub Actions job fetches fresh load-shedding data every 4 hours.
- **No secrets in the browser:** the EskomSePush token is stored as a GitHub secret and never reaches the page.
- **Honest data:** clear messages when data is missing, failing or out of date, and no made-up sample schedules.
- **Responsive and accessible:** works on phones, with live status messages for screen readers.

## How it works

```
GitHub Actions (every 4 hours)
   └─ scripts/fetch_loadshedding.py ──► EskomSePush API (token from the ESP_TOKEN secret)
          └─ saves data/loadshedding.json ──► committed to the repo
                                                  │
Browser ─ index.html ─┬─ reads data/loadshedding.json (load-shedding)
                      └─ calls Open-Meteo directly (weather, no key needed)
```

**Why not call EskomSePush from the page?** The EskomSePush API doesn't allow requests from web pages (it sends no CORS headers), so the browser blocks them. A token in the page would also be visible to everyone. Running the request on GitHub Actions solves both problems, and it uses only 12 of the free plan's 50 daily API calls.

## Set up load-shedding updates

1. Get an EskomSePush API token (the free plan is enough) from the [EskomSePush API page](https://eskomsepush.gumroad.com/l/api).
2. In this repo, open **Settings → Secrets and variables → Actions**.
3. Under **Secrets**, click **New repository secret**. Name it `ESP_TOKEN` and paste your token.
4. Optional: under **Variables**, add `ESP_AREA` with your town or suburb. The default is `Cape Town`.
5. Open the **Actions** tab, choose **Update load-shedding data**, and click **Run workflow**.

The dashboard shows the new data a minute or two after the job finishes, then updates itself every 4 hours.

## Run it locally

```bash
git clone https://github.com/Ukhezo/SA-Utilities-Dashboard.git
cd SA-Utilities-Dashboard
python -m http.server 8000      # then open http://localhost:8000
```

To fetch load-shedding data yourself:

```bash
ESP_TOKEN=your-token ESP_AREA="Cape Town" python scripts/fetch_loadshedding.py
```

Run the tests (they use fake API responses, so they need no token and use no credits):

```bash
pip install pytest
pytest
```

## Project structure

```
SA-Utilities-Dashboard/
├── index.html                       # the dashboard (HTML, CSS, JavaScript)
├── data/loadshedding.json           # saved by the scheduled job
├── scripts/fetch_loadshedding.py    # fetches from EskomSePush (Python standard library only)
├── tests/                           # pytest tests with fake API responses
└── .github/workflows/
    ├── loadshedding.yml             # every 4 hours: fetch and save data
    └── tests.yml                    # runs the tests on every push
```

## Data sources

- Weather: [Open-Meteo](https://open-meteo.com/) geocoding and forecast APIs. These are model forecasts, not weather-station readings.
- Load-shedding: [EskomSePush Business API v3.1](https://developer.sepush.co.za/business/3.1/), which is marked beta.

Data depends on these providers being available. Always check official Eskom or municipal notices for critical planning.

## Built with

HTML · CSS · JavaScript · Python · GitHub Actions · GitHub Pages

## License

[MIT](LICENSE) © 2026 Ukhezo
