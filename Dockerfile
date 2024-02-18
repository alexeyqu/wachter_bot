FROM python:3.9

RUN pip install "setuptools<46" && pip install pipenv

COPY Pipfile /Pipfile
COPY Pipfile.lock /Pipfile.lock

RUN pip install "httpcore[asyncio]"

RUN pipenv install --deploy --system

COPY . /app
WORKDIR /app

RUN ["chmod", "+x", "/app/entrypoint.sh"]
ENTRYPOINT ["/app/entrypoint.sh"]
