# Ecomet Test Task(Python=3.11.9)
## Тестовое задание состоит из 2х частей:
  1. Github parser в Yandex Cloud
  2. Fast API приложение в Docker контейнере

### Запуск Github parser в Yandex Cloud

1. Создать облачную функцию через Yandex CLI
```console
yc serverless function create --name=parser
```

2. Создать версию облачной функции
```console
yc serverless function version create \
  --function-name=parser \
  --runtime python312 \
  --entrypoint github_parser.handler \
  --memory 128m \
  --execution-timeout 20s \
  --source-path ./parser \
  --environment POSTGRES_HOST=<POSTGRES HOST> \
  --environment POSTGRES_USER=<POSTGRES USER> \
  --environment POSTGRES_DATABASE=<POSTGRES DATABASE> \
  --environment GITHUB_TOKEN=<GITHUB Token для парсинга> \
  --environment POSTGRES_PORT=<POSTGRES PORT> \
  --environment POSTGRES_PASSWORD=<POSTGRES PASSWORD> \
  --environment TOP_N_REPOS=<Кол-во репозиториев для парсинга, если не указывать будет равен 100> \
  --environment SINCE_DAYS_ACTIVITY=<Кол-во дней для парсинга активности,если не указывать будет равен 30>
```

3. Создать триггер на каждый час, одного раза в час достаточно, чтобы иметь актуальную информацию о топе репозиториев Github. Выставить каждые 5 минут для тестов: '*/5 * ? * * *'
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


### Дополнительная информация:
1. SQL-запросы для создания таблиц
```console
CREATE TABLE Repository (
    repo VARCHAR(255) PRIMARY KEY,
    owner VARCHAR(255) NOT NULL,
    position_cur INTEGER,
    position_prev INTEGER,
    stars INTEGER,
    watchers INTEGER,
    forks INTEGER,
    open_issues INTEGER,
    language VARCHAR(255)
);
```
```console
CREATE TABLE Activity (
    id SERIAL PRIMARY KEY,
    repo VARCHAR(255) REFERENCES Repository(repo) ON DELETE CASCADE,
    date DATE,
    commits INTEGER,
    authors TEXT
);
```
2. Варианты улучшить FastAPI приложение:
  - Добавить Юнит тесты
  - Добавить логирование запросов и ошибок
   