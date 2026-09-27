from django.test import TestCase
from decimal import Decimal
from django.core.exceptions import ValidationError
from .models import Producto


class ProductoTests(TestCase):
    def test_validacion_codigo_unico(self):
        """Verifica que no se pueda crear dos productos con el mismo SKU."""
        Producto.objects.create(
            sku="SKU001", nombre="Test 1", descripcion="Desc",
            precio=Decimal("100.00"), cantidad=10
        )
        prod2 = Producto(
            sku="SKU001", nombre="Test 2", descripcion="Desc 2",
            precio=Decimal("50.00"), cantidad=5
        )
        with self.assertRaises(ValidationError):
            prod2.full_clean()

    def test_validacion_precio_negativo(self):
        """Verifica que no se permita un precio negativo."""
        prod = Producto(
            sku="SKU002", nombre="Test 2", descripcion="Desc",
            precio=Decimal("-10.00"), cantidad=10
        )
        with self.assertRaises(ValidationError):
            prod.full_clean()

    def test_propiedad_bajo_stock(self):
        """Verifica la propiedad bajo_stock cuando la cantidad <= stock_minimo."""
        prod = Producto.objects.create(
            sku="SKU003", nombre="RAM Test", descripcion="Módulo DDR5",
            precio=Decimal("50.00"), cantidad=3, stock_minimo=5
        )
        self.assertTrue(prod.bajo_stock)

        prod.cantidad = 10
        prod.save()
        self.assertFalse(prod.bajo_stock)

    def test_propiedad_valor_total_stock(self):
        """Verifica el cálculo del valor total invertido (precio * cantidad)."""
        prod = Producto.objects.create(
            sku="SKU004", nombre="SSD Test", descripcion="NVMe 1TB",
            precio=Decimal("120.00"), cantidad=5
        )
        self.assertEqual(prod.valor_total_stock, Decimal("600.00"))

    def test_validacion_cantidad_negativa(self):
        """Verifica que no se acepte una cantidad negativa en el formulario."""
        from .forms import ProductoForm
        datos = {
            'sku': 'SKU005',
            'nombre': 'GPU Test',
            'descripcion': 'Tarjeta gráfica',
            'categoria': 'Tarjetas Gráficas',
            'precio': '300.00',
            'cantidad': '-5',
            'stock_minimo': '2',
            'estado': 'Nuevo',
            'activo': True,
        }
        form = ProductoForm(data=datos)
        self.assertFalse(form.is_valid())
        self.assertIn('cantidad', form.errors)
