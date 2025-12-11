```markdown
# 🚚 TG Yuk Monitor

Telegram’dagi yuk e’lonlari kanallaridan ma’lumot olib, ularni bir joyda ko‘rsatadigan web-panel.  
Loyiha **Django + Telethon** yordamida ishlaydi.

- Telegram akkauntingiz bilan **telefon raqam orqali** login qilasiz
- Kanallar ro‘yxatini ko‘rasiz va kerakli kanaldan xabarlarni yuklaysiz
- Xabarlar matnidan yo‘nalish (A→B), yuk turi, transport, to‘lov va telefonlarni ajratib oladi
- Statistikalar, filtrlar, Excel eksport va telefonlar ro‘yxati mavjud

---

## 1. Talablar

- Python 3.10+ (tavsiya)
- Git
- Telegram’da developer akkaunt (API ID / API HASH uchun)

---

## 2. O‘rnatish

```bash
git clone https://github.com/Salohiddin08/logistic_tracker.git
cd logistic_tracker
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
---

## 3. Sozlamalar

### 3.1. `.env` fayl

Loyiha ildizida `.env` fayl yarating (agar yo‘q bo‘lsa) va quyidagilarni kiriting:

```env
SECRET_KEY=ozingizning_django_secret_key_i
DEBUG=True

TG_API_ID=34259513
TG_API_HASH=558c38cc422e57adf957c21e0062c5fa
```
`TG_API_ID` va `TG_API_HASH` – Telegram’da ochilgan API ma’lumotlari.  
*Agar bu qiymatlar o‘zgarsa, `get_session.py` va sessiya yaratish oqimi ham shu qiymatlar bilan ishlaydi.*

### 3.2. Migratsiyalar

```bash
python manage.py migrate
```
Agar admin panel kerak bo‘lsa, superuser yarating:

```bash
python manage.py createsuperuser
```
---

## 4. Ishga tushirish

```bash
python manage.py runserver
```
Brauzerda oching:

- `http://127.0.0.1:8000/` – Telegram login oqimi (telefon bilan)
- `http://127.0.0.1:8000/channels/` – kanallar ro‘yxati
- `http://127.0.0.1:8000/admin/` – Django admin (ixtiyoriy)

---

## 5. Telegram login oqimi (telefon raqam orqali)

Sayt foydalanuvchi login / parolini **umuman so‘ramaydi**, faqat Telegram akkauntingizdan foydalanadi.

1. **Telefon raqam**  
   - Bosh sahifada yoki `/login/` manzilida telefoningizni `+998...` ko‘rinishida kiriting.  
   - Telethon sizga Telegram orqali SMS / kod yuboradi.

2. **SMS kodi va 2-bosqichli parol**  
   - `/tg-login/code/` sahifasida:
     - *SMS kodi* maydoniga Telegram’dan kelgan kodni kiriting.
     - Agar akkauntingizda **Two-step verification** yoqilgan bo‘lsa, *2-bosqichli parol* maydoniga Telegram parolingizni yozing (bo‘lmasa bo‘sh qoldirish mumkin).

3. **Sessiya saqlash**  
   - Login muvaffaqiyatli bo‘lsa, Telethon `StringSession` yaratadi.
   - Bu sessiya `TelegramSession` jadvalida saqlanadi.
   - Siz avtomatik ravishda `Kanallar` sahifasiga yo‘naltirilasiz.

Keyingi kirishlarda, sessiya bazada turgan ekan, to‘g‘ridan‑to‘g‘ri kanallar va statistika bilan ishlash mumkin.

---

## 6. Asosiy bo‘limlar

### 6.1. Kanallar (`/channels/`)

- Oxirgi saqlangan `TelegramSession` asosida Telethon client yaratiladi.
- Siz a’zo bo‘lgan kanallar ro‘yxatini chiqaradi.
- Kerakli kanalni tanlab, xabarlarni `fetch` qilib olasiz.

### 6.2. Xabarlarni yuklash

- Tanlangan kanal uchun so‘nggi xabarlar (hozircha limit: 100) olinadi.
- Har bir xabar:
  - `Message` jadvaliga saqlanadi
  - Matn ichidan yuk haqidagi ma’lumotlar ajratilib, `Shipment` jadvaliga yoziladi:
    - `origin` / `destination`
    - `cargo_type`
    - `truck_type`
    - `payment_type`
    - `phone`

### 6.3. Kanal statistikasi (`/stats/<channel_id>/`)

Bir kanal bo‘yicha:

- **A → B yo‘nalishlari** (Qayerdan / Qayerga / Soni)
- **Yuk turlari** (va ularning soni)
- **Transport turlari** (masalan, ТЕНТ)
- **To‘lov turlari** (НАХТ va hokazo)
- Sana bo‘yicha filter: `date_from` / `date_to`
- Statistikani **Excel** formatida yuklab olish:

```text
/stats/<channel_id>/export-excel/
```
### 6.4. Telefonlar va xabarlar

- `Phones` bo‘limida unikal telefon raqamlar ro‘yxati
- Tanlangan telefon bo‘yicha barcha xabarlar (`/phones/messages/`)
- Yo‘nalish, yuk turi, transport va to‘lov bo‘yicha alohida xabarlar ro‘yxati (`route_messages.html`, `phone_messages.html` va boshqalar)

---

## 7. Paginatsiya

Ko‘p satrli jadvalar tartibli ko‘rinishi uchun pagination qo‘llanadi:

- **Saqlangan xabarlar (`/messages/`)** – har sahifada 20 ta xabar.
- **Kanal statistika** sahifasida:
  - A → B yo‘nalishlari – 1 sahifada 20 ta yo‘nalish.
  - Yuk turlari – 20 tadan.
  - Transport turlari – 20 tadan.
  - To‘lov turlari – 20 tadan.

Har bir jadval ostida (faqat 1 dan ko‘p sahifa bo‘lsa):

- `⬅ Oldingi` / `Keyingi ➡`
- `Sahifa X / Y`

---

## 8. JSON eksport

`/export-json/` – saqlangan xabarlarni JSON faylga yozib qo‘yadi (`telegram_messages.json` yoki `utils` ichida ko‘rsatilgan fayl nomi).

---

## 9. Foydali scriptlar

- `get_session.py`  
  – Terminal orqali tez `StringSession` olish uchun (hozirgi oqim web orqali ishlaydi, lekin kerak bo‘lsa qo‘lda ham session yaratish mumkin).

- `session_gen.py`, `session_bot.py`  
  – Eksperimental yoki eski scriptlar; asosiy oqim front orqali telefon-login.

---

## 10. Eslatma

- Bu loyiha **shaxsiy Telegram akkauntingiz** bilan ishlaydi. Telegram ToS qoidalariga rioya qiling.
- Kodni production’da ishlatmoqchi bo‘lsangiz:
  - `DEBUG=False` qiling
  - Ishonchli `SECRET_KEY` qo‘ying
  - Gunicorn / Nginx kabi WSGI server bilan deploy qiling.

