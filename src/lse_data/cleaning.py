"""Strict normalization before values reach the database."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
import re

from .schema import COLUMNS, LENGTHS, PRICES, INTEGERS, nullable


def normalize(table, fields):
    names = COLUMNS[table]
    if len(fields) != len(names):
        raise ValueError(f"Expected {len(names)} fields; received {len(fields)}")
    result = []
    for name, raw in zip(names, fields):
        value = raw.strip()
        if value.upper() in {"", "NULL", "\\N"}:
            if not nullable(table, name):
                raise ValueError(f"{name}: required value missing")
            result.append(None)
            continue
        if name in PRICES:
            try:
                number = Decimal(value)
            except InvalidOperation as exc:
                raise ValueError(f"{name}: invalid decimal") from exc
            if (
                not number.is_finite()
                or number < 0
                or number >= Decimal("10000000000")
                or number != number.quantize(Decimal("0.00000001"))
            ):
                raise ValueError(f"{name}: outside nonnegative DECIMAL(18,8)")
            value = format(number, ".8f")
        elif name in INTEGERS:
            limit = (
                9223372036854775807 if name == "MessageSequenceNumber" else 999999999999
            )
            if not re.fullmatch(r"\d+", value) or int(value) > limit:
                raise ValueError(f"{name}: invalid nonnegative integer")
            value = int(value)
        elif name.endswith("Date"):
            pattern = "%d%m%Y" if re.fullmatch(r"\d{8}", value) else "%Y-%m-%d"
            value = datetime.strptime(value, pattern).date().isoformat()
        elif name.endswith("Time"):
            if not re.fullmatch(r"\d{2}:\d{2}:\d{2}(\.\d{1,6})?", value):
                raise ValueError(f"{name}: invalid time")
            value = datetime.strptime(
                value, "%H:%M:%S.%f" if "." in value else "%H:%M:%S"
            ).strftime("%H:%M:%S.%f")
        elif len(value) > LENGTHS[name]:
            raise ValueError(f"{name}: field too long")
        if name == "BuySellInd" and value not in {"B", "S"}:
            raise ValueError("BuySellInd: expected B or S")
        if name == "OrderActionType" and value not in {"D", "E", "P", "M", "T"}:
            raise ValueError("OrderActionType: unknown lifecycle action")
        result.append(value)
    return result
