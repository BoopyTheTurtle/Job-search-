import pytest

from jobbot.enrich.language import detect_language

LONG_EN = (
    "We are looking for a junior Python developer to join our fully remote team. You will "
    "build APIs, write tests, review code and work closely with product managers across Europe. "
    "Experience with Django or FastAPI is a plus. We offer a learning budget and flexible hours."
)
LONG_FR = (
    "Nous recherchons un développeur Python junior pour rejoindre notre équipe entièrement en "
    "télétravail. Vous développerez des API, écrirez des tests et travaillerez avec les chefs de "
    "produit. Une expérience avec Django est un plus. Nous offrons un budget formation."
)
LONG_LV = (
    "Meklējam jaunāko Python programmētāju, kas pievienosies mūsu pilnībā attālinātajai komandai. "
    "Tu veidosi API, rakstīsi testus un strādāsi kopā ar produktu vadītājiem visā Eiropā. "
    "Pieredze ar Django būs priekšrocība. Piedāvājam mācību budžetu un elastīgu darba laiku."
)
LONG_ES = (
    "Buscamos un desarrollador Python junior para unirse a nuestro equipo totalmente remoto. "
    "Construirás APIs, escribirás pruebas y trabajarás con los gerentes de producto en Europa. "
    "Se valora experiencia con Django. Ofrecemos presupuesto de formación y horario flexible."
)
LONG_DE = (
    "Wir suchen einen Junior Python Entwickler für unser vollständig remote arbeitendes Team. "
    "Du baust APIs, schreibst Tests und arbeitest eng mit dem Produktmanagement zusammen. "
    "Erfahrung mit Django ist ein Plus. Wir bieten ein Weiterbildungsbudget und flexible Zeiten."
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [(LONG_EN, "en"), (LONG_FR, "fr"), (LONG_LV, "lv"), (LONG_ES, "es"), (LONG_DE, "de")],
)
def test_detects_long_texts(text: str, expected: str) -> None:
    code, confidence = detect_language(text)
    assert code == expected
    assert confidence >= 0.8


def test_short_text_uses_lower_bar() -> None:
    code, _ = detect_language("Junior Python Developer, fully remote, Europe")
    assert code == "en"
    code, _ = detect_language("Programmētājs attālināti, pilna slodze")
    assert code == "lv"


def test_empty_text() -> None:
    assert detect_language("   ") == (None, 0.0)
