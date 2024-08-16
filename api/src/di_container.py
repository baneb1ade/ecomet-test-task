from dependency_injector import containers, providers

from services import PsqlService, RepoService


class Container(containers.DeclarativeContainer):

	config = providers.Configuration()
 
	psql_service = providers.Singleton(
		PsqlService,
		connection_string=config.db_connection_string
	)
	repo_service = providers.Factory(
		RepoService,
		psql_service=psql_service
	)