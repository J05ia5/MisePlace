from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from inventario.models import Insumo, Proveedor, Compra, Perdida
from inventario.services import registrar_ingreso_compra, registrar_perdida_merma


class InventarioServiciosTestCase(TestCase):
    def setUp(self):
        self.prov = Proveedor.objects.create(nombre='Proveedor Test', telefono='123456')
        self.insumo = Insumo.objects.create(
            nombre='Tomates Test',
            tipo_medicion='peso',
            unidad_medida='kg',
            stock_actual=Decimal('10.00'),
            stock_minimo=Decimal('3.00'),
            stock_objetivo=Decimal('15.00')
        )

    def test_registrar_ingreso_compra_suma_stock(self):
        compra = registrar_ingreso_compra(
            nombre_insumo='Tomates Test',
            unidad_medida='kg',
            cantidad=Decimal('5.00'),
            proveedor_id=self.prov.id,
            fecha_ingreso='2026-10-14',
            precio_compra_total=Decimal('50.00'),
            precio_unidad=Decimal('10.00')
        )

        self.insumo.refresh_from_db()
        self.assertEqual(self.insumo.stock_actual, Decimal('15.00'))
        self.assertEqual(compra.detalles.count(), 1)

    def test_registrar_perdida_descuenta_stock(self):
        perdida = registrar_perdida_merma(
            insumo_id=self.insumo.id,
            cantidad=Decimal('2.50'),
            fecha='2026-10-14',
            observacion='Tomate en mal estado'
        )

        self.insumo.refresh_from_db()
        self.assertEqual(self.insumo.stock_actual, Decimal('7.50'))
        self.assertEqual(perdida.insumo, self.insumo)

    def test_perdida_no_permite_stock_negativo(self):
        with self.assertRaises(ValidationError):
            registrar_perdida_merma(
                insumo_id=self.insumo.id,
                cantidad=Decimal('15.00'),  # Mayor al stock actual de 10.00
                fecha='2026-10-14'
            )

        self.insumo.refresh_from_db()
        self.assertEqual(self.insumo.stock_actual, Decimal('10.00'))
