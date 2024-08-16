Запуск
GitHub парсер:

yc serverless function create --name=parser

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
  --environment POSTGRES_PORT=<POSTGRES PORT>


yc serverless trigger create timer \
  --name parser \
  --cron-expression '*/5 * ? * * *' \
  --invoke-function-id <ID функции> \
  --invoke-function-service-account-id <ID сервисного аккаунта>
   