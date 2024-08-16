from datetime import date as date_string

from pydantic import BaseModel,  Field


class TopReposResponseItemScheme(BaseModel):
    '''Pydantic схема ответа на /api/repos/top100'''
    
    repo: str = Field(..., description='Название репозитория')
    owner: str = Field(..., description='Владелец репозитория')
    position_cur: int = Field(..., description='Текущая позиция в топе')
    position_prev: int | None = Field(..., description='Предыдущая позиция в топе')
    stars: int = Field(..., description='Кол-во звезд')
    watchers: int = Field(..., description='Кол-во просмотров')
    forks: int = Field(..., description='Кол-во форков')
    open_issues: int = Field(..., description='Кол-во открытых issues')
    language: str | None = Field(..., description='Язык')


class ActivityResponseScheme(BaseModel):
    '''Pydantic схема ответа на /api/repos/owner/repo'''
    
    date: date_string = Field(..., description='Дата')
    commits: int = Field(..., description='Кол-во  коммитов')
    authors: list[str] = Field(..., description='Авторы коммитов')