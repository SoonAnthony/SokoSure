# app/features/ussd/constants.py

from enum import Enum


class USSDState(str, Enum):
    MAIN_MENU = "MAIN_MENU"

    # Registration — 3 steps only (phone comes from AT)
    REGISTER_ID      = "REGISTER_ID"
    REGISTER_PIN     = "REGISTER_PIN"
    REGISTER_CONFIRM = "REGISTER_CONFIRM"

    # Login — 1 step only (phone comes from AT)
    LOGIN_PIN = "LOGIN_PIN"

    # Post-login dashboard and sub-flows
    DASHBOARD       = "DASHBOARD"
    VIEW_POLICY     = "VIEW_POLICY"
    ACTIVATE_POLICY = "ACTIVATE_POLICY"
    PAY_PREMIUM     = "PAY_PREMIUM"
    FILE_CLAIM_TYPE = "FILE_CLAIM_TYPE"
    FILE_CLAIM_DESC = "FILE_CLAIM_DESC"
    HELP            = "HELP"


# All 47 Kenyan counties (uppercase, used for validation)
COUNTIES: list[str] = [
    "MOMBASA", "KWALE", "KILIFI", "TANA_RIVER", "LAMU", "TAITA_TAVETA",
    "GARISSA", "WAJIR", "MANDERA", "MARSABIT", "ISIOLO", "MERU",
    "THARAKA_NITHI", "EMBU", "KITUI", "MACHAKOS", "MAKUENI", "NYANDARUA",
    "NYERI", "KIRINYAGA", "MURANGA", "KIAMBU", "TURKANA", "WEST_POKOT",
    "SAMBURU", "TRANS_NZOIA", "UASIN_GISHU", "ELGEYO_MARAKWET", "NANDI",
    "BARINGO", "LAIKIPIA", "NAKURU", "NAROK", "KAJIADO", "KERICHO",
    "BOMET", "KAKAMEGA", "VIHIGA", "BUNGOMA", "BUSIA", "SIAYA",
    "KISUMU", "HOMA_BAY", "MIGORI", "KISII", "NYAMIRA", "NAIROBI",
]

# Menu option → BusinessType enum value
BUSINESS_OPTIONS: dict[str, str] = {
    "1": "MAMA_MBOGA",
    "2": "MITUMBA",
    "3": "KIBANDA_FOOD",
    "4": "SALON_BARBERSHOP",
    "5": "JUAKALI",
    "6": "ELECTRONICS_PHONE",
    "7": "SHOES_BAGS",
    "8": "DUKA",
    "9": "TAILORING",
    "0": "OTHER",
}

# Menu option → IncomeBracket enum value
INCOME_OPTIONS: dict[str, str] = {
    "1": "Below 500",
    "2": "500 - 1,000",
    "3": "1,000 - 3,000",
    "4": "3,000 - 10,000",
    "5": "Above 10,000",
}

# Menu option → PaymentFrequency enum value
FREQUENCY_OPTIONS: dict[str, str] = {
    "1": "Daily",
    "2": "Weekly",
    "3": "Monthly",
}

# Menu option → ClaimCategory enum value
CLAIM_CATEGORY_OPTIONS: dict[str, str] = {
    "1": "FIRE",
    "2": "THEFT",
    "3": "FLOOD",
    "4": "OTHER",
}
