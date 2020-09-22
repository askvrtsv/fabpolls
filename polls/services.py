from django.utils import timezone

from polls.models import Poll


def is_admin(user) -> bool:
    return user and getattr(user, 'is_admin', False)


def get_all_polls():
    return Poll.objects.all()


def get_published_polls():
    all_polls = get_all_polls()
    return all_polls.filter(is_published=True)


def get_active_polls():
    today = timezone.now().date()
    all_polls = get_all_polls()
    return all_polls.filter(
        start_date__lte=today, finish_date__gte=today)


def get_polls_by_user_perm(is_admin_user: bool):
    if is_admin_user:
        # для админа доступны все опросы
        return get_all_polls()
    # пользователи могут видеть только опубликованные
    return get_published_polls()


def get_poll_user(request):
    result = {}
    try:
        auid = abs(int(request.GET['auid']))
    except (KeyError, ValueError):
        if request.user.is_authenticated:
            result['user'] = request.user
    else:
        result['auid'] = auid
    return result
