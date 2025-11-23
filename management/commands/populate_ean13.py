from django.core.management.base import BaseCommand
from inventory.models import Product
import random


class Command(BaseCommand):
    help = 'Populate EAN-13 codes for all products that do not have one'

    def generate_ean13(self):
        """Generate a valid EAN-13 barcode with check digit"""
        # Generate 12 random digits
        code = ''.join([str(random.randint(0, 9)) for _ in range(12)])

        # Calculate check digit
        odd_sum = sum(int(code[i]) for i in range(0, 12, 2))
        even_sum = sum(int(code[i]) for i in range(1, 12, 2))
        total = odd_sum + (even_sum * 3)
        check_digit = (10 - (total % 10)) % 10

        return code + str(check_digit)

    def handle(self, *args, **options):
        products = Product.objects.filter(ean13__isnull=True) | Product.objects.filter(ean13='')
        count = products.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('All products already have EAN-13 codes'))
            return

        self.stdout.write(f'Found {count} products without EAN-13 codes')

        updated = 0
        for product in products:
            # Generate unique EAN-13
            max_attempts = 100
            for _ in range(max_attempts):
                ean13 = self.generate_ean13()
                if not Product.objects.filter(ean13=ean13).exists():
                    product.ean13 = ean13
                    product.save()
                    updated += 1
                    self.stdout.write(f'  ✓ {product.name} ({product.sku}): {ean13}')
                    break
            else:
                self.stdout.write(self.style.WARNING(f'  ✗ Could not generate unique EAN-13 for {product.name}'))

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully updated {updated} products'))
