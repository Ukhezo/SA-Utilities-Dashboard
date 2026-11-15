# SA Utilities Dashboard

A standalone South African weather and load-shedding dashboard built with HTML, CSS, and vanilla JavaScript.

## Run

Open `index.html` in a modern browser with an internet connection. Weather loads automatically for Cape Town; use the search box to select another South African city or town.

## Data sources

- Weather: [Open-Meteo geocoding](https://open-meteo.com/en/docs/geocoding-api) and forecast APIs. No API key is required.
- Load-shedding: [EskomSePush Business API v3.1](https://developer.sepush.co.za/business/3.1/), currently marked beta. A personal API token is required to search areas and schedules. The page keeps the token only in the open page and sends it directly to EskomSePush over HTTPS; it does not save it in browser storage or source code. Requests may consume the token's API credits.

The dashboard displays API errors and missing data instead of substituting sample schedules. Live data depends on the providers' availability and terms. Check official local notices for critical planning.
