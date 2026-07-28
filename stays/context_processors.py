from django.db.models import Q, Count


def unread_messages(request):
    """নেভবারে ইনবক্স badge দেখানোর জন্য — সব টেমপ্লেটে available থাকবে"""
    if not request.user.is_authenticated:
        return {}
    from .models import Conversation
    result = Conversation.objects.filter(
        Q(guest=request.user) | Q(host=request.user)
    ).aggregate(
        total_unread=Count(
            'messages',
            filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)
        )
    )
    return {'unread_messages_count': result['total_unread'] or 0}
