# hello_async/views.py
import asyncio
import random
from time import sleep
from typing import List

import httpx
from asgiref.sync import sync_to_async
from django.http import HttpResponse


# helpers
from django.shortcuts import render


async def http_call_async():
    for num in range(1, 6):
        await asyncio.sleep(1)
        print(num)
    async with httpx.AsyncClient() as client:
        r = await client.get("https://httpbin.org/")
        print(r)


def http_call_sync():
    for num in range(1, 6):
        sleep(1)
        print(num)
    r = httpx.get("https://httpbin.org/")
    print(r)


# views
async def index(request):
    return render(request, 'hello_async/index.html')


async def async_view(request):
    loop = asyncio.get_event_loop()
    loop.create_task(http_call_async())
    return HttpResponse("Non-blocking HTTP request")


def sync_view(request):
    http_call_sync()
    return HttpResponse("Blocking HTTP request")


async def smoke(smokables: List[str] = None, flavor: str = "Sweet Baby Ray's") -> int:
    """ Smokes some meats and applies the Sweet Baby Ray's """

    for smokable in smokables:
        print(f"Smoking some {smokable}...")
        print(f"Applying the {flavor}...")
        print(f"{smokable.capitalize()} smoked.")

    return len(smokables)


async def get_smokables():
    print("Getting smokeables...")

    await asyncio.sleep(2)
    async with httpx.AsyncClient() as client:
        await client.get("https://httpbin.org/")

        print("Returning smokeable")
        return [
            "ribs",
            "brisket",
            "lemon chicken",
            "salmon",
            "bison sirloin",
            "sausage",
        ]


async def get_flavor():
    print("Getting flavor...")

    await asyncio.sleep(1)
    async with httpx.AsyncClient() as client:
        await client.get("https://httpbin.org/")

        print("Returning flavor")
        return random.choice(
            [
                "Sweet Baby Ray's",
                "Stubb's Original",
                "Famous Dave's",
            ]
        )


async def smoke_some_meats(request):
    results = await asyncio.gather(*[get_smokables(), get_flavor()])
    total = await asyncio.gather(*[smoke(results[0], results[1])])
    return HttpResponse(f"Smoked {total[0]} meats with {results[1]}!")


def oversmoke() -> None:
    """ If it's not dry, it must be uncooked """
    sleep(5)
    print("Who doesn't love burnt meats?")


async def burn_some_meats(request):
    oversmoke()
    return HttpResponse(f"Burned some meats.")


async def async_with_sync_view(request):
    loop = asyncio.get_event_loop()
    async_function = sync_to_async(http_call_sync, thread_sensitive=False)
    loop.create_task(async_function())
    return HttpResponse("Non-blocking HTTP request (via sync_to_async)")
