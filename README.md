# Products Manager Plugin

**Comprehensive product and inventory management plugin for CPOS**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/cpos-plugins/cpos-plugin-products)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Django](https://img.shields.io/badge/django-5.1.x-green.svg)](https://www.djangoproject.com/)

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

## 📋 Requirements

- **CPOS**: >= 1.0.0
- **Django**: 5.1.x
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

## 🔗 Links

- **Repository Structure**: Each plugin should have its own GitHub repository
- **Plugin Registry**: https://github.com/cpos-plugins (organization)
- **Documentation**: https://docs.erplora.com/plugins/
