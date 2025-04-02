def format_currency(value):
    try:
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"
    except (TypeError, ValueError):
        return "-"
