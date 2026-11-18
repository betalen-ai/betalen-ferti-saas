from fastapi import FastAPI
from app.routes import products
from app.routes import warehouses
from app.routes import stock

app = FastAPI(title="beta_inventory", version="0.1.0")

app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(warehouses.router, prefix="/warehouses", tags=["warehouses"])
app.include_router(stock.router, prefix="/stock", tags=["stock"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "beta_inventory"}