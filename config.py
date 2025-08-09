DEFAULT_YEARS = [2025]
DEFAULT_COUNTRIES = ["ESP", "BAS", "CAN"]

# Mapping of custom country codes to WSL internal numeric identifiers
# These IDs are used by the athletes directory when filtering by country.
# Spain (ESP) was previously mis-mapped which caused the scraper to return
# cero resultados. 208 is the correct identifier for Spain, while the Basque
# Country and Canary Islands use their specific internal IDs.
COUNTRY_CODE_MAP = {
    "ESP": 208,  # Spain
    "BAS": 253,  # Basque Country
    "CAN": 250,  # Canary Islands
}
