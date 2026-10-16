from fastapi import FastAPI

app = FastAPI(title="Vault API")


@app.get("/health")
def health():
    return {"status": "ok"}
