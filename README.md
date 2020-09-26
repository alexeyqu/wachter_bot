# Wachter Telegram bot

## Как запустить

В корне есть Dockerfile

```bash
$ docker build -t wachter_bot .
$ docker run -e TELEGRAM_TOKEN=<token> wachter_bot
```

## Как добавить в свой чат

1. Добавить в чат
2. Написать whois (минимальная длина 20 символов)
3. Написать боту в лс /start - бот заработает и появятся настройки чата
