import asyncpg
from asyncpg.exceptions import UndefinedTableError


class PsqlService:
    '''`PsqlService` класс для работы с Postgres
    
    Args:
        connection_string (str): Строка подключения к базе данных PostgreSQL
    
    Methods:
        `__init__(self, connection_string) -> None`
            Конструктор класса PsqlService
            
        `____initialize(self) -> None`
            Проверить создан ли пул соединений

        `fetch(self, query: str, *args) -> list[asyncpg.Record]`
            Выполнить SQL-запрос и вернуть результат
    '''
    
    __slots__ = ('__connection_string', '__pool', '__is_initialized',)


    def __init__(self, connection_string: str) -> None:
        '''Конструктор класса'''
        
        self.__connection_string = connection_string
        self.__pool = None
        self.__is_initialized = False


    async def __initialize(self) -> None:
        '''Проверить создан ли пул соединений
        
        Raises:
            ConnectionError: Если не удалось подключится к базе данных
        '''
        
        if not self.__is_initialized:
            self.__pool = await asyncpg.create_pool(self.__connection_string)
            
            if self.__pool is None:
                raise ConnectionError('Не удалось подключиться к базе данных')
            
            self.__is_initialized = True


    async def fetch(self, query: str, *args) -> list[asyncpg.Record]:
        '''Выполнить SQL-запрос и вернуть результат
        
        Args:
            query (str): SQL-запрос для выполнения
            *args: Параметры для подстановки в SQL-запрос

        Returns:
            list[asyncpg.Record]: Результаты работы метода в виде списка asyncpg.Record
            
        Raises:
            RuntimeError: Если в БД нет необходимых таблиц
        '''
        
        await self.__initialize()
        async with self.__pool.acquire() as conn:
            try:
                result = await conn.fetch(query, *args)
                return result
            except UndefinedTableError as _ex:
                raise RuntimeError("Нет необходимых таблиц") from _ex
