from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import facturacion
from app.config import SERVIDORES

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(facturacion.router)


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("SISTEMA DE FACTURACIÓN DE FIRMAS")
    print("=" * 60)
    print("📡 Servidores configurados:")
    for key, val in SERVIDORES.items():
        estado = "Configurado" if val["url"] and val["token"] else "No configurado"
        print(f"   {estado} {key}: {val['url']}")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)