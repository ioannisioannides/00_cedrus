import base64
from io import BytesIO

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone

import qrcode
from weasyprint import HTML

from audits.models import Audit


@login_required
@permission_required('audits.view_audit', raise_exception=True)
def generate_audit_report_pdf(request, audit_id):
    """
    Generate a PDF audit report for a specific audit.
    """
    audit = get_object_or_404(Audit, pk=audit_id)
    
    # Gather context data
    context = {
        'audit': audit,
        'summary': getattr(audit, 'summary', None),
        'recommendation': getattr(audit, 'recommendation', None),
        'nonconformities': audit.nonconformity_set.all(),
        'ofis': audit.opportunityforimprovement_set.all(),
        'generated_at': timezone.now(),
        'generated_by': request.user,
    }
    
    # Render HTML template
    html_string = render_to_string('reporting/audit_report.html', context)
    
    # Generate PDF
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf()
    
    # Create HTTP response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"Audit_Report_{audit.organization.name}_{audit.total_audit_date_from}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response

@login_required
@permission_required('audits.view_audit', raise_exception=True)
def generate_certificate_pdf(request, audit_id):
    """
    Generate a PDF certificate for a specific audit.
    """
    audit = get_object_or_404(Audit, pk=audit_id)
    
    # Generate QR Code for verification
    # In a real system, this would point to a public verification URL
    verification_url = request.build_absolute_uri(f"/verify/{audit.id}/")
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    # Calculate expiry date (3 years from decision or audit date)
    # This logic might need to be more complex based on specific rules
    expiry_date = audit.total_audit_date_to.replace(year=audit.total_audit_date_to.year + 3)
    
    context = {
        'audit': audit,
        'certificate_number': f"CERT-{audit.id}-{timezone.now().year}",
        'expiry_date': expiry_date,
        'qr_code': qr_code_base64,
    }
    
    html_string = render_to_string('reporting/certificate.html', context)
    
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf()
    
    # Create HTTP response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"Certificate_{audit.organization.name}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response
