from fastapi import FastApi

app = FastApi(
    title="InvoiceTrack",
    description="Personal time-tracking and invoice generation service",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {"status": "ok"}
