# Асинхронные представления в Django
[Original post by Jace Medlin](https://testdriven.io/blog/django-async-views/)

## Цели

* Напиши синхронное представление в Django

* Сделай неблокирующий HTTP-запрос в представлении Django

* Упростить основные фоновые задачи с помощью асинхронных представлений Django

* Используй `sync_to_async` для синхронного вызова внутри асинхронного представления

* Обьясни, когда ты должен и не должен использовать асинхронные представления

## Предпосылки

### Зависимости

* Python >= 3.10

* Django >= 4.0

* Uvicorn

* HTTPX

### Что такое ASGI?

ASGI означает асинхронный интерфейс шлюза сервера. Это современное асинхронное продолжение WSGI, 
предоставляющее стандарт для создания асинхронных веб-приложений на основе Python.

Еще одна вещь, о которой стоит упомянуть, это то, что ASGI обратно совместим с WSGI, что делает 
его хорошим предлогом для перехода с сервера WSGI, такого как Gunicorn или uWSGI, на сервер ASGI, 
такой как Uvicorn или Daphne, даже если вы не готовы переключиться на написание асинхронных приложений.

## Создание приложения

```bash
$ mkdir django-async-views && cd django-async-views
$ python3.10 -m venv env
$ source env/bin/activate

(env)$ pip install django
(env)$ django-admin startproject hello_async
```

Django будет запускать ваши асинхронные представления, если вы используете встроенный сервер разработки, 
но на самом деле он не будет запускать их асинхронно, поэтому мы будем запускать Django с Uvicorn.

Установите его:

```bash
(env)$ pip install uvicorn
```

Чтобы запустить ваш проект с Uvicorn, вы используете следующую команду из корня вашего проекта:

```bash
(env)$ uvicorn hello_async.asgi:application
```

Далее давайте создадим наше первое асинхронное представление. Добавьте новый файл для хранения 
представлений в папку «hello_async», а затем добавьте следующее представление:

```python
# hello_async/views.py

from django.http import HttpResponse


async def index(request):
    return HttpResponse("Hello, async Django!")
```
Создание асинхронных представлений в Django так же просто, как создание синхронных представлений — 
все, что вам нужно сделать, это добавить `async` ключевое слово.

Обновите URL-адреса:

```python
# hello_async/urls.py

from django.contrib import admin
from django.urls import path

from hello_async.views import index


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index),
]
```

Теперь в терминале в корневой папке запустите:

```bash
(env)$ uvicorn hello_async.asgi:application --reload
```

> Флаг `--reload` сообщает Uvicorn, что нужно следить за изменениями в ваших файлах 
> и перезагружать их, если они будут обнаружены. Это, наверное, было само собой разумеющимся.

## HTTPX
Стоит отметить, что асинхронная поддержка полностью совместима с предыдущими версиями, 
поэтому вы можете смешивать асинхронные и синхронные представления, промежуточное ПО и 
тесты. Django выполнит каждый в правильном контексте выполнения.

Чтобы продемонстрировать это, добавьте несколько новых представлений:

```python
# hello_async/views.py

import asyncio
from time import sleep

import httpx
from django.http import HttpResponse


# helpers

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
    return HttpResponse("Hello, async Django!")


async def async_view(request):
    loop = asyncio.get_event_loop()
    loop.create_task(http_call_async())
    return HttpResponse("Non-blocking HTTP request")


def sync_view(request):
    http_call_sync()
    return HttpResponse("Blocking HTTP request")
```

Обновите URL-адреса:

```python
# hello_async/urls.py

from django.contrib import admin
from django.urls import path

from hello_async.views import index, async_view, sync_view


urlpatterns = [
    path("admin/", admin.site.urls),
    path("async/", async_view),
    path("sync/", sync_view),
    path("", index),
]
```

Когда сервер запущен, перейдите по адресу http://localhost:8000/async/. 
Вы должны сразу увидеть ответ:

> Non-blocking HTTP request

В вашем терминале вы должны увидеть:

```bash
INFO:     127.0.0.1:60374 - "GET /async/ HTTP/1.1" 200 OK
1
2
3
4
5
<Response [200 OK]>
```

Здесь ответ HTTP отправляется обратно перед первым вызовом сна.

Затем перейдите по адресу http://localhost:8000/sync/. 
Получение ответа должно занять около пяти секунд:

> Blocking HTTP request

Повернитесь к терминалу:

```bash
1
2
3
4
5
<Response [200 OK]>
INFO:     127.0.0.1:60375 - "GET /sync/ HTTP/1.1" 200 OK
```

Здесь ответ HTTP отправляется после завершения цикла и завершения запроса `https://httpbin.org/`.

## Коптим мясо

Чтобы смоделировать более реальный сценарий использования асинхронности, давайте рассмотрим, как 
асинхронно выполнять несколько операций, агрегировать результаты и возвращать их обратно вызывающему 
объекту.

Вернувшись в URLconf вашего проекта, создайте новый путь по адресу `smoke_some_meats`:

```python
# hello_async/urls.py

from django.contrib import admin
from django.urls import path

from hello_async.views import index, async_view, sync_view, smoke_some_meats


urlpatterns = [
    path("admin/", admin.site.urls),
    path("smoke_some_meats/", smoke_some_meats),
    path("async/", async_view),
    path("sync/", sync_view),
    path("", index),
]
```

Вернувшись в представления, создайте новую вспомогательную асинхронную функцию 
с именем `smoke`. Эта функция принимает два параметра: список вызываемых строк 
`smokables` и строку с именем `flavor`. По умолчанию это список копченого мяса 
и «Sweet Baby Ray's» соответственно.

```python
# hello_async/views.py

async def smoke(smokables: List[str] = None, flavor: str = "Sweet Baby Ray's") -> List[str]:
    """ Smokes some meats and applies the Sweet Baby Ray's """

    for smokable in smokables:
        print(f"Smoking some {smokable}...")
        print(f"Applying the {flavor}...")
        print(f"{smokable.capitalize()} smoked.")

    return len(smokables)
```

Затем добавьте еще два асинхронных помощника:

```python
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
```

Создайте асинхронное представление, использующее асинхронные функции:

```python
# hello_async/views.py

async def smoke_some_meats(request):
    results = await asyncio.gather(*[get_smokables(), get_flavor()])
    total = await asyncio.gather(*[smoke(results[0], results[1])])
    return HttpResponse(f"Smoked {total[0]} meats with {results[1]}!")
```

Это представление вызывает функции `get_smokables` и `get_flavor` одновременно. Так `smoke` как зависит от 
результатов обоих `get_smokables` и `get_flavor`, мы обычно `gather` ждали завершения каждой асинхронной задачи.

**Имейте в виду, что в обычном представлении синхронизации `get_smokables` они `get_flavor` будут обрабатываться 
по одному. Кроме того, асинхронное представление приведет к выполнению и позволит обрабатывать другие запросы 
во время обработки асинхронных задач, что позволяет обрабатывать большее количество запросов одним и тем же 
процессом за определенное время.**

Наконец, возвращается ответ, информирующий пользователя о том, что вкусная еда для барбекю готова.

Отлично. Сохраните файл, затем вернитесь в браузер и перейдите по адресу http://localhost:8000/smoke_some_meats/. 

Получение ответа должно занять несколько секунд:

> Smoked 6 meats with Sweet Baby Ray's!

В консоли вы должны увидеть:

```bash
Getting smokeables...
Getting flavor...
Returning flavor
Returning smokeable

Smoking some ribs...
Applying the Stubb's Original...
Ribs smoked.
Smoking some brisket...
Applying the Stubb's Original...
Brisket smoked.
Smoking some lemon chicken...
Applying the Stubb's Original...
Lemon chicken smoked.
Smoking some salmon...
Applying the Stubb's Original...
Salmon smoked.
Smoking some bison sirloin...
Applying the Stubb's Original...
Bison sirloin smoked.
Smoking some sausage...
Applying the Stubb's Original...
Sausage smoked.
INFO:     127.0.0.1:57501 - "GET /smoke_some_meats/ HTTP/1.1" 200 OK
```

## Пригоревшее мясо

### Синхронизация вызова

Вопрос. *Что делать, если вы делаете синхронный вызов внутри асинхронного представления?*

То же самое произойдет, если вы вызовете синхронную функцию из синхронного представления.

Чтобы проиллюстрировать это, создайте новую вспомогательную функцию в файле views.py с именем `oversmoke`.

```python
# hello_async/views.py

def oversmoke() -> None:
    """ If it's not dry, it must be uncooked """
    sleep(5)
    print("Who doesn't love burnt meats?")
```

Очень просто: мы просто синхронно ждем пять секунд.

Создайте представление, которое вызывает эту функцию:

```python
# hello_async/views.py

async def burn_some_meats(request):
    oversmoke()
    return HttpResponse(f"Burned some meats.")
```

Наконец, подключите маршрут в URLconf вашего проекта:

```python
# hello_async/urls.py

from django.contrib import admin
from django.urls import path

from hello_async.views import index, async_view, sync_view, smoke_some_meats, burn_some_meats


urlpatterns = [
    path("admin/", admin.site.urls),
    path("smoke_some_meats/", smoke_some_meats),
    path("burn_some_meats/", burn_some_meats),
    path("async/", async_view),
    path("sync/", sync_view),
    path("", index),
]
```

Посетите маршрут в браузере по адресу http://localhost:8000/burn_some_meats:

> Burned some meats.

Обратите внимание, что потребовалось пять секунд, чтобы наконец получить ответ от браузера. 
Вы также должны были получить вывод консоли одновременно:

```bash
Who doesn't love burnt meats?
INFO:     127.0.0.1:40682 - "GET /burn_some_meats HTTP/1.1" 200 OK
```

Возможно, стоит отметить, что одно и то же произойдет независимо от используемого вами сервера, 
будь то WSGI или ASGI.

### Синхронные и асинхронные вызовы

Вопрос. *Что делать, если вы выполняете синхронный и асинхронный вызов внутри асинхронного представления?*

Не делай этого.

Синхронные и асинхронные представления лучше всего подходят для разных целей. Если у вас есть функция 
блокировки в асинхронном представлении, в лучшем случае это будет не лучше, чем просто использование 
синхронного представления.

## Синхронизировать с асинхронным

Если вам нужно сделать синхронный вызов внутри асинхронного представления (например, для взаимодействия 
с базой данных через ORM Django), используйте sync_to_async в качестве оболочки или декоратора.

Пример:

```python
# hello_async/views.py

async def async_with_sync_view(request):
    loop = asyncio.get_event_loop()
    async_function = sync_to_async(http_call_sync, thread_sensitive=False)
    loop.create_task(async_function())
    return HttpResponse("Non-blocking HTTP request (via sync_to_async)")
```

Вы заметили, что мы установили для `thread_sensitive` параметра значение `False`? Это означает, что 
синхронная функция `http_call_sync` будет выполняться в новом потоке. Просмотрите документы для 
получения дополнительной информации.

Добавьте URL-адрес:

```python
# hello_async/urls.py

from django.contrib import admin
from django.urls import path

from hello_async.views import (
    index,
    async_view,
    sync_view,
    smoke_some_meats,
    burn_some_meats,
    async_with_sync_view
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("smoke_some_meats/", smoke_some_meats),
    path("burn_some_meats/", burn_some_meats),
    path("sync_to_async/", async_with_sync_view),
    path("async/", async_view),
    path("sync/", sync_view),
    path("", index),
]
```

Проверьте это в своем браузере по адресу http://localhost:8000/sync_to_async/.

В вашем терминале вы должны увидеть:

```bash
INFO:     127.0.0.1:34776 - "GET /sync_to_async/ HTTP/1.1" 200 OK
1
2
3
4
5
<Response [200 OK]>
```

## Celery и асинхронные представления

**Нужен ли Celery для асинхронных представлений Django?**

Это зависит.

Асинхронные представления Django предлагают функциональность, аналогичную задаче или очереди сообщений, 
но без сложности. Если вы используете (или рассматриваете) Django и хотите сделать что-то простое (и не 
заботитесь о надежности), асинхронные представления — отличный способ сделать это быстро и легко. Если 
вам нужно выполнять гораздо более тяжелые и длительные фоновые процессы, вы все равно захотите 
использовать Celery или RQ.

Следует отметить, что для эффективного использования асинхронных представлений в представлении должны 
быть только асинхронные вызовы. Очереди задач, с другой стороны, используют воркеры в отдельных 
процессах и поэтому могут выполнять синхронные вызовы в фоновом режиме на нескольких серверах.

Кстати, вы ни в коем случае не должны выбирать между асинхронными представлениями и очередью сообщений — вы 
можете легко использовать их в тандеме. Например: вы можете использовать асинхронное представление для 
отправки электронной почты или внесения одноразовых изменений в базу данных, но заставить Celery очищать 
вашу базу данных в запланированное время каждую ночь или создавать и отправлять отчеты о клиентах.

## Когда использовать

Для новых проектов, если вам нужна асинхронность, используйте асинхронные представления и пишите процессы 
ввода-вывода максимально асинхронно. Тем не менее, если большинству ваших представлений просто нужно сделать 
вызовы к базе данных и выполнить некоторую базовую обработку перед возвратом данных, вы не увидите большого 
увеличения (если оно вообще будет) по сравнению с простым использованием синхронизированных представлений.

Для старых проектов, если у вас практически нет процессов ввода-вывода, придерживайтесь синхронизированных 
представлений. Если у вас есть несколько процессов ввода-вывода, оцените, насколько легко будет переписать 
их асинхронно. Переписать синхронный ввод-вывод в асинхронный непросто, поэтому вы, вероятно, захотите 
оптимизировать свой синхронный ввод-вывод и представления, прежде чем пытаться переписать в асинхронный. 
Кроме того, никогда не стоит смешивать процессы синхронизации с асинхронными представлениями.

В рабочей среде обязательно используйте `Gunicorn` для управления `Uvicorn`, чтобы воспользоваться 
преимуществами как параллелизма (через `Uvicorn`), так и параллелизма (через воркеры `Gunicorn`):

```bash
gunicorn -w 3 -k uvicorn.workers.UvicornWorker hello_async.asgi:application
```

## Вывод
В заключение, хотя это был простой вариант использования, он должен дать вам общее представление о возможностях, 
которые открывают асинхронные представления Django. Некоторые другие вещи, которые можно попробовать в а
синхронных представлениях, — это отправка электронных писем, вызов сторонних API и чтение из/запись в файлы.

Чтобы узнать больше о новой асинхронности Django, смотри эту 
[прекрасную статью](https://wersdoerfer.de/blogs/ephes_blog/django-31-async/), которая охватывает ту же тему, 
а также многопоточность и тестирование.