from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import Usuario
from inventario.models import Insumo, Proveedor
from recetas.models import Plato, RecetaIngrediente
from ventas.models import Venta
from ventas.services import procesar_venta_atomic


class VentasYStockTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Crear usuarios para cada rol
        self.admin = Usuario.objects.create_user(
            email='admin@test.com',
            password='Password123!',
            rol=Usuario.Rol.ADMINISTRADOR
        )
        self.cajero = Usuario.objects.create_user(
            email='cajero@test.com',
            password='Password123!',
            rol=Usuario.Rol.CAJERO
        )
        self.empleado = Usuario.objects.create_user(
            email='empleado@test.com',
            password='Password123!',
            rol=Usuario.Rol.EMPLEADO
        )

        # Insumos de prueba
        self.pan = Insumo.objects.create(
            nombre='Pan de prueba',
            tipo_medicion='unidad',
            unidad_medida='und',
            stock_actual=Decimal('10.00'),
            stock_minimo=Decimal('5.00'),
            stock_objetivo=Decimal('10.00')
        )
        self.carne = Insumo.objects.create(
            nombre='Carne de prueba',
            tipo_medicion='peso',
            unidad_medida='kg',
            stock_actual=Decimal('2.00'),
            stock_minimo=Decimal('1.00'),
            stock_objetivo=Decimal('5.00')
        )

        # Plato y Receta: Hamburguesa (2 panes, 0.20 kg carne)
        self.burger = Plato.objects.create(
            nombre='Hamburguesa Test',
            precio_venta=Decimal('30.00'),
            activo=True
        )
        RecetaIngrediente.objects.create(
            plato=self.burger,
            insumo=self.pan,
            cantidad_necesaria=Decimal('2.00')
        )
        RecetaIngrediente.objects.create(
            plato=self.burger,
            insumo=self.carne,
            cantidad_necesaria=Decimal('0.20')
        )

    def test_venta_exitosa_descuenta_stock_atomico(self):
        """Verifica que una venta de 2 hamburguesas descuenta 4 panes y 0.40 kg carne."""
        items = [{'id': self.burger.id, 'cantidad': 2, 'observacion': 'Sin cebolla'}]
        venta = procesar_venta_atomic(items, 'Efectivo', usuario=self.cajero)

        self.assertEqual(venta.total_venta, Decimal('60.00'))
        self.assertEqual(venta.detalles.count(), 1)
        self.assertEqual(venta.detalles.first().observacion, 'Sin cebolla')

        # Recargar stock desde BD
        self.pan.refresh_from_db()
        self.carne.refresh_from_db()

        self.assertEqual(self.pan.stock_actual, Decimal('6.00'))  # 10 - 4
        self.assertEqual(self.carne.stock_actual, Decimal('1.60'))  # 2.0 - 0.40

    def test_venta_falla_por_stock_insuficiente(self):
        """Verifica que pedir más platos de los que permite el stock lanza error y no modifica nada."""
        # Se requieren 10 * 2 = 20 panes, pero solo hay 10 disponibles
        items = [{'id': self.burger.id, 'cantidad': 10, 'observacion': ''}]

        with self.assertRaises(Exception):
            procesar_venta_atomic(items, 'Efectivo', usuario=self.cajero)

        # Stock intacto
        self.pan.refresh_from_db()
        self.assertEqual(self.pan.stock_actual, Decimal('10.00'))
        self.assertEqual(Venta.objects.count(), 0)

    def test_cajero_accede_pos_pero_no_a_recetas(self):
        """El cajero puede ver el POS pero es redirigido/bloqueado si intenta entrar a recetas."""
        self.client.login(username='cajero@test.com', password='Password123!')

        resp_pos = self.client.get(reverse('ventas:pos'))
        self.assertEqual(resp_pos.status_code, 200)

        resp_recetas = self.client.get(reverse('recetas:lista'))
        # Cajero no tiene rol 'administrador', debe ser redirigido a su inicio
        self.assertEqual(resp_recetas.status_code, 302)

    def test_empleado_accede_inventario_pero_no_a_pos(self):
        """El empleado tiene acceso a inventario pero no a pos."""
        self.client.login(username='empleado@test.com', password='Password123!')

        resp_inv = self.client.get(reverse('inventario:lista'))
        self.assertEqual(resp_inv.status_code, 200)

        resp_pos = self.client.get(reverse('ventas:pos'))
        self.assertEqual(resp_pos.status_code, 302)
