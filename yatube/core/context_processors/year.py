import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    server_time = datetime.datetime.now()
    return {
        'year': server_time.year
    }
