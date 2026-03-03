# Products Manager Plugin

**Comprehensive product and inventory management plugin for CPOS**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/cpos-plugins/cpos-plugin-products)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Django](https://img.shields.io/badge/django-6.0.x-green.svg)](https://www.djangoproject.com/)

## 🌟 Features

- ✅ **Product Management**: Full CRUD operations for products
- ✅ **Category System**: Organize products with customizable categories
- ✅ **Image Support**: Upload images for products and categories with letter fallback
- ✅ **Multi-Language**: Built-in support for English and Spanish
- ✅ **Import/Export**: CSV and Excel support for bulk operations
- ✅ **Stock Management**: Track inventory with low stock alerts
- ✅ **Search & Pagination**: Fast product search with pagination
- ✅ **Profit Calculations**: Automatic profit margin calculations
- ✅ **Avatar System**: Beautiful avatars with image or letter fallback
- ✅ **Barcode Generation**: Generate Code128/EAN13 barcodes for products
- ✅ **Native Printing**: Print barcodes using OS native dialogs in packaged app

## 📋 Requirements

- **CPOS**: >= 1.0.0
- **Django**: 6.0.x
- **Python**: >= 3.10
- **Dependencies**:
  - Pillow >= 10.0.0 (for image processing)
  - openpyxl >= 3.1.0 (for Excel import/export)

## 🚀 Installation

### Via GitHub (Recommended for separate repos)

```bash
cd /path/to/cpos/plugins/
git clone https://github.com/cpos-plugins/cpos-plugin-products.git products
cd products
pip install -r requirements.txt
python ../../manage.py migrate
python ../../manage.py compilemessages
```

## 📦 Barcode Generation & Printing

### Server-Side Barcode Generation

Barcodes are generated server-side using `python-barcode` library with SVG output:

```python
# barcode_utils.py
from barcode import Code128
from barcode.writer import SVGWriter

def generate_barcode_svg(sku, format_type='code128'):
    """Generate SVG barcode from SKU"""
    barcode_class = barcode.get_barcode_class('code128')
    output = io.BytesIO()
    barcode_instance = barcode_class(sku, writer=SVGWriter())
    barcode_instance.write(output, {
        'module_width': 0.3,
        'module_height': 10,
        'font_size': 10,
        'text_distance': 5,
        'quiet_zone': 6.5,
    })
    output.seek(0)
    return output.read().decode('utf-8')
```

**Supported formats:**
- `code128`: Most flexible, accepts alphanumeric (default)
- `ean13`: Requires 12 or 13 digits

### Native Print Support (PyWebView)

When running as packaged app with PyWebView, barcode printing uses native OS dialogs:

**JavaScript Detection:**
```javascript
async function printBarcode(containerId) {
    const svg = container.querySelector('svg');

    // Check if running in pywebview (packaged app)
    if (window.pywebview && window.pywebview.api && window.pywebview.api.print_barcode) {
        // Use native API
        const result = await window.pywebview.api.print_barcode(svg.outerHTML);
        if (result.success) {
            showToast('Barcode sent to printer', 'success');
        }
    } else {
        // Fallback for browser development (window.open + window.print)
        const printWindow = window.open('', '_blank');
        printWindow.document.write(htmlContent);
        printWindow.print();
    }
}
```

**Python API (main.py):**
```python
class WindowAPI:
    def print_barcode(self, svg_content):
        """Open native print dialog with barcode"""
        import tempfile
        import subprocess

        # Create temporary HTML file with SVG
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(f"<html><body>{svg_content}</body></html>")
            temp_path = f.name

        # Open with native browser
        if sys.platform == 'darwin':
            subprocess.run(['open', '-a', 'Safari', temp_path])
        elif sys.platform == 'win32':
            os.startfile(temp_path)
        else:
            subprocess.run(['xdg-open', temp_path])

        return {'success': True, 'message': 'Barcode opened. Use Cmd+P/Ctrl+P to print.'}
```

**Features:**
- ✅ Native OS print dialogs (macOS, Windows, Linux)
- ✅ Automatic fallback to browser method in development
- ✅ No external dependencies required
- ✅ Works with PyInstaller packaged app

## 🔗 Links

- **Repository Structure**: Each plugin should have its own GitHub repository
- **Plugin Registry**: https://github.com/cpos-plugins (organization)
- **Documentation**: https://docs.erplora.com/plugins/
