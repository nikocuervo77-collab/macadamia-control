import sqlite3
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os

class ReportManager:
    def __init__(self, db_path="macadamia.db"):
        self.db_path = db_path
        self.reports_dir = "reports"
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_kardex_data(self, product_barcode=None):
        query = """
            SELECT 
                m.confirmed_at as date,
                m.doc_number,
                m.type_id as type,
                mi.product_barcode,
                p.name as product_name,
                CASE 
                    WHEN m.type_id IN ('ENTRY', 'INITIAL_INVENTORY') THEN mi.quantity
                    WHEN m.type_id = 'TRANSFER' AND m.target_warehouse_id IS NOT NULL THEN mi.quantity
                    ELSE 0 
                END as input,
                CASE 
                    WHEN m.type_id = 'EXIT' THEN mi.quantity
                    WHEN m.type_id = 'TRANSFER' AND m.source_warehouse_id IS NOT NULL THEN mi.quantity
                    ELSE 0 
                END as output,
                w_source.name as from_wh,
                w_target.name as to_wh
            FROM movement_items mi
            JOIN movements m ON mi.movement_id = m.id
            JOIN products p ON mi.product_barcode = p.barcode
            LEFT JOIN warehouses w_source ON m.source_warehouse_id = w_source.id
            LEFT JOIN warehouses w_target ON m.target_warehouse_id = w_target.id
            WHERE m.status = 'CONFIRMED'
        """
        if product_barcode:
            query += f" AND mi.product_barcode = '{product_barcode}'"
        query += " ORDER BY m.confirmed_at ASC"
        
        conn = self._get_connection()
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def export_kardex_excel(self, product_barcode=None):
        df = self.get_kardex_data(product_barcode)
        filename = f"kardex_{product_barcode or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        filepath = os.path.join(self.reports_dir, filename)
        df.to_excel(filepath, index=False)
        print(f"Excel generado: {filepath}")
        return filepath

    def export_movement_pdf(self, movement_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Obtener cabecera
        cursor.execute("""
            SELECT m.*, mt.prefix, u.email as user_email, 
                   ws.name as source_name, wt.name as target_name
            FROM movements m
            JOIN movement_types mt ON m.type_id = mt.id
            JOIN users u ON m.user_id = u.id
            LEFT JOIN warehouses ws ON m.source_warehouse_id = ws.id
            LEFT JOIN warehouses wt ON m.target_warehouse_id = wt.id
            WHERE m.id = ?
        """, (movement_id,))
        mov = cursor.fetchone()
        
        # Obtener items
        cursor.execute("""
            SELECT mi.*, p.name as product_name
            FROM movement_items mi
            JOIN products p ON mi.product_barcode = p.barcode
            WHERE mi.movement_id = ?
        """, (movement_id,))
        items = cursor.fetchall()
        conn.close()

        filename = f"comprobante_{mov[1] or movement_id}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        elements = []
        styles = getSampleStyleSheet()

        # Header con info de empresa (Simulado Macadamia Beachwear)
        elements.append(Paragraph("<b>MACADAMIA BEACHWEAR</b>", styles['Title']))
        elements.append(Paragraph("Warehouse Control System", styles['Normal']))
        elements.append(Spacer(1, 12))

        # Movimiento Info
        elements.append(Paragraph(f"Documento: {mov[1]}", styles['Heading2']))
        elements.append(Paragraph(f"Tipo: {mov[2]}", styles['Normal']))
        elements.append(Paragraph(f"Fecha: {mov[8]}", styles['Normal']))
        elements.append(Paragraph(f"Origen: {mov[12] or '-'}", styles['Normal']))
        elements.append(Paragraph(f"Destino: {mov[13] or '-'}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # Tabla de Items
        data = [['Referencia', 'Descripción', 'Cantidad']]
        for item in items:
            data.append([item[2], item[4], item[3]])

        t = Table(data, colWidths=[100, 300, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.teal),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
        
        doc.build(elements)
        print(f"PDF generado: {filepath}")
        return filepath

if __name__ == "__main__":
    rep = ReportManager()
    # Generar un Excel de Kardex total
    rep.export_kardex_excel()
    # Intentar generar PDF del primer movimiento confirmado (si existe)
    try:
        rep.export_movement_pdf(1)
    except:
        pass
