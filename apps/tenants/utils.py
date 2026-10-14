"""Enriquecimento dos dados de tenant devolvidos pela API do UltraDoc."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

# Dias antes do vencimento em que o cliente passa a aparecer como "vence em breve".
EXPIRING_SOON_DAYS = 7

STATUS_LABELS = {
    "expired": ("Vencido", "danger"),
    "trial": ("Em teste", "info"),
    "expiring": ("Vence em breve", "warning"),
    "active": ("Ativo", "success"),
    "no_due_date": ("Sem vencimento", "secondary"),
}


def parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def parse_decimal(value):
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def compute_status(tenant: dict, today=None) -> str:
    """Espelha a regra do UltraDoc (``TenantExpirationMiddleware``): com
    ``paid_until`` no passado o acesso do cliente é bloqueado, mesmo em teste;
    sem ``paid_until`` o acesso nunca expira."""
    today = today or date.today()
    paid_until = parse_date(tenant.get("paid_until"))
    if paid_until and paid_until < today:
        return "expired"
    if tenant.get("on_trial"):
        return "trial"
    if paid_until is None:
        return "no_due_date"
    if (paid_until - today).days <= EXPIRING_SOON_DAYS:
        return "expiring"
    return "active"


def enrich_tenant(tenant: dict, today=None) -> dict:
    """Converte datas/valores e acrescenta ``status``, ``status_label``,
    ``status_color`` e ``days_left`` ao dicionário vindo da API."""
    today = today or date.today()
    tenant["paid_until"] = parse_date(tenant.get("paid_until"))
    tenant["created_on"] = parse_date(tenant.get("created_on"))
    tenant["monthly_price"] = parse_decimal(tenant.get("monthly_price"))
    status = compute_status(tenant, today)
    label, color = STATUS_LABELS[status]
    tenant["status"] = status
    tenant["status_label"] = label
    tenant["status_color"] = color
    tenant["days_left"] = (tenant["paid_until"] - today).days if tenant["paid_until"] else None
    return tenant


def summarize_tenants(tenants: list) -> dict:
    """KPIs do painel inicial a partir de UMA chamada de listagem (a API do
    UltraDoc limita a 20 requisições por minuto por IP; nada de N+1)."""
    summary = {
        "total": len(tenants),
        "active": 0,
        "expiring": 0,
        "trial": 0,
        "expired": 0,
        "no_due_date": 0,
        "mrr": Decimal("0"),
        "storage_gb": 0,
        "storage_used_gb": 0.0,
        "manager_licenses": 0,
        "staff_licenses": 0,
    }
    for tenant in tenants:
        summary[tenant["status"]] += 1
        if tenant["status"] != "expired":
            summary["mrr"] += tenant["monthly_price"]
        summary["storage_gb"] += int(tenant.get("storage_gb") or 0)
        summary["storage_used_gb"] += float(tenant.get("storage_used_gb") or 0)
        summary["manager_licenses"] += int(tenant.get("manager_licenses") or 0)
        summary["staff_licenses"] += int(tenant.get("staff_licenses") or 0)
    summary["storage_used_gb"] = round(summary["storage_used_gb"], 2)
    if summary["storage_gb"]:
        summary["storage_percent"] = round(min(summary["storage_used_gb"] / summary["storage_gb"] * 100, 100), 1)
    else:
        summary["storage_percent"] = None
    return summary
