from dataclasses import dataclass
from decimal import Decimal
from zoneinfo import ZoneInfo

from apps.accounts.models import Role
from apps.billing.domain.types import BillingModel

DEMO_PASSWORD = "billable-demo"
DEMO_TIMEZONE = ZoneInfo("Europe/Istanbul")


@dataclass(frozen=True, slots=True)
class DemoMember:
    email: str
    first_name: str
    last_name: str
    role: Role
    daily_hours: tuple[float, float]
    focus: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DemoProject:
    code: str
    name: str
    color: str
    is_billable: bool = True


@dataclass(frozen=True, slots=True)
class DemoContract:
    billing_model: BillingModel
    rounding_increment_minutes: int
    hourly_rate: Decimal | None = None
    monthly_fee: Decimal | None = None
    included_hours: Decimal | None = None
    overage_rate: Decimal | None = None
    rollover_cap_hours: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class DemoClient:
    key: str
    name: str
    contact_name: str
    email: str
    currency: str
    tax_rate: Decimal
    weight: float
    projects: tuple[DemoProject, ...]
    contract: DemoContract | None


MEMBERS = (
    DemoMember("ayse@northwind.test", "Ayşe", "Kaya", Role.OWNER, (1.5, 3.0), ("NW", "LUM")),
    DemoMember("can@northwind.test", "Can", "Demir", Role.MANAGER, (3.0, 4.5), ("ATL", "NW")),
    DemoMember("elif@northwind.test", "Elif", "Şahin", Role.MEMBER, (5.5, 7.5), ("LUM", "KZY")),
    DemoMember("mert@northwind.test", "Mert", "Yıldız", Role.MEMBER, (6.0, 7.5), ("ATL", "ORB")),
    DemoMember(
        "zeynep@northwind.test", "Zeynep", "Arslan", Role.MEMBER, (5.0, 7.0), ("LUM", "KZY")
    ),
    DemoMember("deniz@northwind.test", "Deniz", "Aydın", Role.MEMBER, (6.0, 7.5), ("ORB", "ATL")),
)

CLIENTS = (
    DemoClient(
        key="LUM",
        name="Lumen Coffee",
        contact_name="Selin Öztürk",
        email="finance@lumencoffee.test",
        currency="USD",
        tax_rate=Decimal("0.00"),
        weight=0.22,
        projects=(
            DemoProject("LUM-BR", "Brand Refresh", "#8D6E63"),
            DemoProject("LUM-SOC", "Social Content", "#FF7043"),
        ),
        contract=DemoContract(
            billing_model=BillingModel.RETAINER,
            rounding_increment_minutes=15,
            monthly_fee=Decimal("19800.00"),
            included_hours=Decimal("180.00"),
            overage_rate=Decimal("125.00"),
            rollover_cap_hours=Decimal("15.00"),
        ),
    ),
    DemoClient(
        key="ATL",
        name="Atlas Fintech",
        contact_name="Emre Koç",
        email="ap@atlasfintech.test",
        currency="USD",
        tax_rate=Decimal("0.00"),
        weight=0.30,
        projects=(
            DemoProject("ATL-APP", "Mobile App UI", "#3949AB"),
            DemoProject("ATL-WEB", "Marketing Site", "#1E88E5"),
        ),
        contract=DemoContract(
            billing_model=BillingModel.HOURLY,
            rounding_increment_minutes=6,
            hourly_rate=Decimal("115.00"),
        ),
    ),
    DemoClient(
        key="ORB",
        name="Orbit Outdoor",
        contact_name="Lena Fischer",
        email="billing@orbitoutdoor.test",
        currency="EUR",
        tax_rate=Decimal("0.00"),
        weight=0.22,
        projects=(DemoProject("ORB-SHOP", "E-commerce Rebuild", "#43A047"),),
        contract=DemoContract(
            billing_model=BillingModel.FIXED_FEE,
            rounding_increment_minutes=15,
            monthly_fee=Decimal("16000.00"),
        ),
    ),
    DemoClient(
        key="KZY",
        name="Kuzey Mobilya",
        contact_name="Burak Çelik",
        email="muhasebe@kuzeymobilya.test",
        currency="TRY",
        tax_rate=Decimal("20.00"),
        weight=0.13,
        projects=(
            DemoProject("KZY-CAT", "Catalog Design", "#6D4C41"),
            DemoProject("KZY-Q4", "Q4 Campaign", "#F4511E"),
        ),
        contract=DemoContract(
            billing_model=BillingModel.RETAINER,
            rounding_increment_minutes=15,
            monthly_fee=Decimal("260000.00"),
            included_hours=Decimal("100.00"),
            overage_rate=Decimal("3000.00"),
            rollover_cap_hours=Decimal("10.00"),
        ),
    ),
    DemoClient(
        key="NW",
        name="Northwind Internal",
        contact_name="",
        email="",
        currency="USD",
        tax_rate=Decimal("0.00"),
        weight=0.13,
        projects=(DemoProject("NW-INT", "Internal & Admin", "#78909C", is_billable=False),),
        contract=None,
    ),
)

DESCRIPTIONS = {
    "LUM-BR": ("Logo exploration", "Packaging mockups", "Brand guideline layout", "Client review"),
    "LUM-SOC": ("Instagram carousel", "Reels storyboard", "Monthly content calendar"),
    "ATL-APP": ("Onboarding flow", "Design system tokens", "Payments screen", "Usability fixes"),
    "ATL-WEB": ("Landing page build", "Pricing page copy", "SEO improvements"),
    "ORB-SHOP": ("Product listing page", "Checkout integration", "Performance tuning", "QA pass"),
    "KZY-CAT": ("Catalog spreads", "Product photo retouching", "Print-ready export"),
    "KZY-Q4": ("Campaign key visual", "Billboard adaptation", "Social media sizes"),
    "NW-INT": ("Team sync", "Planning", "Portfolio update", "Hiring interviews"),
}
