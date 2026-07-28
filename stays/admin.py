from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from .models import CustomUser, Property, PropertyImage, Review, BookingInquiry, Conversation, Message


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'role', 'phone_number', 'is_phone_verified', 'is_nid_verified', 'date_joined')
    list_filter = ('role', 'is_phone_verified', 'is_nid_verified', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    list_editable = ('is_phone_verified', 'is_nid_verified')

    fieldsets = UserAdmin.fieldsets + (
        ('RoomLagbe Info', {
            'fields': ('role', 'phone_number', 'nid_number', 'is_phone_verified', 'is_nid_verified', 'profile_photo', 'bio')
        }),
    )


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3
    fields = ('image', 'caption', 'is_cover')


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'owner', 'property_type', 'area', 'city',
        'price', 'price_type', 'is_approved', 'is_available',
        'is_featured', 'is_female_safe', 'created_at'
    )
    list_filter = ('property_type', 'city', 'is_approved', 'is_available', 'is_featured', 'is_female_safe')
    search_fields = ('title', 'area', 'city', 'owner__username', 'owner__phone_number')
    list_editable = ('is_approved', 'is_available', 'is_featured')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PropertyImageInline]
    readonly_fields = ('views_count', 'created_at', 'updated_at')

    fieldsets = (
        ('Basic Info', {
            'fields': ('owner', 'title', 'slug', 'property_type', 'description')
        }),
        ('Location', {
            'fields': ('area', 'city', 'full_address', 'google_map_link')
        }),
        ('Pricing', {
            'fields': ('price', 'price_type')
        }),
        ('Amenities', {
            'fields': (
                'has_wifi', 'has_ac', 'has_attached_bath', 'has_kitchen',
                'has_parking', 'has_lift', 'has_cctv', 'is_female_safe'
            ),
            'classes': ('collapse',)
        }),
        ('Room Details', {
            'fields': ('max_guests', 'total_rooms')
        }),
        ('Status', {
            'fields': ('is_approved', 'is_available', 'is_featured')
        }),
        ('Stats', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def approve_properties(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} property/properties approved.")
    approve_properties.short_description = "✅ Approve selected properties"

    def unapprove_properties(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} property/properties unapproved.")
    unapprove_properties.short_description = "❌ Unapprove selected properties"

    actions = ['approve_properties', 'unapprove_properties']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('property', 'reviewer', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('property__title', 'reviewer__username')


@admin.register(BookingInquiry)
class BookingInquiryAdmin(admin.ModelAdmin):
    list_display = ('guest_name', 'guest_phone', 'property', 'status', 'check_in', 'check_out', 'created_at')
    list_filter = ('status',)
    search_fields = ('guest_name', 'guest_phone', 'property__title')
    actions = ['mark_confirmed', 'mark_cancelled']

    def mark_confirmed(self, request, queryset):
        """Confirm করার আগে date-conflict চেক করে — double booking আটকানোর জায়গা"""
        confirmed, skipped = 0, []
        for inquiry in queryset:
            inquiry.status = 'confirmed'
            try:
                inquiry.full_clean()
                inquiry.save()
                confirmed += 1
            except ValidationError:
                skipped.append(f"{inquiry.guest_name} ({inquiry.check_in} → {inquiry.check_out})")

        if confirmed:
            self.message_user(request, f"✅ {confirmed}টি বুকিং কনফার্ম করা হয়েছে।")
        if skipped:
            self.message_user(
                request,
                "⚠️ এই তারিখগুলোতে আগে থেকেই CONFIRMED বুকিং আছে, তাই confirm করা যায়নি: " + ", ".join(skipped),
                level=messages.ERROR,
            )
    mark_confirmed.short_description = "✅ Confirm selected (তারিখ conflict চেক সহ)"

    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f"{queryset.count()}টি বুকিং বাতিল করা হয়েছে।")
    mark_cancelled.short_description = "❌ Cancel selected bookings"


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'body', 'is_read', 'created_at')
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('property', 'guest', 'host', 'created_at', 'updated_at')
    search_fields = ('property__title', 'guest__username', 'host__username')
    inlines = [MessageInline]


# Admin site customization
admin.site.site_header = "🏠 RoomLagbe Admin"
admin.site.site_title = "RoomLagbe"
admin.site.index_title = "Dashboard"
