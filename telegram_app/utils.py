# telegram_app/utils.py
import json
import re
import requests
from django.conf import settings
from .models import TelegramMessage


def save_messages_json():
    """
    TelegramMessage modelidagi barcha xabarlarni JSON faylga saqlash
    """
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


def parse_shipment_text(text: str) -> list:
    """
    AI yordamida yuklar parsing qilish
    """
    if not text or not text.strip():
        return []
    
    GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', '')
    
    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY topilmadi! Fallback parsing...")
        return parse_shipment_text_fallback(text)
    
    prompt = f"""Sen professional yuk parsing botsan. Quyidagi xabardagi BARCHA yuklarni ajratib ber.

MUHIM QOIDALAR:
1. Har bir "━━━" yoki "---" chiziq YANGI YUK ekanligini bildiradi
2. Har bir 🇷🇺 yoki 🇧🇾 = ORIGIN (qayerdan)
3. Har bir 🇺🇿 = DESTINATION (qayerga)
4. Agar bitta origin dan bir nechta destination bo'lsa - har biri ALOHIDA YUK!

XABAR:
{text}

Faqat JSON array qaytaring:
[
  {{"origin": "shahar", "destination": "shahar", "cargo_type": "yuk", "truck_type": "transport", "payment_type": "tolov"}}
]
"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "Sen yuk parsing botsan. Faqat JSON qaytarasan."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 8000
            },
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        ai_response = result['choices'][0]['message']['content'].strip()
        
        # JSON ni tozalash
        if ai_response.startswith('```json'):
            ai_response = ai_response[7:]
        if ai_response.startswith('```'):
            ai_response = ai_response[3:]
        if ai_response.endswith('```'):
            ai_response = ai_response[:-3]
        
        ai_response = ai_response.strip()
        shipments = json.loads(ai_response)
        
        if not isinstance(shipments, list):
            raise ValueError("AI javob list emas")
        
        # Telefon qo'shish
        phones = re.findall(r"\+?\d{9,15}", text)
        default_phone = phones[0] if phones else None
        
        for shipment in shipments:
            if not isinstance(shipment, dict):
                continue
            shipment['phone'] = shipment.get('phone') or default_phone
            shipment['weight'] = shipment.get('weight')
            shipment['additional_info'] = shipment.get('additional_info')
        
        print(f"✅ AI {len(shipments)} ta yuk topdi!")
        return shipments
        
    except Exception as e:
        print(f"❌ AI xato: {e} - Fallback ishlatilmoqda")
        return parse_shipment_text_fallback(text)


def parse_shipment_text_fallback(text: str) -> list:
    """
    YAXSHILANGAN FALLBACK PARSER
    
    Har bir yuk guruhini to'liq ajratadi
    """
    if not text or not text.strip():
        return []
    
    print("🔄 Fallback parser ishga tushdi...")
    
    # Telefon
    phones = re.findall(r"\+?\d{9,15}", text)
    default_phone = phones[0] if phones else None
    
    # Xabarni ━━━ yoki --- bilan bo'lish
    sections = re.split(r'[━─]{3,}', text)
    
    all_shipments = []
    
    for idx, section in enumerate(sections):
        if not section.strip():
            continue
        
        # Origins: 🇷🇺 va 🇧🇾
        origins = []
        
        # 🇷🇺 dan keyin kelgan shaharlar
        ru_pattern = r'🇷🇺\s*([А-ЯЁA-Z][А-ЯЁA-Z\s]*?)(?=\s*(?:🇷🇺|🇧🇾|🇺🇿|ГРУЗ|ТЕНТ|РЕФ|ОПЛАТА|\+|$))'
        ru_matches = re.findall(ru_pattern, section, re.MULTILINE | re.IGNORECASE)
        
        # 🇧🇾 dan keyin kelgan shaharlar
        by_pattern = r'🇧🇾\s*([А-ЯЁA-Z][А-ЯЁA-Z\s]*?)(?=\s*(?:🇷🇺|🇧🇾|🇺🇿|ГРУЗ|ТЕНТ|РЕФ|ОПЛАТА|\+|$))'
        by_matches = re.findall(by_pattern, section, re.MULTILINE | re.IGNORECASE)
        
        origins.extend([o.strip() for o in ru_matches if o.strip()])
        origins.extend([o.strip() for o in by_matches if o.strip()])
        
        # Destinations: 🇺🇿
        uz_pattern = r'🇺🇿\s*(?:УЗБ\s+)?([А-ЯЁA-Z][А-ЯЁA-Z\s]*?)(?=\s*(?:🇷🇺|🇧🇾|🇺🇿|ГРУЗ|ТЕНТ|РЕФ|ОПЛАТА|\+|$))'
        uz_matches = re.findall(uz_pattern, section, re.MULTILINE | re.IGNORECASE)
        destinations = [d.strip() for d in uz_matches if d.strip()]
        
        # Yuk turi
        cargo_match = re.search(r'ГРУЗ\s+([А-ЯЁ\s]+?)(?=\n|ТЕНТ|РЕФ|ОПЛАТА|$)', section, re.IGNORECASE)
        cargo_type = cargo_match.group(1).strip() if cargo_match else None
        
        # Transport
        truck_types = []
        if re.search(r'ТЕНТ\s*ФУРА', section, re.IGNORECASE):
            truck_types.append('ТЕНТ ФУРА')
        if re.search(r'РЕФ\s*ФУРА', section, re.IGNORECASE):
            truck_types.append('РЕФ ФУРА')
        truck_type = ', '.join(truck_types) if truck_types else None
        
        # To'lov
        payment_match = re.search(r'ОПЛАТА\s+([А-ЯЁ\s]+?)(?=\n|\$|💲|$)', section, re.IGNORECASE)
        payment_type = payment_match.group(1).strip() if payment_match else None
        
        # ✅ Har bir origin × destination = alohida yuk
        if origins and destinations:
            for origin in origins:
                for destination in destinations:
                    all_shipments.append({
                        "origin": origin[:50],  # Max 50 belgi
                        "destination": destination[:50],
                        "cargo_type": cargo_type[:50] if cargo_type else None,
                        "truck_type": truck_type[:50] if truck_type else None,
                        "payment_type": payment_type[:30] if payment_type else None,
                        "phone": default_phone,
                        "weight": None,
                        "additional_info": None
                    })
        elif origins or destinations:
            # Faqat biri bo'lsa
            all_shipments.append({
                "origin": origins[0][:50] if origins else None,
                "destination": destinations[0][:50] if destinations else None,
                "cargo_type": cargo_type[:50] if cargo_type else None,
                "truck_type": truck_type[:50] if truck_type else None,
                "payment_type": payment_type[:30] if payment_type else None,
                "phone": default_phone,
                "weight": None,
                "additional_info": None
            })
    
    if not all_shipments:
        # Agar hech narsa topilmasa, bo'sh yuk
        all_shipments.append({
            "origin": None,
            "destination": None,
            "cargo_type": None,
            "truck_type": None,
            "payment_type": None,
            "phone": default_phone,
            "weight": None,
            "additional_info": None
        })
    
    print(f"✅ Fallback: {len(all_shipments)} ta yuk topildi")
    return all_shipments