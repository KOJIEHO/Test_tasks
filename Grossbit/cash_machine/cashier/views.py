import os
import qrcode
import pdfkit
import jinja2
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.views import APIView
from .models import Item
import io


class CashMachineView(APIView):
    def post(self, request, *args, **kwargs):
        item_ids = request.data.get('items', [])

        items = Item.objects.filter(id__in=item_ids)
        total_amount = sum(item.price for item in items)
        context = {
            'items': items,
            'total_amount': total_amount,
            'timestamp': timezone.now().strftime('%d.%m.%Y %H:%M')
        }

        template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(settings.BASE_DIR, 'templates'))
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template('receipt_template.html')
        html = template.render(context)

        pdf_path = os.path.join(settings.MEDIA_ROOT, 'receipt.pdf')
        config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')
        pdfkit.from_string(html, pdf_path, configuration=config)

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        IP = ''
        if IP == '': IP = '127.0.0.1'
        qr.add_data(f'http://{IP}:8000{settings.MEDIA_URL}receipt.pdf')
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return HttpResponse(buffer, content_type='image/png')
