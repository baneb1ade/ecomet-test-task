from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from di_container import Container
from controllers import repo_controller


def start_app() -> FastAPI:
    '''Запустить FastAPI приложение
    
    Returns:
        FastAPI: FastAPI приложение
    '''
    
    container = Container()
    container.config.from_yaml('config/config.yaml')
    container.wire(
        modules=[
            repo_controller,
        ]
    )

    app = FastAPI()
    app.include_router(repo_controller.router)
    
    return app


app = start_app()


@app.exception_handler(Exception)
async def internal_errors_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
