from datetime import date, datetime

# 📦 Euro-Währungsformat im deutschen Stil
def format_currency(value):
    try:
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"
    except (TypeError, ValueError):
        return "-"

# 📅 Datum im Format TT.MM.JJJJ
def format_datum(value):
    try:
        return value.strftime('%d.%m.%Y')
    except:
        return "–"