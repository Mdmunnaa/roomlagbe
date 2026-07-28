from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify


class CustomUser(AbstractUser):
    """কাস্টম ইউজার মডেল — Guest, Host, Admin তিনটি রোল"""

    ROLE_CHOICES = [
        ('guest', 'Guest'),
        ('host', 'Host'),
        ('admin', 'Admin'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='guest')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    nid_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="NID Number")
    is_phone_verified = models.BooleanField(default=False)
    is_nid_verified = models.BooleanField(default=False)
    profile_photo = models.ImageField(upload_to='users/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def is_verified_host(self):
        return self.role == 'host' and self.is_phone_verified and self.is_nid_verified


class Property(models.Model):
    """মেইন প্রপার্টি মডেল"""

    TYPE_CHOICES = [
        ('hotel', 'Hotel / Guest House'),
        ('sublet', 'Sublet Room'),
        ('flat', 'Family Flat'),
        ('single', 'Single Room'),
        ('transit', 'Transit Stay (Day Use)'),
    ]

    PRICE_TYPE_CHOICES = [
        ('per_night', 'Per Night'),
        ('per_month', 'Per Month'),
        ('per_hour', 'Per Hour'),
        ('per_day', 'Per Day'),
    ]

    # Basic Info
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='properties')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    property_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField()

    # Location
    area = models.CharField(max_length=100, help_text="যেমন: Banani, Mirpur-10, Uttara")
    city = models.CharField(max_length=100, default='Dhaka')
    full_address = models.TextField()
    google_map_link = models.URLField(blank=True, null=True)

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_type = models.CharField(max_length=15, choices=PRICE_TYPE_CHOICES, default='per_night')

    # Amenities (BooleanField গুলো)
    has_wifi = models.BooleanField(default=False, verbose_name="WiFi")
    has_ac = models.BooleanField(default=False, verbose_name="AC")
    has_attached_bath = models.BooleanField(default=False, verbose_name="Attached Bathroom")
    has_kitchen = models.BooleanField(default=False, verbose_name="Kitchen")
    has_parking = models.BooleanField(default=False, verbose_name="Parking")
    has_lift = models.BooleanField(default=False, verbose_name="Lift")
    has_cctv = models.BooleanField(default=False, verbose_name="CCTV Security")
    is_female_safe = models.BooleanField(default=False, verbose_name="Female Safe Stay")

    # Room Info
    max_guests = models.PositiveIntegerField(default=1)
    total_rooms = models.PositiveIntegerField(default=1)

    # Status & Trust
    is_approved = models.BooleanField(default=False, verbose_name="Admin Approved")
    is_available = models.BooleanField(default=True, verbose_name="Currently Available")
    is_featured = models.BooleanField(default=False, verbose_name="Featured Listing")

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-is_featured', '-created_at']
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title) + '-' + str(self.owner.id)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} — {self.area} ({self.get_property_type_display()})"

    @property
    def whatsapp_link(self):
        """ডায়নামিক WhatsApp বুকিং লিংক"""
        phone = self.owner.phone_number or ''
        message = f"Hi, I want to book '{self.title}' from RoomLagbe. Please confirm availability."
        import urllib.parse
        return f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"

    @property
    def map_embed_url(self):
        """Google Maps embed URL — API key ছাড়াই কাজ করে।
        host যদি নিজে একটা embed-ready google_map_link দিয়ে থাকে সেটাই ব্যবহার হবে,
        নাহলে ঠিকানা (address/area/city) দিয়ে সার্চ-ভিত্তিক embed বানানো হয়।"""
        import urllib.parse
        if self.google_map_link and 'output=embed' in self.google_map_link:
            return self.google_map_link
        query = f"{self.full_address}, {self.area}, {self.city}, Bangladesh"
        return f"https://maps.google.com/maps?q={urllib.parse.quote(query)}&output=embed"

    @property
    def map_link(self):
        """সরাসরি Google Maps-এ খোলার জন্য লিংক (নতুন ট্যাবে)"""
        import urllib.parse
        if self.google_map_link:
            return self.google_map_link
        query = f"{self.full_address}, {self.area}, {self.city}, Bangladesh"
        return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(query)}"

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return None

    @property
    def cover_image(self):
        first = self.images.filter(is_cover=True).first()
        if not first:
            first = self.images.first()
        return first

    def get_confirmed_bookings(self, from_date=None):
        """এই প্রপার্টির CONFIRMED বুকিং রেঞ্জগুলো — ক্যালেন্ডার আর overlap check দুটোতেই ব্যবহার হয়"""
        from django.utils import timezone
        if from_date is None:
            from_date = timezone.localdate()
        return self.inquiries.filter(
            status='confirmed',
            check_in__isnull=False,
            check_out__isnull=False,
            check_out__gte=from_date,
        ).order_by('check_in')

    def is_available_for(self, check_in, check_out, exclude_inquiry_id=None):
        """দেওয়া তারিখ রেঞ্জে প্রপার্টি খালি আছে কিনা (কোনো CONFIRMED বুকিংয়ের সাথে overlap করে না)"""
        if not check_in or not check_out or check_out <= check_in:
            return False
        qs = self.inquiries.filter(
            status='confirmed',
            check_in__lt=check_out,
            check_out__gt=check_in,
        )
        if exclude_inquiry_id:
            qs = qs.exclude(pk=exclude_inquiry_id)
        return not qs.exists()


class PropertyImage(models.Model):
    """প্রপার্টির ছবি — multiple images support"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='properties/')
    caption = models.CharField(max_length=200, blank=True)
    is_cover = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_cover', 'uploaded_at']

    def __str__(self):
        return f"Image for {self.property.title}"


class Review(models.Model):
    """রিভিউ মডেল"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('property', 'reviewer')

    def __str__(self):
        return f"{self.reviewer.username} → {self.property.title} ({self.rating}★)"


class BookingInquiry(models.Model):
    """বুকিং ইনকোয়ারি ট্র্যাক করার জন্য"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='inquiries')
    guest_name = models.CharField(max_length=100)
    guest_phone = models.CharField(max_length=15)
    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.guest_name} → {self.property.title}"

    def clean(self):
        """Double-booking আটকানোর মূল জায়গা — নতুন inquiry, বা কোনো inquiry-কে confirmed করা,
        দুটো ক্ষেত্রেই date-overlap চেক করে।"""
        super().clean()

        if self.check_in and self.check_out and self.check_out <= self.check_in:
            raise ValidationError({'check_out': 'চেক-আউট তারিখ অবশ্যই চেক-ইন তারিখের পরে হতে হবে।'})

        if self.property_id and self.check_in and self.check_out:
            overlapping = BookingInquiry.objects.filter(
                property_id=self.property_id,
                status='confirmed',
                check_in__lt=self.check_out,
                check_out__gt=self.check_in,
            ).exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError(
                    'দুঃখিত! এই তারিখগুলোতে প্রপার্টিটি ইতিমধ্যে বুক করা আছে। অন্য তারিখ বেছে নিন।'
                )


class Conversation(models.Model):
    """একটা প্রপার্টি নিয়ে guest আর host-এর মধ্যে in-app চ্যাট থ্রেড — WhatsApp-এর fallback"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='conversations')
    guest = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='guest_conversations')
    host = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='host_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('property', 'guest')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.guest} ↔ {self.host} ({self.property.title})"

    def other_user(self, current_user):
        return self.host if current_user == self.guest else self.guest

    def unread_count_for(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    """চ্যাট থ্রেডের একটা মেসেজ"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.body[:30]}"
