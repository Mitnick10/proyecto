from io import BytesIO
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
<<<<<<< HEAD
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
=======
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
import os
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
>>>>>>> 19bc0b42141dc9139c457364af8c7d05a8913cbc
from reportlab.lib.units import inch
from datetime import datetime

def generar_listado_pdf(becas):
    """
    Genera un PDF con el listado de atletas filtrados.
    Retorna un objeto BytesIO con el contenido del archivo PDF.
    Campos: Nombre, Cédula, Cuenta Bancaria, Tipo de Beca, Disciplina.
    """
    buffer = BytesIO()
    
    # Configurar documento (Landscape para más espacio horizontal)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
        title="Listado de Atletas"
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # --- ESTILOS ---
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=14,
        leading=18,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Heading2'],
        alignment=TA_CENTER,
        fontSize=11,
        leading=14,
        textColor=colors.grey,
        spaceAfter=20
    )
<<<<<<< HEAD
=======

    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        alignment=TA_LEFT
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.white,
        fontName='Helvetica-Bold'
    )
>>>>>>> 19bc0b42141dc9139c457364af8c7d05a8913cbc
    
    # --- ENCABEZADO ---
    elements.append(Paragraph("REPUBLICA BOLIVARIANA DE VENEZUELA", title_style))
    elements.append(Paragraph("INSTITUTO REGIONAL DE DEPORTES DEL ESTADO BOLIVARIANO DE GUÁRICO", title_style))
    elements.append(Paragraph("PROGRAMA BECAS DEPORTIVAS", title_style))
    
    fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"Reporte generado el: {fecha_hoy}", subtitle_style))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # --- TABLA ---
    # Encabezados
<<<<<<< HEAD
    headers = ["Nombre Completo", "Cédula", "Cuenta Bancaria", "Tipo de Beca", "Disciplina"]
=======
    headers = [
        Paragraph("Nombre Completo", header_style),
        Paragraph("Cédula", header_style),
        Paragraph("Cuenta Bancaria", header_style),
        Paragraph("Tipo de Beca", header_style),
        Paragraph("Disciplina", header_style)
    ]
>>>>>>> 19bc0b42141dc9139c457364af8c7d05a8913cbc
    
    # Datos
    data = [headers]
    
    for b in becas:
        nombre_completo = f"{b.get('nombre', '')} {b.get('apellido', '')}".upper().strip()
        cedula = b.get('cedula', '')
        cuenta = b.get('cuenta_bancaria', '') or "No registrada"
        tipo = b.get('tipo_beca', '') or "Sin asignar"
        disciplina = b.get('disciplina', '')
        
<<<<<<< HEAD
        row = [nombre_completo, cedula, cuenta, tipo, disciplina]
        data.append(row)
        
    if not becas:
        data.append(["No se encontraron registros para este filtro.", "", "", "", ""])
=======
        row = [
            Paragraph(nombre_completo, cell_style),
            Paragraph(cedula, cell_style),
            Paragraph(cuenta, cell_style),
            Paragraph(tipo, cell_style),
            Paragraph(disciplina, cell_style)
        ]
        data.append(row)
        
    if not becas:
        data.append([
            Paragraph("No se encontraron registros para este filtro.", cell_style),
            "", "", "", ""
        ])
>>>>>>> 19bc0b42141dc9139c457364af8c7d05a8913cbc

    # Crear Tabla
    # Ajustar anchos de columna (Total ancho aprox page width - margins = ~10 inches = ~720 pts)
    # page width landscape letter = 11 inch = 792 pts. Margins 30+30=60. Usable = 732.
    col_widths = [200, 80, 160, 120, 120] 
    
    table = Table(data, colWidths=col_widths, repeatRows=1)
    
    # Estilos de Tabla
    style = TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')), # Blue 800
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Cuerpo
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Alternar colores de fila (Zebra striping)
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
    ])
    
    table.setStyle(style)
    
    elements.append(table)
    
    # --- FOOTER ---
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(f"Total de registros: {len(becas)}", subtitle_style))
    
    # Construir PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer
<<<<<<< HEAD
=======


>>>>>>> 19bc0b42141dc9139c457364af8c7d05a8913cbc
