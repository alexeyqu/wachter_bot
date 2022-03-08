FROM python:3.6

RUN pip install "setuptools<46" && pip install pipenv

COPY Pipfile /Pipfile
COPY Pipfile.lock /Pipfile.lock

RUN pipenv install --system

COPY . /app
WORKDIR /app

CMD alembic upgrade head && python wachter/bot.py
