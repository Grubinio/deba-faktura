
# 📦 Euro-Währungsformat im deutschen Stil
@app.template_filter('currency')
def format_currency(value):
    try:
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"
    except (TypeError, ValueError):
        return "-"

# 📅 Datum im Format TT.MM.JJJJ
@app.template_filter('datum_de')
def format_datum(value):
    try:
        return value.strftime('%d.%m.%Y')
    except:
        return "–"