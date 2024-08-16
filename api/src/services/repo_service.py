from datetime import date
from typing import Optional

from services import PsqlService
from schemas import TopReposResponseItemScheme, ActivityResponseScheme


class RepoService:
    '''`RepoService` класс для работы с данными репозиториев и их активностью
    
    Args:
        psql_service (PsqlService): Экземпляр сервиса для работы с PostgreSQL
    
    Methods:
        `__init__(self, psql_service)`
            Конструктор класса RepoService
        
        `get_top_repos(self) -> list[TopReposResponseItemScheme]`
            Получить список топовых репозиториев
        
        `get_repo_activity(self, owner: str, repo: str, since: Optional[date] = None, until: Optional[date] = None) -> list[ActivityResponseScheme]`
            Получить активность репозитория за указанный период времени
    '''
    
    __slots__ = ('__psql_service',)
    
    def  __init__(self, psql_service: PsqlService) -> None:
        '''Конструктор класса
        
        Args:
            psql_service (PsqlService): Экземпляр сервиса для работы с PostgreSQL
        '''
        
        self.__psql_service = psql_service
    
    
    async def get_top_repos(self) -> list[TopReposResponseItemScheme]:
        '''Получить список ТОП репозиториев
        
        Returns:
            list[TopReposResponseItemScheme]: Список объектов, представляющих топовые репозитории
        '''
        
        query = '''
        SELECT repo, owner, position_cur, position_prev, stars, watchers, forks, open_issues, language
        FROM repository
        ORDER BY position_cur;
        '''
        
        result = await self.__psql_service.fetch(query)
        response = [
            TopReposResponseItemScheme(
                repo=item['repo'],
                owner=item['owner'],
                position_cur=item['position_cur'],
                position_prev=item['position_prev'],
                stars=item['stars'],
                watchers=item['watchers'],
                forks=item['forks'],
                open_issues=item['open_issues'],
                language=item['language']
            )
            for item in result
        ]
        
        return response
    
    
    async def get_repo_activity(
        self, 
        owner: str, 
        repo: str, 
        since: Optional[date] = None, 
        until: Optional[date] = None
    ) -> list[ActivityResponseScheme]:
        '''Получить активность репозитория за указанный период времени
        
        Args:
            owner (str): Владелец репозитория
            repo (str): Название репозитория
            since (Optional[date]): Дата начала периода (включительно)
            until (Optional[date]): Дата конца периода (включительно)
        
        Returns:
            list[ActivityResponseScheme]: Результат работы метода в виде списка ActivityResponseScheme
        '''
        
        repo_full_name = f'{owner}/{repo}'
        query = '''
        SELECT date, commits, authors
        FROM activity
        WHERE repo = $1
        '''
        
        query_params: list  = [repo_full_name]
        if since and until:
            query += ' AND date BETWEEN $2 AND $3'
            query_params.extend([since, until])
        elif since:
            query += ' AND date >= $2'
            query_params.append(since)
        elif until:
            query += ' AND date <= $2'
            query_params.append(until)
        
        result = await self.__psql_service.fetch(query, *query_params)
        
        response = [
            ActivityResponseScheme(
                date=item['date'],
                commits=item['commits'],
                authors=item['authors'].split(' | ')
            )
            for item in result
        ]
        
        return response