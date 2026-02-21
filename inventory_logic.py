import sqlite3
from datetime import datetime

class InventoryManager:
    def __init__(self, db_path="macadamia.db"):
        self.db_path = db_path

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_draft_movement(self, type_id, user_id, items, source_wh=None, target_wh=None):
        """
        Crea un documento en estado DRAFT.
        items: lista de diccionarios [{'barcode': '...', 'quantity': 10}, ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO movements (type_id, user_id, source_warehouse_id, target_warehouse_id, status) VALUES (?, ?, ?, ?, 'DRAFT')",
                (type_id, user_id, source_wh, target_wh)
            )
            movement_id = cursor.lastrowid

            for item in items:
                cursor.execute(
                    "INSERT INTO movement_items (movement_id, product_barcode, quantity) VALUES (?, ?, ?)",
                    (movement_id, item['barcode'], item['quantity'])
                )
            
            conn.commit()
            return movement_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def confirm_movement(self, movement_id):
        """
        Confirma un movimiento, actualiza stock y genera numeración.
        Implementa validación de stock negativo y bloqueo de edición.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # 1. Obtener datos del movimiento y validar estado
            cursor.execute("SELECT * FROM movements WHERE id = ?", (movement_id,))
            mov = cursor.fetchone()
            if not mov:
                raise ValueError("Movimiento no encontrado.")
            if mov['status'] == 'CONFIRMED':
                raise ValueError("El documento ya está confirmado y no se puede modificar.")

            # 2. Obtener items
            cursor.execute("SELECT * FROM movement_items WHERE movement_id = ?", (movement_id,))
            items = cursor.fetchall()

            # 3. Procesar lógica de stock según tipo
            type_id = mov['type_id']
            source_wh = mov['source_warehouse_id']
            target_wh = mov['target_warehouse_id']

            for item in items:
                barcode = item['product_barcode']
                qty = item['quantity']

                # Lógica de Salida (Salida, Transferencia, Ajuste negativo)
                if type_id in ['EXIT', 'TRANSFER', 'ADJUSTMENT']:
                    if source_wh:
                        self._update_stock(cursor, source_wh, barcode, -qty)

                # Lógica de Entrada (Entrada, Transferencia, Ajuste positivo, Inventario Inicial)
                if type_id in ['ENTRY', 'TRANSFER', 'ADJUSTMENT', 'INITIAL_INVENTORY']:
                    if target_wh:
                        self._update_stock(cursor, target_wh, barcode, qty)

            # 4. Generar numeración automática
            cursor.execute("SELECT prefix FROM movement_types WHERE id = ?", (type_id,))
            prefix = cursor.fetchone()['prefix']
            
            cursor.execute("SELECT COUNT(*) FROM movements WHERE type_id = ? AND status = 'CONFIRMED'", (type_id,))
            count = cursor.fetchone()[0] + 1
            doc_number = f"{prefix}-{str(count).zfill(5)}"

            # 5. Actualizar estado del documento
            cursor.execute(
                "UPDATE movements SET status = 'CONFIRMED', doc_number = ?, confirmed_at = ? WHERE id = ?",
                (doc_number, datetime.now().isoformat(), movement_id)
            )

            conn.commit()
            print(f"Movimiento {movement_id} confirmado exitosamente como {doc_number}.")
            return doc_number

        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "CHECK constraint failed: positive_stock" in str(e):
                raise ValueError("Error: Operación cancelada. El stock resultante no puede ser negativo.")
            raise e
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _update_stock(self, cursor, warehouse_id, barcode, quantity_change):
        # Asegurar que el registro de inventario exista
        cursor.execute(
            "INSERT OR IGNORE INTO inventory (warehouse_id, product_barcode, quantity) VALUES (?, ?, 0)",
            (warehouse_id, barcode)
        )
        # Actualizar cantidad (El CONSTRAINT en la DB lanzará error si el resultado es < 0)
        cursor.execute(
            "UPDATE inventory SET quantity = quantity + ? WHERE warehouse_id = ? AND product_barcode = ?",
            (quantity_change, warehouse_id, barcode)
        )

# --- Script de Prueba ---
if __name__ == "__main__":
    mgr = InventoryManager()
    
    # Setup inicial para pruebas
    conn = sqlite3.connect("macadamia.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO warehouses (id, name, city) VALUES (1, 'Bodega Central', 'Bogotá')")
    c.execute("INSERT OR IGNORE INTO warehouses (id, name, city) VALUES (2, 'Bodega Norte', 'Medellín')")
    c.execute("INSERT OR IGNORE INTO products (barcode, name) VALUES ('PROD001', 'Macadamia Original')")
    # Asegurarnos de tener un usuario
    c.execute("SELECT id FROM users LIMIT 1")
    user_id = c.fetchone()[0]
    conn.commit()
    conn.close()

    try:
        print("\n--- TEST 1: Entrada de Stock ---")
        mov_id = mgr.create_draft_movement('ENTRY', user_id, [{'barcode': 'PROD001', 'quantity': 100}], target_wh=1)
        mgr.confirm_movement(mov_id)

        print("\n--- TEST 2: Intento de salida mayor al stock (Debe fallar) ---")
        mov_id_fail = mgr.create_draft_movement('EXIT', user_id, [{'barcode': 'PROD001', 'quantity': 150}], source_wh=1)
        try:
            mgr.confirm_movement(mov_id_fail)
        except ValueError as e:
            print(f"Validación correcta: {e}")

        print("\n--- TEST 3: Transferencia exitosa ---")
        mov_id_tra = mgr.create_draft_movement('TRANSFER', user_id, [{'barcode': 'PROD001', 'quantity': 50}], source_wh=1, target_wh=2)
        mgr.confirm_movement(mov_id_tra)

        # Verificar resultados finales
        conn = sqlite3.connect("macadamia.db")
        print("\n--- Stock Final ---")
        stocks = conn.execute("SELECT warehouse_id, product_barcode, quantity FROM inventory").fetchall()
        for s in stocks:
            print(f"Bodega {s[0]} | Producto {s[1]} | Cantidad: {s[2]}")
        conn.close()

    except Exception as e:
        print(f"Error inesperado: {e}")
