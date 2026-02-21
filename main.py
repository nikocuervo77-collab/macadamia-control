from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
from inventory_logic import InventoryManager
from reports_logic import ReportManager

app = FastAPI(title="Macadamia Beachwear – Warehouse Control API")

# Inicializar managers
inv_mgr = InventoryManager()
rep_mgr = ReportManager()

# Modelos para la API
class MovementItem(BaseModel):
    barcode: str
    quantity: int

class MovementCreate(BaseModel):
    type_id: str
    user_id: int
    items: List[MovementItem]
    source_wh: Optional[int] = None
    target_wh: Optional[int] = None

# Servir el frontend
@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    with open("index.html", "r") as f:
        return f.read()

# Endpoints de Inventario
@app.post("/api/movements/confirm")
async def create_and_confirm_movement(mov: MovementCreate):
    try:
        # Simplificamos: Creamos draft y confirmamos de inmediato para el modo 'Quick'
        items_dict = [item.dict() for item in mov.items]
        mov_id = inv_mgr.create_draft_movement(
            mov.type_id, mov.user_id, items_dict, mov.source_wh, mov.target_wh
        )
        doc_number = inv_mgr.confirm_movement(mov_id)
        return {"status": "success", "doc_number": doc_number, "id": mov_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/reports/kardex")
async def get_kardex(barcode: Optional[str] = None):
    try:
        filepath = rep_mgr.export_kardex_excel(barcode)
        return FileResponse(filepath, filename=os.path.basename(filepath))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/movement/{mov_id}")
async def get_movement_pdf(mov_id: int):
    try:
        filepath = rep_mgr.export_movement_pdf(mov_id)
        return FileResponse(filepath, filename=os.path.basename(filepath))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Inicializar DB si no existe
    import init_db
    init_db.init_db()
    
    print("Iniciando servidor de despliegue para Macadamia Beachwear...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
