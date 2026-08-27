from fastapi import FastAPI

app = FastAPI(title="StatusNest")


@app.get("/health")
def health():
    return {"status": "ok"}
