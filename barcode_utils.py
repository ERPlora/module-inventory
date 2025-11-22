"""
Barcode Generation Utilities for Inventory Plugin

This module provides barcode generation functionality using python-barcode library.
Supports Code128 format for SKU-based barcodes.
"""

import io
import barcode
from barcode.writer import SVGWriter


def generate_barcode_svg(sku, format_type='code128'):
    """
    Generate a barcode in SVG format from SKU

    Args:
        sku (str): Product SKU to encode
        format_type (str): Barcode format ('code128' or 'ean13')

    Returns:
        str: SVG content as string

    Raises:
        ValueError: If SKU is invalid for selected format
    """
    try:
        # Select barcode class based on format
        if format_type.lower() == 'code128':
            barcode_class = barcode.get_barcode_class('code128')
        elif format_type.lower() == 'ean13':
            # EAN13 requires exactly 12 or 13 digits
            barcode_class = barcode.get_barcode_class('ean13')
            if not sku.isdigit() or len(sku) not in (12, 13):
                raise ValueError("EAN13 requires 12 or 13 digits")
        else:
            raise ValueError(f"Unsupported barcode format: {format_type}")

        # Generate barcode
        output = io.BytesIO()
        barcode_instance = barcode_class(sku, writer=SVGWriter())
        barcode_instance.write(output, {
            'module_width': 0.3,
            'module_height': 10,
            'font_size': 10,
            'text_distance': 5,
            'quiet_zone': 6.5,
        })

        # Return SVG content
        output.seek(0)
        return output.read().decode('utf-8')

    except Exception as e:
        raise ValueError(f"Error generating barcode: {str(e)}")


def is_valid_sku_for_barcode(sku, format_type='code128'):
    """
    Validate if SKU can be encoded in specified barcode format

    Args:
        sku (str): Product SKU
        format_type (str): Barcode format

    Returns:
        tuple: (bool, str) - (is_valid, error_message)
    """
    if not sku or not sku.strip():
        return False, "SKU cannot be empty"

    sku = sku.strip()

    if format_type.lower() == 'code128':
        # Code128 accepts most ASCII characters
        if len(sku) > 80:
            return False, "SKU too long for Code128 (max 80 characters)"
        return True, ""

    elif format_type.lower() == 'ean13':
        # EAN13 requires exactly 12 or 13 digits
        if not sku.isdigit():
            return False, "EAN13 requires only digits"
        if len(sku) not in (12, 13):
            return False, "EAN13 requires 12 or 13 digits"
        return True, ""

    return False, f"Unsupported format: {format_type}"
