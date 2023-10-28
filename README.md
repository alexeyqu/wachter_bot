# Wachter Telegram bot

[![Docker prod](https://github.com/alexeyqu/wachter_bot/actions/workflows/publish_production.yml/badge.svg)](https://github.com/alexeyqu/wachter_bot/actions/workflows/publish_production.yml) [![Docker testing](https://github.com/alexeyqu/wachter_bot/actions/workflows/publish_testing.yml/badge.svg)](https://github.com/alexeyqu/wachter_bot/actions/workflows/publish_testing.yml)

<img src="https://github.com/alexeyqu/wachter_bot/assets/7394728/75869909-59fa-4d1b-a829-7737613adf87" alt="telegram logo" height="18px"/> [Вахтёр Бот](https://t.me/wachter_bot)


![photo_2023-10-28_15-36-58](https://github.com/alexeyqu/wachter_bot/assets/7394728/dac59c1b-0868-4bcc-aa07-48944c9a15b8)


## Как добавить в свою группу

1. Добавить в группу.
2. Сделать администратором.
3. Опционально, настроить бота в личном чате.

## Local Development

### Prerequisites 

We are using black to keep our code looking nice and tidy. To make things easier, there's a pre-commit hook which ensures that files to commit are properly formatted. You need to install and initialize pre-commit. Any installation should suffice, one can find pipenv good choice since we use it in this project. After installation run:

```bash
pre-commit install
```

Then will be executed black against changed files in commits.

### Running

1) Set `TELEGRAM_TOKEN` and `TELEGRAM_ERROR_CHAT_ID` environment variable;

2) Run:

```bash
docker-compose -f docker-compose.dev.yml build && docker-compose -f docker-compose.dev.yml up
```
