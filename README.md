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

[!TIP] Флаг `--reload` сообщает Uvicorn, что нужно следить за изменениями в ваших файлах 
и перезагружать их, если они будут обнаружены. Это, наверное, было само собой разумеющимся.