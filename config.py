# Default processing settings
DEFAULT_SETTINGS = {
    "MAX_PDF_SIZE": 10 * 1024 * 1024,  # 10 MB
    "MAX_EXCEL_ROWS": 1000000,
    "MAX_WORKERS": 1,  # Force single worker for sequential processing
    "RETRY_ATTEMPTS": 3,
    "RETRY_DELAY": 2,  # seconds
}

# Coupon rules
COUPON_RULES = {
    4900: {"reduction": 400, "categories": ["A"]},
    15500: {"reduction": 500, "categories": ["B1", "C"]},
    17900: {"reduction": 900, "categories": ["B"]},
    19080: {"reduction": 1080, "categories": ["C"]},
    26235: {"reduction": 1235, "categories": ["D"]},
    41750: {"reduction": 1750, "categories": ["AUTRES"]},
}

# Excel headers (for CSV/IA)
EXCEL_HEADERS = [
    "DATE",
    "N° PV",
    "DESCRIPTIONS",
    "COUPON",
    "C/CV",
    "IMMATRI",
    "CONTACT",
    "CAT",
    "DATE P.V",
    "pht",
    "TVA",
    "PTTC",
]

class Config:
    """Configuration class for IA/CSV extraction only"""
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.coupon_rules = COUPON_RULES.copy()
        self.excel_headers = EXCEL_HEADERS.copy()

    def validate(self) -> None:
        if self.settings["MAX_WORKERS"] < 1:
            raise ConfigError("MAX_WORKERS must be at least 1")
        if self.settings["MAX_PDF_SIZE"] < 1024:
            raise ConfigError("MAX_PDF_SIZE must be at least 1KB")
        if self.settings["MAX_EXCEL_ROWS"] < 1:
            raise ConfigError("MAX_EXCEL_ROWS must be at least 1")

class ConfigError(Exception):
    pass

config = Config()

try:
    config.validate()
except ConfigError as e:
    print(f"Configuration Error: {str(e)}")
    raise
 