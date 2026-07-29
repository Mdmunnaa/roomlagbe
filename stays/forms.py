from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Property, BookingInquiry, Review, Message
from .locations import BD_CITIES


class CustomUserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, label="আপনার নাম")
    phone_number = forms.CharField(max_length=15, required=True, label="ফোন নম্বর")
    email = forms.EmailField(required=True, label="ইমেইল")

    class Meta:
        model = CustomUser
        fields = ('first_name', 'username', 'email', 'phone_number', 'password1', 'password2')


class HostRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, label="আপনার নাম")
    phone_number = forms.CharField(max_length=15, required=True, label="ফোন নম্বর")
    nid_number = forms.CharField(max_length=20, required=True, label="NID নম্বর")
    email = forms.EmailField(required=True, label="ইমেইল")
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label="আপনার সম্পর্কে")
    profile_photo = forms.ImageField(required=False, label="প্রোফাইল ছবি")

    class Meta:
        model = CustomUser
        fields = ('first_name', 'username', 'email', 'phone_number', 'nid_number', 'bio', 'profile_photo', 'password1', 'password2')


class PropertyForm(forms.ModelForm):
    city = forms.ChoiceField(
        choices=[('', 'শহর বেছে নিন')] + [(c, c) for c in BD_CITIES],
        label='শহর',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_city'}),
    )

    class Meta:
        model = Property
        exclude = ('owner', 'slug', 'is_approved', 'is_featured', 'views_count', 'created_at', 'updated_at')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'যেমন: Cozy Room in Banani Block C'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'area': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'id_area', 'autocomplete': 'off',
                'list': 'area_datalist', 'placeholder': 'আগে শহর বেছে নিন, তারপর এলাকা লিখুন/বেছে নিন',
            }),
            'full_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'google_map_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Google Maps লিংক (ঐচ্ছিক)'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'মূল্য টাকায়'}),
            'price_type': forms.Select(attrs={'class': 'form-select'}),
            'max_guests': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_rooms': forms.NumberInput(attrs={'class': 'form-control'}),
            'has_wifi': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_ac': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_attached_bath': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_kitchen': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_parking': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_lift': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_cctv': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_female_safe': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': 'প্রপার্টির নাম',
            'property_type': 'ধরন',
            'description': 'বিস্তারিত',
            'area': 'এলাকা',
            'full_address': 'পূর্ণ ঠিকানা',
            'price': 'মূল্য (৳)',
            'price_type': 'মূল্যের ধরন',
            'max_guests': 'সর্বোচ্চ গেস্ট',
            'is_available': 'বর্তমানে খালি আছে',
            'is_female_safe': 'মহিলাদের জন্য নিরাপদ',
        }


class BookingInquiryForm(forms.ModelForm):
    """property=... পাস করে দিলে instance-এ বসিয়ে দেয়, যাতে model.clean()-এর
    date-overlap validation ঠিকমতো কাজ করে (নাহলে property_id না থাকায় চেক স্কিপ হয়ে যায়)।"""

    def __init__(self, *args, property=None, **kwargs):
        self.property = property
        super().__init__(*args, **kwargs)
        if self.property is not None:
            self.instance.property = self.property
        self.fields['check_in'].required = True
        self.fields['check_out'].required = True

    class Meta:
        model = BookingInquiry
        fields = ('guest_name', 'guest_phone', 'check_in', 'check_out', 'message')
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'check_out': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'guest_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guest_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'যেকোনো বিশেষ প্রয়োজনীয়তা লিখুন...'}),
        }
        labels = {
            'guest_name': 'আপনার নাম',
            'guest_phone': 'ফোন নম্বর',
            'check_in': 'চেক-ইন তারিখ',
            'check_out': 'চেক-আউট তারিখ',
            'message': 'বার্তা (ঐচ্ছিক)',
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('rating', 'comment')
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} ★') for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'আপনার অভিজ্ঞতা শেয়ার করুন...'}),
        }
        labels = {
            'rating': 'রেটিং',
            'comment': 'রিভিউ',
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('body',)
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 2, 'class': 'form-control', 'placeholder': 'একটা মেসেজ লিখুন...',
                'autofocus': True,
            }),
        }
        labels = {'body': ''}
