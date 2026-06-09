from fastapi import FastAPI


def create_app() -> FastAPI:
    fastapi_app = FastAPI(title="Chronologix API")

    @fastapi_app.get("/health")
    def health_check():
        return {"status": "ok"}

    return fastapi_app


app = create_app()