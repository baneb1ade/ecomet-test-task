from datetime import date

from fastapi import APIRouter, Depends, Query
from dependency_injector.wiring import inject, Provide

from services import RepoService
from di_container import Container
from schemas import TopReposResponseItemScheme, ActivityResponseScheme


router = APIRouter(tags=['repositories'], prefix='/api/repos')


@router.get('/top100', response_model=list[TopReposResponseItemScheme])
@inject
async def get_top_repos(repo_service: RepoService = Depends(Provide[Container.repo_service])):
    return await repo_service.get_top_repos()


@router.get('/{owner}/{repo}', response_model=list[ActivityResponseScheme])
@inject
async def get_repo_activity(
    owner: str,
    repo: str,
    since: date = Query(None, description='С какой даты отображать активность, формат: YYYY-MM-DD(2024-08-12)'),
    until: date = Query(None, description='До какой даты отображать активность, формат: YYYY-MM-DD(2024-08-15)'),
    repo_service: RepoService = Depends(Provide[Container.repo_service])
):
    return await repo_service.get_repo_activity(owner, repo, since, until)
