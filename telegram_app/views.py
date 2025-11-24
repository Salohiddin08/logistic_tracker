import asyncio
import csv

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.dateparse import parse_date

from .models import TelegramSession, Channel, Message, Shipment
from .telethon_client import get_client, get_channels, get_messages
from .utils import save_messages_json, parse_shipment_text

@login_required
def add_session(request):
    # Oddiy forma orqali API ID / HASH / StringSession qabul qilamiz
    if request.method == 'POST':
        api_id = request.POST.get('api_id')
        api_hash = request.POST.get('api_hash')
        string_session = request.POST.get('string_session')

        TelegramSession.objects.create(
            api_id=api_id,
            api_hash=api_hash,
            string_session=string_session
        )
        return redirect('channels')

    default_api_id = getattr(settings, 'TG_API_ID', '')
    default_api_hash = getattr(settings, 'TG_API_HASH', '')

    context = {
        'default_api_id': default_api_id,
        'default_api_hash': default_api_hash,
    }
    return render(request, 'add_session.html', context)


@login_required
def channels_view(request):
    session = TelegramSession.objects.last()
    if not session:
        return redirect('add_session')

    async def run():
        client = await get_client(session.api_id, session.api_hash, session.string_session)
        return await get_channels(client)

    channels = asyncio.run(run())

    return render(request, 'channels.html', {'channels': channels})


@login_required
def fetch_messages_view(request, channel_id):
    session = TelegramSession.objects.last()
    if not session:
        return redirect('add_session')

    async def run():
        client = await get_client(session.api_id, session.api_hash, session.string_session)
        return await get_messages(client, channel_id, limit=100)

    messages = asyncio.run(run())

    channel_obj, _ = Channel.objects.get_or_create(channel_id=channel_id)

    for m in messages:
        msg_obj, _ = Message.objects.get_or_create(
            channel=channel_obj,
            message_id=m.id,
            defaults={
                'sender_id': getattr(m.from_id, 'user_id', None),
                'sender_name': getattr(m.sender, 'username', None) if m.sender else None,
                'text': m.message,
                'date': m.date,
            },
        )

        # Har bir xabar matnidan yuk ma'lumotlarini parslash
        parsed = parse_shipment_text(m.message or "")
        Shipment.objects.update_or_create(
            message=msg_obj,
            defaults={
                'origin': parsed.get('origin'),
                'destination': parsed.get('destination'),
                'cargo_type': parsed.get('cargo_type'),
                'truck_type': parsed.get('truck_type'),
                'payment_type': parsed.get('payment_type'),
                'phone': parsed.get('phone'),
            },
        )

    return redirect('channel_stats', channel_id=channel_id)


@login_required
def saved_messages_view(request):
    """Saqlangan xabarlarni sana bo'yicha filtrlash bilan ko'rsatish."""
    messages = Message.objects.select_related('channel').order_by('-date')

    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    parsed_from = parse_date(date_from) if date_from else None
    parsed_to = parse_date(date_to) if date_to else None

    if parsed_from:
        messages = messages.filter(date__date__gte=parsed_from)
    if parsed_to:
        messages = messages.filter(date__date__lte=parsed_to)

    messages = messages[:200]

    context = {
        'messages': messages,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'messages.html', context)


def _get_filtered_shipments(request, channel_id):
    """Yordamchi funksiya: kanal va sana bo'yicha Shipment querysetini qaytaradi."""
    shipments = Shipment.objects.filter(message__channel__channel_id=channel_id)

    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    parsed_from = parse_date(date_from) if date_from else None
    parsed_to = parse_date(date_to) if date_to else None

    if parsed_from:
        shipments = shipments.filter(message__date__date__gte=parsed_from)
    if parsed_to:
        shipments = shipments.filter(message__date__date__lte=parsed_to)

    return shipments, date_from, date_to



@login_required
def channel_stats_view(request, channel_id):
    """Tanlangan kanal bo'yicha yuk statistikasi (sana filtri bilan)."""
    shipments, date_from, date_to = _get_filtered_shipments(request, channel_id)

    route_stats = (
        shipments
        .values('origin', 'destination')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    cargo_stats = (
        shipments
        .values('cargo_type')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    truck_stats = (
        shipments
        .values('truck_type')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    payment_stats = (
        shipments
        .values('payment_type')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    context = {
        'channel_id': channel_id,
        'total_shipments': shipments.count(),
        'route_stats': route_stats,
        'cargo_stats': cargo_stats,
        'truck_stats': truck_stats,
        'payment_stats': payment_stats,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'stats.html', context)


@login_required
def channel_stats_excel(request, channel_id):
    """Tanlangan kanal bo'yicha yuk ma'lumotlarini (sana filtri bilan) CSV/Excel formatida yuklab berish."""
    shipments, date_from, date_to = _get_filtered_shipments(request, channel_id)

    response = HttpResponse(content_type='text/csv')

    filename_parts = [f"channel_{channel_id}"]
    if date_from:
        filename_parts.append(f"from_{date_from}")
    if date_to:
        filename_parts.append(f"to_{date_to}")
    filename = "_".join(filename_parts) + ".csv"

    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'channel_id', 'channel_title', 'message_id', 'date',
        'origin', 'destination', 'cargo_type', 'truck_type',
        'payment_type', 'phone',
    ])

    for shipment in shipments.select_related('message__channel'):
        msg = shipment.message
        ch = msg.channel
        writer.writerow([
            ch.channel_id,
            ch.title or "",
            msg.message_id,
            msg.date.isoformat() if msg.date else "",
            shipment.origin or "",
            shipment.destination or "",
            shipment.cargo_type or "",
            shipment.truck_type or "",
            shipment.payment_type or "",
            shipment.phone or "",
        ])
    return response



@login_required
def channel_route_messages_view(request, channel_id):
    """Muayyan yo'nalish (origin/destination) bo'yicha xabarlar ro'yxati."""
    shipments, date_from, date_to = _get_filtered_shipments(request, channel_id)

    origin = request.GET.get('origin') or None
    destination = request.GET.get('destination') or None

    if origin:
        shipments = shipments.filter(origin=origin)
    if destination:
        shipments = shipments.filter(destination=destination)

    shipments = shipments.select_related('message__channel').order_by('-message__date')

    context = {
        'channel_id': channel_id,
        'origin': origin,
        'destination': destination,
        'cargo_type': None,
        'date_from': date_from,
        'date_to': date_to,
        'shipments': shipments,
    }
    return render(request, 'route_messages.html', context)


@login_required
def channel_cargo_messages_view(request, channel_id):
    """Muayyan yuk turi bo'yicha xabarlar ro'yxati."""
    shipments, date_from, date_to = _get_filtered_shipments(request, channel_id)

    cargo_type = request.GET.get('cargo_type') or None
    if cargo_type:
        shipments = shipments.filter(cargo_type=cargo_type)

    shipments = shipments.select_related('message__channel').order_by('-message__date')

    context = {
        'channel_id': channel_id,
        'origin': None,
        'destination': None,
        'cargo_type': cargo_type,
        'date_from': date_from,
        'date_to': date_to,
        'shipments': shipments,
    }
    return render(request, 'route_messages.html', context)



@login_required
def export_json(request):
    save_messages_json()
    return HttpResponse("JSON file created successfully!")


@login_required
def logout_view(request):
    """Oddiy GET orqali ham chiqishni qo'llab-quvvatlaydigan logout."""
    logout(request)
    return redirect('login')
