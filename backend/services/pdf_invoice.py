from io import BytesIO
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm

from domain.admin import MonthlyInvoice, CostCentre

def generate_invoice_pdf(invoice: MonthlyInvoice, cost_centre: CostCentre) -> bytes:
    """
    Generate a PDF invoice for a monthly invoice record.
    Returns: Bytes of the PDF file.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Configuration
    margin = 20 * mm
    line_height = 6 * mm
    primary_color = colors.HexColor("#2563eb") # Blue-600
    
    # --- HEADER ---
    c.setFillColor(primary_color)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(margin, height - margin - 10 * mm, "FLOWBOT HUB")
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawString(margin, height - margin - 18 * mm, "Automated Platform Invoice")
    
    # Invoice Label
    c.setFont("Helvetica-Bold", 30)
    c.drawRightString(width - margin, height - margin - 10 * mm, "INVOICE")
    
    # --- DETAILS BOX ---
    y = height - 60 * mm
    
    # Left Side: Bill To
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Bill To:")
    y -= line_height
    c.setFont("Helvetica", 11)
    c.drawString(margin, y, cost_centre.name)
    y -= line_height
    c.drawString(margin, y, f"Code: {cost_centre.code}")
    y -= line_height
    if cost_centre.is_overhead:
        c.setFillColor(colors.gray)
        c.drawString(margin, y, "(Overhead)")
        c.setFillColor(colors.black)
    
    # Right Side: Invoice Details
    y = height - 60 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - margin, y, "Invoice Details")
    y -= line_height
    
    details = [
        ("Invoice Date:", datetime.now().strftime("%Y-%m-%d")),
        ("Period:", invoice.year_month),
        ("Invoice #:", f"INV-{invoice.year_month.replace('-', '')}-{invoice.cost_centre_id:03d}"),
    ]
    
    c.setFont("Helvetica", 11)
    for label, value in details:
        c.drawRightString(width - margin - 40 * mm, y, label)
        c.drawRightString(width - margin, y, value)
        y -= line_height
        
    # --- TABLE ---
    y = height - 110 * mm
    
    # Header
    c.setFillColor(colors.lightgrey)
    c.rect(margin, y, width - 2 * margin, 10 * mm, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    
    col_desc = margin + 5 * mm
    col_amount = width - margin - 5 * mm
    
    c.drawString(col_desc, y + 3 * mm, "Description")
    c.drawRightString(col_amount, y + 3 * mm, "Amount (£)")
    
    # Rows
    y -= 10 * mm
    c.setFont("Helvetica", 11)
    
    items = [
        ("Platform Utilization Cost", invoice.utilization_cost),
        ("Data Storage Cost", invoice.storage_cost),
    ]
    
    total = 0
    for desc, amount in items:
        # Alternating bg could go here
        c.drawString(col_desc, y + 3 * mm, desc)
        c.drawRightString(col_amount, y + 3 * mm, f"{amount:.2f}")
        c.line(margin, y, width - margin, y) # Bottom line
        total += amount
        y -= 10 * mm
        
    # --- TOTAL ---
    y -= 5 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(col_amount - 40 * mm, y, "Total:")
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(col_amount, y, f"£{invoice.total_cost:.2f}")
    
    # --- USAGE BREAKDOWN (If available) ---
    if invoice.details_json:
        try:
            data = json.loads(invoice.details_json)
            usage = data.get("usage", {})
            storage = data.get("storage", {})
            
            y -= 30 * mm
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margin, y, "Usage Breakdown")
            y -= line_height
            c.setFont("Helvetica", 9)
            
            # Module Usage
            request_count = usage.get("request_count", 0)
            c.drawString(margin, y, f"Total API Requests: {request_count}")
            y -= line_height
            
            # Storage
            storage_mb = storage.get("total_bytes", 0) / (1024 * 1024)
            projects = storage.get("project_count", 0)
            c.drawString(margin, y, f"Storage Consumed: {storage_mb:.2f} MB across {projects} projects")
            
        except:
            pass
            
    # --- FOOTER ---
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.gray)
    c.drawCentredString(width / 2, 10 * mm, f"FlowBot Hub | Cost Allocation Automated Report | Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer.getvalue()
