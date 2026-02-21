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
class WarehouseCreate(BaseModel):
    name: str
    city: str
    active: Optional[bool] = True

class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    active: Optional[bool] = None

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

@app.get("/api/products/{barcode}")
async def get_product(barcode: str):
    import sqlite3
    # Nota: Usamos sqlite3 directamente por simplicidad, pero lo ideal es usar el manager o SQLAlchemy
    conn = sqlite3.connect("macadamia.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE barcode = ?", (barcode,))
    product = cursor.fetchone()
    conn.close()
    
    if product:
        return dict(product)
    raise HTTPException(status_code=404, detail="Producto no encontrado")

# Endpoints de Bodegas
@app.get("/api/warehouses")
async def get_warehouses():
    import sqlite3
    conn = sqlite3.connect("macadamia.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM warehouses ORDER BY name ASC")
    warehouses = cursor.fetchall()
    conn.close()
    return [dict(w) for w in warehouses]

@app.post("/api/warehouses")
async def create_warehouse(wh: WarehouseCreate):
    import sqlite3
    conn = sqlite3.connect("macadamia.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO warehouses (name, city, active) VALUES (?, ?, ?)", (wh.name, wh.city, wh.active))
    conn.commit()
    wh_id = cursor.lastrowid
    conn.close()
    return {"status": "success", "id": wh_id}

@app.put("/api/warehouses/{wh_id}")
async def update_warehouse(wh_id: int, wh: WarehouseUpdate):
    import sqlite3
    conn = sqlite3.connect("macadamia.db")
    cursor = conn.cursor()
    # Dinámicamente construir el UPDATE
    fields = []
    params = []
    if wh.name is not None:
        fields.append("name = ?")
        params.append(wh.name)
    if wh.city is not None:
        fields.append("city = ?")
        params.append(wh.city)
    if wh.active is not None:
        fields.append("active = ?")
        params.append(wh.active)
    
    if not fields:
        raise HTTPException(status_code=400, detail="Sin campos para actualizar")
    
    params.append(wh_id)
    query = f"UPDATE warehouses SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()
    conn.close()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    # Inicializar DB si no existe
    import init_db
    init_db.init_db()
    
    print("Iniciando servidor de despliegue para Macadamia Beachwear...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
