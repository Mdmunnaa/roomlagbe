"""
Bangladesh শহর ও এলাকার তালিকা — location dropdown/autocomplete-এর জন্য।
নতুন শহর/এলাকা দরকার হলে শুধু এই ডিকশনারিতে যোগ করলেই সব জায়গায় (add property,
search filter, homepage popular-area chips) reflect হবে।
"""

BD_CITIES = [
    'Dhaka', 'Chattogram', 'Sylhet', 'Rajshahi', 'Khulna', 'Barishal',
    'Rangpur', 'Mymensingh', 'Gazipur', 'Narayanganj', 'Cumilla', "Cox's Bazar",
]

AREAS_BY_CITY = {
    'Dhaka': [
        'Banani', 'Gulshan 1', 'Gulshan 2', 'Dhanmondi', 'Mirpur 1', 'Mirpur 2',
        'Mirpur 10', 'Mirpur 11', 'Mirpur 12', 'Mirpur DOHS', 'Uttara', 'Mohammadpur',
        'Bashundhara R/A', 'Badda', 'Rampura', 'Motijheel', 'Farmgate', 'Malibagh',
        'Khilgaon', 'Jatrabari', 'Wari', 'Old Dhaka (Puran Dhaka)', 'Shyamoli',
        'Adabor', 'Cantonment', 'Tejgaon', 'Banasree', 'Khilkhet', 'Nikunja',
        'Baridhara', 'Shahbagh', 'Elephant Road', 'Kalabagan', 'Panthapath',
        'Lalmatia', 'Mohakhali', 'Niketan', 'Aftabnagar', 'Shantinagar',
        'Segunbagicha', 'Kakrail', 'Paltan', 'Kawran Bazar', 'Basabo', 'Demra',
    ],
    'Chattogram': [
        'Agrabad', 'Nasirabad', 'GEC Circle', 'Khulshi', 'Halishahar', 'Panchlaish',
        'Chawkbazar', 'Patenga', 'Bayazid', 'Muradpur', 'Oxygen More', 'EPZ', 'Kotwali',
    ],
    'Sylhet': [
        'Zindabazar', 'Amberkhana', 'Shahjalal Upashahar', 'Subid Bazar',
        'Tilagor', 'Airport Road', 'Bandarbazar',
    ],
    'Rajshahi': ['Shaheb Bazar', 'Uposhohor', 'Kazla', 'Talaimari', 'Rajpara'],
    'Khulna': ['Sonadanga', 'Khalishpur', 'Boyra', 'Daulatpur', 'Nirala'],
    'Barishal': ['Band Road', 'Sadar Road', 'Nathullabad'],
    'Rangpur': ['Jahaj Company More', 'Dhap', 'College Road'],
    'Mymensingh': ['Ganginarpar', 'Choto Bazar', 'Town Hall'],
    'Gazipur': ['Tongi', 'Konabari', 'Chandra', 'Board Bazar'],
    'Narayanganj': ['Chashara', 'Dewvog', 'Fatullah'],
    'Cumilla': ['Kandirpar', 'Rajgonj', 'Jhawtala'],
    "Cox's Bazar": ['Kolatoli', 'Laboni Beach', 'Sugandha Beach'],
}

# হোমপেজে "জনপ্রিয় এলাকা" চিপ হিসেবে দেখানোর জন্য (Dhaka-centric, যেহেতু বেশিরভাগ ট্রাফিক ঢাকায়)
POPULAR_AREAS = [
    ('Dhaka', 'Banani'), ('Dhaka', 'Gulshan 1'), ('Dhaka', 'Dhanmondi'),
    ('Dhaka', 'Mirpur 10'), ('Dhaka', 'Uttara'), ('Dhaka', 'Mohammadpur'),
    ('Dhaka', 'Bashundhara R/A'), ('Chattogram', 'Agrabad'),
]


def get_areas_by_city(queryset=None):
    """Curated লিস্ট + (দেওয়া হলে) DB-তে থাকা আসল listing-এর এলাকা merge করে রিটার্ন করে —
    সময়ের সাথে সাথে যেসব নতুন এলাকা host-রা লিখবে সেগুলোও suggestion-এ চলে আসবে।"""
    merged = {city: set(areas) for city, areas in AREAS_BY_CITY.items()}
    if queryset is not None:
        for city, area in queryset.exclude(area='').exclude(city='').values_list('city', 'area').distinct():
            city, area = city.strip(), area.strip()
            merged.setdefault(city, set()).add(area)
    return {city: sorted(areas) for city, areas in merged.items()}
