from fastapi import FastAPI


app = FastAPI(
    title="The Governor",
    description=(
        "Merchant-side transaction governance infrastructure "
        "for agentic commerce."
    ),
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "the-governor",
    }
    