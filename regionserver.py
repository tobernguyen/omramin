########################################################################################################################

import typing as T  # isort: split

########################################################################################################################


def get_server_for_region(region: str) -> T.Optional[str]:
    servers = {
        "ASIA/PACIFIC": "https://data-sg.omronconnect.com",
        "EUROPE": "https://oi-api.ohiomron.eu",
        "NORTH AMERICA": "https://oi-api.ohiomron.com",
    }

    return servers.get(region.upper(), None)


def get_server_for_country_code(country_code: str) -> T.Optional[str]:
    # Define the mapping of regions to countries and their codes
    regions = {
        "ASIA/PACIFIC": [
            "AF",
            "AU",
            "BD",
            "BN",
            "BT",
            "KH",
            "CN",
            "FJ",
            "HK",
            "IN",
            "ID",
            # "JP",
            "KR",
            "LA",
            "MY",
            "MN",
            "MM",
            "NP",
            "NZ",
            "PK",
            "PG",
            "PH",
            "SG",
            "LK",
            "TW",
            "TH",
            "TL",
            "VN",
        ],
        "EUROPE": [
            "AL",
            "AD",
            "AT",
            "BY",
            "BE",
            "BA",
            "BG",
            "HR",
            "CZ",
            "DK",
            "EE",
            "FI",
            "FR",
            "DE",
            "GR",
            "HU",
            "IS",
            "IE",
            "IT",
            "LV",
            "LI",
            "LT",
            "LU",
            "MT",
            "MC",
            "ME",
            "NL",
            "MK",
            "NO",
            "PL",
            "PT",
            "RO",
            "RU",
            "SM",
            "RS",
            "SK",
            "SI",
            "ES",
            "SE",
            "CH",
            "UA",
            "GB",
            "VA",
        ],
        "NORTH AMERICA": ["CA", "MX", "US", "BZ", "CR", "SV", "GT", "HN", "NI", "PA"],
        "SOUTH AMERICA": ["AR", "BO", "BR", "CL", "CO", "EC", "GY", "PY", "PE", "SR", "UY", "VE"],
        "AFRICA": [
            "DZ",
            "AO",
            "BJ",
            "BW",
            "BF",
            "BI",
            "CM",
            "CV",
            "CF",
            "TD",
            "KM",
            "CI",
            "CD",
            "DJ",
            "EG",
            "GQ",
            "ER",
            "ET",
            "GA",
            "GM",
            "GH",
            "GN",
            "GW",
            "KE",
            "LS",
            "LR",
            "LY",
            "MG",
            "MW",
            "ML",
            "MR",
            "MA",
            "MZ",
            "NA",
            "NE",
            "NG",
            "RW",
            "SN",
            "SC",
            "SL",
            "SO",
            "ZA",
            "SS",
            "SD",
            "SZ",
            "TZ",
            "TG",
            "TN",
            "UG",
            "ZM",
            "ZW",
        ],
        "MIDDLE EAST": ["BH", "CY", "IR", "IQ", "IL", "JO", "KW", "LB", "OM", "PS", "QA", "SA", "SY", "TR", "AE", "YE"],
    }

    country_code = country_code.upper()
    if country_code == "JP":
        return "https://oi-api.ohiomron.jp"

    for region, codes in regions.items():
        if country_code in codes:
            return get_server_for_region(region)

    return None


########################################################################################################################
