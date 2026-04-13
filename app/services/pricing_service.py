"""
pricing_service.py — Tính giá bán sau khi markup
"""

import logging
from app.config import PRICE_MARKUP

logger = logging.getLogger(__name__)


def apply_markup(base_price: float) -> float:
    """
    Tăng giá thêm PRICE_MARKUP%.
    Kết quả làm tròn đến .5K gần nhất để giá trông tự nhiên hơn.
    """
    marked = base_price * (1 + PRICE_MARKUP / 100)

    # Làm tròn đến 1K gần nhất (VD: 87.5 → 88, 87.4 → 87)
    rounded = round(marked)

    logger.debug(
        "Pricing: base=%.1fK markup=%.1f%% → %.1fK",
        base_price, PRICE_MARKUP, rounded,
    )
    return rounded


def format_price(price: float) -> str:
    """Định dạng giá để hiển thị, luôn là số nguyên K. VD: 25.0 → '25K'."""
    return f"{int(price)}K"
