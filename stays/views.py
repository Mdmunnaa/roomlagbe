import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from .models import Property, CustomUser, BookingInquiry, Review, Conversation, Message
from .locations import BD_CITIES, POPULAR_AREAS, get_areas_by_city
from .forms import (
    CustomUserRegistrationForm, HostRegistrationForm,
    PropertyForm, BookingInquiryForm, ReviewForm, MessageForm
)


def home(request):
    """হোমপেজ — সার্চ + ফিল্টার + ফিচার্ড প্রপার্টি"""
    properties = Property.objects.filter(is_approved=True, is_available=True)

    # Search
    query = request.GET.get('q', '')
    prop_type = request.GET.get('type', '')
    city = request.GET.get('city', '')

    if query:
        properties = properties.filter(
            Q(title__icontains=query) |
            Q(area__icontains=query) |
            Q(city__icontains=query)
        )
    if prop_type:
        properties = properties.filter(property_type=prop_type)
    if city:
        properties = properties.filter(city__icontains=city)

    featured = properties.filter(is_featured=True)[:6]
    recent = properties.order_by('-created_at')[:6]
    female_safe = properties.filter(is_female_safe=True)[:4]

    context = {
        'properties': properties,
        'featured': featured,
        'recent': recent,
        'female_safe': female_safe,
        'query': query,
        'prop_type': prop_type,
        'total_count': properties.count(),
        'areas_by_city_json': json.dumps(get_areas_by_city(Property.objects.filter(is_approved=True))),
        'popular_areas': POPULAR_AREAS,
    }
    return render(request, 'stays/home.html', context)


def property_detail(request, slug):
    """প্রপার্টি ডিটেইলস পেজ"""
    property = get_object_or_404(Property, slug=slug, is_approved=True)

    # View count বাড়াও
    property.views_count += 1
    property.save(update_fields=['views_count'])

    # Similar properties
    similar = Property.objects.filter(
        property_type=property.property_type,
        city=property.city,
        is_approved=True
    ).exclude(id=property.id)[:3]

    # Review form
    review_form = ReviewForm()
    if request.method == 'POST' and request.user.is_authenticated:
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.property = property
            review.reviewer = request.user
            review.save()
            messages.success(request, "রিভিউ দেওয়ার জন্য ধন্যবাদ!")
            return redirect('property_detail', slug=slug)

    booked_ranges = [
        {'start': b.check_in.isoformat(), 'end': b.check_out.isoformat()}
        for b in property.get_confirmed_bookings()
    ]

    context = {
        'property': property,
        'similar': similar,
        'review_form': review_form,
        'reviews': property.reviews.all().order_by('-created_at'),
        'booked_ranges_json': json.dumps(booked_ranges),
    }
    return render(request, 'stays/property_detail.html', context)


def search_results(request):
    """সার্চ রেজাল্ট পেজ — city/area (Bikroy-স্টাইল location filter) + amenities filter সহ"""
    properties = Property.objects.filter(is_approved=True, is_available=True)

    query = request.GET.get('q', '')
    city = request.GET.get('city', '')
    area = request.GET.get('area', '')
    prop_type = request.GET.get('type', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    female_safe = request.GET.get('female_safe', '')

    # Amenity checkboxes — যেগুলো model-এ BooleanField হিসেবে আছে
    AMENITY_FIELDS = ['has_wifi', 'has_ac', 'has_attached_bath', 'has_kitchen',
                       'has_parking', 'has_lift', 'has_cctv']
    selected_amenities = [f for f in AMENITY_FIELDS if request.GET.get(f)]

    if query:
        properties = properties.filter(
            Q(title__icontains=query) | Q(area__icontains=query) | Q(city__icontains=query)
        )
    if city:
        properties = properties.filter(city__iexact=city)
    if area:
        properties = properties.filter(area__icontains=area)
    if prop_type:
        properties = properties.filter(property_type=prop_type)
    if min_price:
        properties = properties.filter(price__gte=min_price)
    if max_price:
        properties = properties.filter(price__lte=max_price)
    if female_safe:
        properties = properties.filter(is_female_safe=True)
    for field in selected_amenities:
        properties = properties.filter(**{field: True})

    context = {
        'properties': properties,
        'query': query,
        'city': city,
        'area': area,
        'prop_type': prop_type,
        'total': properties.count(),
        'selected_amenities': selected_amenities,
        'min_price': min_price,
        'max_price': max_price,
        'bd_cities': BD_CITIES,
        'areas_by_city_json': json.dumps(get_areas_by_city(Property.objects.filter(is_approved=True))),
        'amenity_options': [
            ('has_wifi', 'fa-solid fa-wifi', 'WiFi'),
            ('has_ac', 'fa-solid fa-snowflake', 'AC'),
            ('has_attached_bath', 'fa-solid fa-shower', 'Attached Bath'),
            ('has_kitchen', 'fa-solid fa-utensils', 'Kitchen'),
            ('has_parking', 'fa-solid fa-car', 'Parking'),
            ('has_lift', 'fa-solid fa-elevator', 'Lift'),
            ('has_cctv', 'fa-solid fa-camera', 'CCTV'),
        ],
    }
    return render(request, 'stays/search_results.html', context)


def register_guest(request):
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'guest'
            user.save()
            login(request, user)
            messages.success(request, f"স্বাগতম {user.first_name}! আপনার অ্যাকাউন্ট তৈরি হয়েছে।")
            return redirect('home')
    else:
        form = CustomUserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form, 'role': 'guest'})


def register_host(request):
    if request.method == 'POST':
        form = HostRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'host'
            user.save()
            login(request, user)
            messages.success(request, "হোস্ট অ্যাকাউন্ট তৈরি হয়েছে! Admin ভেরিফাই করলে আপনার প্রপার্টি পাবলিশ হবে।")
            return redirect('host_dashboard')
    else:
        form = HostRegistrationForm()
    return render(request, 'registration/register_host.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, "Username বা Password ভুল।")
    return render(request, 'registration/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def host_dashboard(request):
    """হোস্ট ড্যাশবোর্ড"""
    if request.user.role not in ['host', 'admin']:
        messages.error(request, "হোস্ট অ্যাকাউন্ট প্রয়োজন।")
        return redirect('home')

    properties = Property.objects.filter(owner=request.user)
    total_inquiries = BookingInquiry.objects.filter(property__owner=request.user).count()
    pending_inquiries = BookingInquiry.objects.filter(property__owner=request.user, status='pending').count()

    context = {
        'properties': properties,
        'total_properties': properties.count(),
        'approved_count': properties.filter(is_approved=True).count(),
        'pending_count': properties.filter(is_approved=False).count(),
        'total_inquiries': total_inquiries,
        'pending_inquiries': pending_inquiries,
    }
    return render(request, 'stays/host_dashboard.html', context)


@login_required
def add_property(request):
    """নতুন প্রপার্টি যোগ করা"""
    if request.user.role not in ['host', 'admin']:
        messages.error(request, "হোস্ট অ্যাকাউন্ট প্রয়োজন।")
        return redirect('home')

    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property = form.save(commit=False)
            property.owner = request.user
            property.save()

            # ছবি সেভ করা
            images = request.FILES.getlist('images')
            for i, image in enumerate(images):
                from .models import PropertyImage
                PropertyImage.objects.create(
                    property=property,
                    image=image,
                    is_cover=(i == 0)
                )

            messages.success(request, "প্রপার্টি সাবমিট হয়েছে! Admin অ্যাপ্রুভ করলে পাবলিশ হবে।")
            return redirect('host_dashboard')
    else:
        form = PropertyForm()

    return render(request, 'stays/add_property.html', {
        'form': form,
        'areas_by_city_json': json.dumps(get_areas_by_city(Property.objects.filter(is_approved=True))),
    })


@login_required
def edit_property(request, slug):
    property = get_object_or_404(Property, slug=slug, owner=request.user)
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property)
        if form.is_valid():
            form.save()
            messages.success(request, "প্রপার্টি আপডেট হয়েছে!")
            return redirect('host_dashboard')
    else:
        form = PropertyForm(instance=property)
    return render(request, 'stays/add_property.html', {
        'form': form,
        'edit': True,
        'areas_by_city_json': json.dumps(get_areas_by_city(Property.objects.filter(is_approved=True))),
    })


@login_required
def delete_property(request, slug):
    property = get_object_or_404(Property, slug=slug, owner=request.user)
    if request.method == 'POST':
        property.delete()
        messages.success(request, "প্রপার্টি ডিলিট হয়েছে।")
    return redirect('host_dashboard')


def booking_inquiry(request, slug):
    """বুকিং ইনকোয়ারি — ক্যালেন্ডারে booked তারিখ দেখানো + double-booking আটকানো"""
    property = get_object_or_404(Property, slug=slug, is_approved=True)

    if request.method == 'POST':
        form = BookingInquiryForm(request.POST, property=property)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.property = property
            inquiry.save()
            messages.success(request, "বুকিং রিকোয়েস্ট পাঠানো হয়েছে! হোস্ট শীঘ্রই WhatsApp-এ যোগাযোগ করবে।")
            return redirect('property_detail', slug=slug)
        else:
            messages.error(request, "বুকিং রিকোয়েস্ট পাঠানো যায়নি। নিচের error গুলো দেখুন।")
    else:
        form = BookingInquiryForm(property=property)

    booked_ranges = [
        {'start': b.check_in.isoformat(), 'end': b.check_out.isoformat()}
        for b in property.get_confirmed_bookings()
    ]

    context = {
        'form': form,
        'property': property,
        'booked_ranges_json': json.dumps(booked_ranges),
    }
    return render(request, 'stays/booking_inquiry.html', context)


# ---------- In-app Chat (WhatsApp fallback) ----------

@login_required
def start_conversation(request, slug):
    """প্রপার্টির পেজ থেকে 'চ্যাট শুরু করুন' চাপলে এখানে আসে — থাকলে পুরনোটা, না থাকলে নতুন থ্রেড খোলে"""
    property = get_object_or_404(Property, slug=slug, is_approved=True)

    if request.user == property.owner:
        messages.error(request, "নিজের প্রপার্টিতে নিজে চ্যাট শুরু করা যাবে না।")
        return redirect('property_detail', slug=slug)

    conversation, created = Conversation.objects.get_or_create(
        property=property, guest=request.user,
        defaults={'host': property.owner},
    )
    return redirect('conversation_detail', conversation_id=conversation.id)


@login_required
def inbox(request):
    """ইউজারের সব চ্যাট থ্রেড (guest বা host, দুই রোলেই)"""
    conversations = Conversation.objects.filter(
        Q(guest=request.user) | Q(host=request.user)
    ).select_related('property', 'guest', 'host')

    threads = [{
        'conversation': c,
        'other_user': c.other_user(request.user),
        'unread': c.unread_count_for(request.user),
        'last_message': c.messages.last(),
    } for c in conversations]

    return render(request, 'stays/inbox.html', {'threads': threads})


@login_required
def conversation_detail(request, conversation_id):
    """একটা চ্যাট থ্রেড — মেসেজ পাঠানো + দেখা"""
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in (conversation.guest, conversation.host):
        return HttpResponseForbidden("এই চ্যাটে আপনার অ্যাক্সেস নেই।")

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.conversation = conversation
            msg.sender = request.user
            msg.save()
            conversation.save(update_fields=['updated_at'])
            return redirect('conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()

    # অন্যজনের পাঠানো মেসেজগুলো read মার্ক করা
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    context = {
        'conversation': conversation,
        'other_user': conversation.other_user(request.user),
        'chat_messages': conversation.messages.select_related('sender'),
        'form': form,
    }
    return render(request, 'stays/conversation_detail.html', context)


@login_required
def conversation_messages_json(request, conversation_id):
    """হালকা polling endpoint — পেজ রিলোড ছাড়াই নতুন মেসেজ আনার জন্য"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in (conversation.guest, conversation.host):
        return HttpResponseForbidden()

    after_id = request.GET.get('after', 0)
    qs = conversation.messages.filter(id__gt=after_id).select_related('sender')
    qs.exclude(sender=request.user).update(is_read=True)

    data = [{
        'id': m.id,
        'sender_id': m.sender_id,
        'sender_name': m.sender.first_name or m.sender.username,
        'body': m.body,
        'created_at': m.created_at.strftime('%d %b, %I:%M %p'),
        'is_mine': m.sender_id == request.user.id,
    } for m in qs]
    return JsonResponse({'messages': data})
