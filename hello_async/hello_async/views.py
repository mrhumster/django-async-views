# hello_async/views.py

from django.http import HttpResponse


async def index(request):
    return HttpResponse("Hello, async Django")
