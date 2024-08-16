# Ecomet Test Task

## Тестовое задание состоит из 2х частей:
  1. Github parser в Yandex Cloud
  2. Fast API приложение в Docker контейнере

### Запуск Github parser в Yandex Cloud

1. Создать облачную функцию через Yandex CLI
```console
yc serverless function create --name=parser
```

2. Создать версию облачной функции, если база данных находится не на Yandex Cloud, то убрать параметр --service-account-id, если на Yandex Cloud, то убрать POSTGRES_PASSWORD
```console
yc serverless function version create \
  --function-name=parser \
  --runtime python312 \
  --entrypoint github_parser.handler \
  --memory 128m \
  --execution-timeout 20s \
  --source-path ./parser \
  --service-account-id <ID сервисного аккаунта, убрать если БД находится не на Yandex Cloud> \
  --environment POSTGRES_HOST=<POSTGRES HOST> \
  --environment POSTGRES_USER=<POSTGRES USER> \
  --environment POSTGRES_DATABASE=<POSTGRES DATABASE> \
  --environment GITHUB_TOKEN=<GITHUB Token для парсинга> \
  --environment POSTGRES_PORT=<POSTGRES PORT> \
  --environment POSTGRES_PASSWORD=<POSTGRES PASSWORD, убрать если БД находится на Yandex Cloud, пароль будет получен из контекста сервисного аккаунта> \
  --environment TOP_N_REPOS=<Кол-во репозиториев для парсинга, если не указывать будет равен 100> \
  --environment SINCE_DAYS_ACTIVITY=<Кол-во дней для парсинга активности,если не указывать будет равен 30>
```

3. Создать триггер на каждый час, одного раза в час достаточно, чтобы иметь актуальную информацию о топе репозиториев Github
```console
yc serverless trigger create timer \
  --name parser \
  --cron-expression '0 * ? * * *' \
  --invoke-function-id <ID функции> \
  --invoke-function-service-account-id <ID сервисного аккаунта>
```

### Запуск FastAPI  приложения в Docker контейнере

1. Перейти в каталог с приложением
```console
cd api
```
2. Создать файл src/config/config.yaml и заполнить его по образцу
```console
touch src/config/config.yaml
```
3. Собрать и запустить Docker контейнер с помощью docker compose
```console
docker compose up -d
```
4. Перейти по адресу http://127.0.0.1:8000/docs









   