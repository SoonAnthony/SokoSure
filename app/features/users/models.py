from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, func


class BusinessType(str, Enum):
    MAMA_MBOGA = "MAMA_MBOGA"               # vegetable/fruit vendor
    MITUMBA = "MITUMBA"                     # secondhand clothes (Gikomba-style)
    KIBANDA_FOOD = "KIBANDA_FOOD"           # food kiosk / street food
    SALON_BARBERSHOP = "SALON_BARBERSHOP"   # salon or barbershop
    JUAKALI = "JUAKALI"                     # hardware/jua kali metalwork/welding
    ELECTRONICS_PHONE = "ELECTRONICS_PHONE" # phone accessories, repair, small electronics
    SHOES_BAGS  = "SHOES_BAGS"              # shoe/bag sellers
    DUKA = "DUKA"                           # small general shop/duka
    TAILORING   = "TAILORING"               # tailoring/fundi cherehani
    OTHER = "OTHER"

class IncomeBracket(str, Enum):
    BELOW_500 = "Below 500"
    RANGE_500_1000 = "500 - 1,000"
    RANGE_1000_3000 = "1,000 - 3,000"
    RANGE_3000_10000 = "3,000 - 10,000"
    ABOVE_10000 = "Above 10,000"

class PaymentFrequency(str, Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"

class County(str, Enum):
    MOMBASA = "MOMBASA"
    KWALE = "KWALE"
    KILIFI = "KILIFI"
    TANA_RIVER = "TANA_RIVER"
    LAMU = "LAMU"
    TAITA_TAVETA = "TAITA_TAVETA"
    GARISSA = "GARISSA"
    WAJIR = "WAJIR"
    MANDERA = "MANDERA"
    MARSABIT = "MARSABIT"
    ISIOLO = "ISIOLO"
    MERU = "MERU"
    THARAKA_NITHI = "THARAKA_NITHI"
    EMBU = "EMBU"
    KITUI = "KITUI"
    MACHAKOS = "MACHAKOS"
    MAKUENI = "MAKUENI"
    NYANDARUA = "NYANDARUA"
    NYERI = "NYERI"
    KIRINYAGA = "KIRINYAGA"
    MURANGA = "MURANGA"
    KIAMBU = "KIAMBU"
    TURKANA = "TURKANA"
    WEST_POKOT = "WEST_POKOT"
    SAMBURU = "SAMBURU"
    TRANS_NZOIA = "TRANS_NZOIA"
    UASIN_GISHU = "UASIN_GISHU"
    ELGEYO_MARAKWET = "ELGEYO_MARAKWET"
    NANDI = "NANDI"
    BARINGO = "BARINGO"
    LAIKIPIA = "LAIKIPIA"
    NAKURU = "NAKURU"
    NAROK = "NAROK"
    KAJIADO = "KAJIADO"
    KERICHO = "KERICHO"
    BOMET = "BOMET"
    KAKAMEGA = "KAKAMEGA"
    VIHIGA = "VIHIGA"
    BUNGOMA = "BUNGOMA"
    BUSIA = "BUSIA"
    SIAYA = "SIAYA"
    KISUMU = "KISUMU"
    HOMA_BAY = "HOMA_BAY"
    MIGORI = "MIGORI"
    KISII = "KISII"
    NYAMIRA = "NYAMIRA"
    NAIROBI = "NAIROBI"

class User(SQLModel, table=True):
    id:UUID = Field(default_factory=uuid4, primary_key=True)
    national_id:str = Field(unique=True, index=True)
    phone_no:str = Field(unique=True, index=True)
    full_name:str 
    hashed_pin:str
    failed_pin_attempts:int = Field(default=0)
    county:County = Field(index=True)
    business_type: BusinessType
    income_bracket: IncomeBracket
    payment_frequency: PaymentFrequency
    created_at:Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True),
        server_default=func.now()
        )
    )

