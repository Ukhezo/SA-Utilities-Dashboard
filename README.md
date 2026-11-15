# SA Utilities Dashboard

A standalone South African utilities dashboard with live weather forecasts for Umvoti Municipality Wards 1–14 and an EskomSePush load-shedding lookup.

## Run

Open `index.html` in a modern browser with an internet connection. The ward panel loads forecasts for all 14 Umvoti wards; use the other weather search to select a South African city or town.

## Data sources

- Weather: [Open-Meteo geocoding](https://open-meteo.com/en/docs/geocoding-api) and forecast APIs. No API key is required.
- Ward locations: forecast coordinates are the polygon centroids of the [geoBoundaries South Africa ADM4 2020 dataset](https://www.geoboundaries.org/api/current/gbOpen/ZAF/ADM4/), sourced from OCHA ROSEA and the South African Municipal Demarcation Board (CC BY 3.0 IGO). The forecast is a gridded model estimate at each ward centroid, not a local weather-station observation; the boundary data represents 2020.
- Load-shedding: [EskomSePush Business API v3.1](https://developer.sepush.co.za/business/3.1/), currently marked beta. A personal API token is required to search areas and schedules. The page keeps the token only in the open page and sends it directly to EskomSePush over HTTPS; it does not save it in browser storage or source code. Requests may consume the token's API credits.

The dashboard displays API errors and missing data instead of substituting sample schedules. Live data depends on the providers' availability and terms. Check official local notices for critical planning.
