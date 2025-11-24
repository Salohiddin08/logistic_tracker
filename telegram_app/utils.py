# telegram_app/utils.py
import json
import re
from .models import TelegramMessage

def save_messages_json():
    qs = TelegramMessage.objects.all()
    data = []

    for m in qs:
        data.append({
            "channel_id": m.channel_id,
            "user_id": m.user_id,
            "date": m.date.isoformat(),
            "text": m.text,
            "location": {
                "uz": m.location_uz,
                "ru": m.location_ru,
                "en": m.location_en
            }
        })

    with open("telegram_messages.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def parse_shipment_text(text: str) -> dict:
    """Kanaldagi yuk eʼlonlaridan A→B, yuk turi, transport va telefonni ajratib olish.

    Qaytadi:
      {
        "origin": str | None,
        "destination": str | None,
        "cargo_type": str | None,
        "truck_type": str | None,
        "payment_type": str | None,
        "phone": str | None,
      }
    """
    if not text:
        return {
            "origin": None,
            "destination": None,
            "cargo_type": None,
            "truck_type": None,
            "payment_type": None,
            "phone": None,
        }

    # Qatorlarga bo'lib, bo'shlarini olib tashlaymiz
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # 1) Manzil/qayerdan-qayergacha (🇷🇺, 🇺🇿, 🇸🇱, 🇧🇾 qatordan olinadi)
    city_lines = []
    route_pairs = []  # [(origin, destination)]
    flag_patterns = ["🇷🇺", "🇺🇿", "🇸🇱", "🇧᷍", "🇧🇾"]
    separators = ["➝", "➡", "→", "🔜", "-", "—", "->"]

    for ln in lines:
        if any(flag in ln for flag in flag_patterns):
            cleaned = ln
            for flag in flag_patterns:
                cleaned = cleaned.replace(flag, "")
            cleaned = cleaned.strip()
            if not cleaned:
                continue

            # Avval bitta qatorda A va B bo'lsa, ajratib olamiz: "Азалкент-Зеленоград",
            # "САМАРКАНД  🔜  КРАСНОДАР АНАПА" va hokazo.
            split_done = False
            for sep in separators:
                if sep in cleaned:
                    left, right = cleaned.split(sep, 1)
                    left = left.strip(" -➡→—🔜")
                    right = right.strip(" -➡→—🔜")
                    if left and right:
                        route_pairs.append((left, right))
                        split_done = True
                        break

            # Agar separator topilmasa, shunchaki shahar qatori sifatida saqlaymiz
            if not split_done:
                city_lines.append(cleaned)

    # Agar aniq A→B juftlik topilgan bo'lsa, shuni ishlatamiz
    if route_pairs:
        origin, destination = route_pairs[0]
    else:
        origin = city_lines[0] if len(city_lines) >= 1 else None
        destination = city_lines[1] if len(city_lines) >= 2 else None

    cargo_type = None
    truck_type = None
    payment_type = None

    for ln in lines:
        upper_ln = ln.upper()
        if upper_ln.startswith("ЮК") and cargo_type is None:
            cargo_type = ln
        if upper_ln.startswith("ТЕНТ") and truck_type is None:
            truck_type = "ТЕНТ"
        if "НАХТ" in upper_ln and payment_type is None:
            payment_type = "НАХТ"

    # Telefon raqam(lar)i
    phones = re.findall(r"\+?\d{7,15}", text)
    phone = phones[0] if phones else None

    return {
        "origin": origin,
        "destination": destination,
        "cargo_type": cargo_type,
        "truck_type": truck_type,
        "payment_type": payment_type,
        "phone": phone,
    }
