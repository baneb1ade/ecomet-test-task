import os
import asyncio
from datetime import datetime, timedelta

import aiohttp
import asyncpg


async def check_tables(pool: asyncpg.Pool) -> None:
    '''Проверить наличие нужных таблиц в БД.
    
    Args:
        pool (asyncpg.Pool): Пул соединений с БД.
    '''
    # Проверить наличие таблиц
    check_tables_query = '''
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_name IN ('repository', 'activity')
    '''
    # Создать таблицу repository
    create_repo_query = '''
    CREATE TABLE IF NOT EXISTS repository(
    repo VARCHAR(255) PRIMARY KEY,
    owner VARCHAR(255) NOT NULL,
    position_cur INTEGER,
    position_prev INTEGER,
    stars INTEGER,
    watchers INTEGER,
    forks INTEGER,
    open_issues INTEGER,
    language VARCHAR(255));
    '''

    create_activity_query = '''
    CREATE TABLE IF NOT EXISTS activity(
    id SERIAL PRIMARY KEY,
    repo VARCHAR(255) REFERENCES repository(repo) ON DELETE CASCADE,
    date DATE,
    commits INTEGER,
    authors TEXT);
    '''

    create_table_querys = {
        'repository': create_repo_query, 
        'activity': create_activity_query
    }

    async with pool.acquire() as conn:
        result = await conn.fetch(check_tables_query)

    existing_tables = {record['table_name'] for record in result}

    required_tables = {'repository', 'activity'}
    missing_tables = required_tables - existing_tables

    if missing_tables:
        async with pool.acquire() as conn:
            await conn.execute(create_table_querys['repository'])
            await conn.execute(create_table_querys['activity'])


async def insert_repos(pool: asyncpg.Pool, repos: dict) -> None:
    '''Вставить в БД репозитории.
    
    Args:
        pool (asyncpg.Pool): Пул соединений с БД.
        repos (dict): Данные о репозиториях, полученные из API GitHub.
    '''

    # Получаем текущие данные из базы данных
    select_query = '''
    SELECT repo, position_cur, position_prev FROM repository ORDER BY position_cur;
    '''

    async with pool.acquire() as conn:
        current_data = await conn.fetch(select_query)

    current_data = {record['repo']: dict(record) for record in current_data}

    # Запрос для обновления данных о репозиториях
    update_query = '''
    UPDATE repository
    SET 
        position_cur = $1,
        position_prev = $2,
        stars = $3,
        watchers = $4,
        forks = $5,
        open_issues = $6,
        language = $7
    WHERE repo = $8
    '''

    # Запрос для вставки нового репозитория, если он отсутствует в БД
    insert_query = '''
    INSERT INTO repository(
        repo,
        owner,
        position_cur,
        position_prev,
        stars,
        watchers,
        forks,
        open_issues,
        language
    ) VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)
    '''

    # Перебираем новые данные и обновляем базу данных
    for position_cur, repo in enumerate(repos['items'], start=1):
        repo_name = repo['full_name']

        # Проверяем, есть ли репозиторий в текущих данных
        if repo_name in current_data:
            current_repo = current_data[repo_name]
            position_prev = current_repo['position_cur'] if  current_repo['position_cur'] != position_cur else current_repo['position_prev']

            async with pool.acquire() as conn:
                await conn.execute(
                    update_query,
                    position_cur,
                    position_prev,
                    repo['stargazers_count'],
                    repo['watchers_count'],
                    repo['forks_count'],
                    repo['open_issues_count'],
                    repo['language'],
                    repo_name
                )
        else:
            # Если репозиторий новый, вставляем его в базу данных
            async with pool.acquire() as conn:
                await conn.execute(
                    insert_query,
                    repo_name,
                    repo['owner']['login'],
                    position_cur,
                    None,
                    repo['stargazers_count'],
                    repo['watchers_count'],
                    repo['forks_count'],
                    repo['open_issues_count'],
                    repo['language']
                )


async def insert_commits_activity(pool: asyncpg.Pool, repo_activity: list[dict]) -> None:
    '''Вставить в БД активность репозиториев.'''

    delete_query = '''DELETE FROM activity'''
    insert_query = '''
    INSERT INTO activity(
        repo,
        date,
        commits,
        authors
    ) VALUES($1, $2, $3, $4)
    '''

    values = []
    for item in repo_activity:
        repo = item.pop('repo')
        for key in item.keys():
            date = datetime.strptime(key, '%Y-%m-%d').date()
            commits = item[key]['commits']
            authors = ' | '.join(item[key]['authors'])
            values.append((repo, date, commits, authors))

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(delete_query)
            await conn.executemany(insert_query, values)


async def get_top_repos(token: str, top_n: int = 100) -> dict:
    '''Получить топ N репозиториев с GitHub.
    
    Args:
        top_n (int): Количество репозиториев для выборки (по умолчанию 100).
        token (str): Токен для аутентификации в API GitHub.

    Returns:
        dict: Данные о топе репозиториев.
    '''

    url = 'https://api.github.com/search/repositories'
    params = {
        'q': 'stars:>1',
        'sort': 'stars',
        'per_page': top_n
    }
    headers = {'Authorization': f'token {token}'}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            response.raise_for_status()
            return await response.json()


async def get_commit_activity(repo_full_name: str, token: str, since_days: int) -> dict:
    '''Получить активность репозитория за период.

    Args:
        repo_full_name (str): Полное имя репозитория (например, 'owner/repo').
        token (str): Токен для аутентификации в API GitHub.
        since_days (int): Количество дней для анализа активности.

    Returns:
        dict: Данные об активности репозитория.
    '''

    url = f'https://api.github.com/repos/{repo_full_name}/commits'
    headers = {
        'Authorization': f'token {token}'
    }
    since_date = (datetime.now() - timedelta(days=since_days)).isoformat()
    params = {
        'since': since_date
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()
            commits_data = await response.json()

    repo_activity = {}
    repo_activity['repo'] = repo_full_name

    for commit in commits_data:
        commit_date = commit['commit']['author']['date'][:10]
        author = commit['commit']['author']['name']

        if commit_date not in repo_activity:
            repo_activity[commit_date] = {'commits': 0, 'authors': set()}

        repo_activity[commit_date]['commits'] += 1
        repo_activity[commit_date]['authors'].add(author)

    return repo_activity


async def get_top_repos_activity(top_repos, token: str, since_days: int = 30) -> list[dict]:
    '''Получить активность переданных репозиториев за период.

    Args:
        top_repos (dict): Данные о топовых репозиториях.
        token (str): Токен для аутентификации в API GitHub.
        since_days (int): Количество дней для анализа активности (по умолчанию 30).

    Returns:
        list[dict]: Список данных об активности для каждого репозитория.
    '''

    tasks = []
    for repo in top_repos['items']:
        task = get_commit_activity(repo['full_name'], token, since_days)
        tasks.append(task)

    return await asyncio.gather(*tasks)


def get_env_variable(name: str, default=None) -> str:
    '''Получить переменную окружения.

    Args:
        name (str): Имя переменной окружения.
        default (Optional[str]): Значение по умолчанию, если переменная окружения не найдена.

    Returns:
        str: Значение переменной окружения.

    Raises:
        EnvironmentError: Если переменная окружения не найдена и значение по умолчанию не указано.
    '''

    value = os.getenv(name, default)
    if value is None:
        raise EnvironmentError(f"Environment variable {name} is missing.")
    return value


async def main(password: str) -> None:
    '''Точка входа в парсер.

    Args:
        password (str): Пароль для подключения к БД.
    '''

    github_token = get_env_variable('GITHUB_TOKEN')
    top_n_repos = int(get_env_variable('TOP_N_REPOS', 100))
    since_days_activity = int(get_env_variable('SINCE_DAYS_ACTIVITY', 30))
    
    # Создаем пул соединений к базе данных
    pool = await asyncpg.create_pool(
        user=get_env_variable('POSTGRES_USER'),
        password=password,
        database=get_env_variable('POSTGRES_DATABASE'),
        port=int(get_env_variable('POSTGRES_PORT')),
        host=get_env_variable('POSTGRES_HOST'),
        statement_cache_size=0,
    )

    if pool is None:
        raise ConnectionError('Не удалось подключиться к базе данных')

    # Получаем данные с GitHub
    top_repos = await get_top_repos(github_token, top_n_repos)
    activity = await get_top_repos_activity(
        top_repos=top_repos,
        token=github_token,
        since_days=since_days_activity
    )
    
    # Проверяем наличие таблиц
    await check_tables(pool)
    # Вставляем данные в базу данных
    await insert_repos(pool, top_repos)
    await insert_commits_activity(pool, activity)

    # Закрываем соединение с базой данных
    await pool.close()


def handler(event, context) -> None:
    '''Точка входа в Yandex Cloud Functions.

    Args:
        event (dict): Данные события, переданные в функцию.
        context (dict): Контекст выполнения, содержащий токен аутентификации.
    '''
    
    # Если БД находится в Yandex Cloud - не указывать пароль в переменных окружения и он возьмется
    # из контекста сервисного аккаунта
    password = os.getenv('POSTGRES_PASSWORD') if os.getenv('POSTGRES_PASSWORD') else  context.token['access_token']
    if password is None:
        raise ValueError('Пароль не может быть None')
    
    asyncio.run(main(password))
