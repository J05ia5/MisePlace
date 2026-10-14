import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from usuarios.models import Usuario
from inventario.models import Insumo, Proveedor, Compra, DetalleCompra
from recetas.models import Plato, RecetaIngrediente
from ventas.models import Venta, DetalleVenta


class Command(BaseCommand):
    help = 'Puebla la base de datos con los datos iniciales y de demostración de MisePlace.'

    def handle(self, *args, **options):
        self.stdout.write("Poblando usuarios...")
        admin, _ = Usuario.objects.get_or_create(
            email='admin@miseplace.com',
            defaults={
                'nombre': 'Administrador General',
                'rol': Usuario.Rol.ADMINISTRADOR,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin.set_password('Admin123!')
        admin.save()

        cajero, _ = Usuario.objects.get_or_create(
            email='caja@miseplace.com',
            defaults={
                'nombre': 'Cajero Principal',
                'rol': Usuario.Rol.CAJERO,
            }
        )
        cajero.set_password('Caja123!')
        cajero.save()

        empleado, _ = Usuario.objects.get_or_create(
            email='empleado@miseplace.com',
            defaults={
                'nombre': 'Empleado de Almacén',
                'rol': Usuario.Rol.EMPLEADO,
            }
        )
        empleado.set_password('Empleado123!')
        empleado.save()

        self.stdout.write("Poblando proveedores...")
        prov1, _ = Proveedor.objects.get_or_create(
            nombre='Distribuidora La Paz',
            defaults={'telefono': '71234567', 'direccion': 'Av. Hernando Siles'}
        )
        prov2, _ = Proveedor.objects.get_or_create(
            nombre='Carniceria El Valle',
            defaults={'telefono': '76543210', 'direccion': 'Mercado Central'}
        )
        prov3, _ = Proveedor.objects.get_or_create(
            nombre='Verduras Fresh',
            defaults={'telefono': None, 'direccion': None}
        )

        self.stdout.write("Poblando insumos...")
        insumos_datos = [
            ('Manzanas', 'peso', 'kg', Decimal('25.00')),
            ('Papas', 'peso', 'kg', Decimal('40.00')),
            ('Carne de res', 'peso', 'kg', Decimal('15.30')),
            ('Aceite', 'volumen', 'litros', Decimal('12.00')),
            ('Pan de hamburguesa', 'unidad', 'und', Decimal('50.00')),
            ('Tomate', 'peso', 'kg', Decimal('10.00')),
            ('Lechuga', 'peso', 'kg', Decimal('5.00')),
            ('Queso', 'unidad', 'und', Decimal('30.00')),
        ]
        insumos_dict = {}
        for nombre, tipo, unidad, stock in insumos_datos:
            insumo, _ = Insumo.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'tipo_medicion': tipo,
                    'unidad_medida': unidad,
                    'stock_actual': stock,
                    'stock_minimo': Decimal('5.00'),
                    'stock_objetivo': Decimal('10.00'),
                }
            )
            insumos_dict[nombre] = insumo

        self.stdout.write("Poblando platos y recetas...")
        platos_datos = [
            ('Hamburguesa Clasica', Decimal('35.00'), 'platos/4cc2b1cd3eb24b8895bb7a164b8ae65d.jpg'),
            ('Pizza Familiar', Decimal('80.00'), None),
            ('Hot Dog', Decimal('25.00'), None),
            ('Papas Fritas', Decimal('15.00'), None),
            ('Pollo a la Parrilla', Decimal('75.00'), None),
            ('Refresco', Decimal('10.00'), None),
        ]
        platos_dict = {}
        for nombre, precio, img in platos_datos:
            plato, _ = Plato.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'precio_venta': precio,
                    'imagen': img,
                    'activo': True,
                }
            )
            platos_dict[nombre] = plato

        # Receta de la Hamburguesa Clásica
        hamburguesa = platos_dict['Hamburguesa Clasica']
        receta_hamb = [
            ('Pan de hamburguesa', Decimal('2.00')),
            ('Carne de res', Decimal('0.15')),
            ('Tomate', Decimal('0.03')),
            ('Lechuga', Decimal('0.02')),
            ('Queso', Decimal('1.00')),
        ]
        for insumo_nom, cant in receta_hamb:
            RecetaIngrediente.objects.get_or_create(
                plato=hamburguesa,
                insumo=insumos_dict[insumo_nom],
                defaults={'cantidad_necesaria': cant}
            )

        # Receta Papas Fritas
        papas_fritas = platos_dict['Papas Fritas']
        RecetaIngrediente.objects.get_or_create(
            plato=papas_fritas,
            insumo=insumos_dict['Papas'],
            defaults={'cantidad_necesaria': Decimal('0.35')}
        )
        RecetaIngrediente.objects.get_or_create(
            plato=papas_fritas,
            insumo=insumos_dict['Aceite'],
            defaults={'cantidad_necesaria': Decimal('0.05')}
        )

        self.stdout.write("Poblando compras históricas...")
        if not Compra.objects.exists():
            c1 = Compra.objects.create(
                proveedor=prov1,
                fecha_ingreso=datetime.date(2026, 7, 31),
                precio_compra_total=Decimal('250.00'),
                observaciones='Ingreso de aceite programado',
                creado_por=empleado
            )
            DetalleCompra.objects.create(
                compra=c1,
                insumo=insumos_dict['Aceite'],
                cantidad=Decimal('5.00'),
                precio_unidad=Decimal('50.00')
            )

            c2 = Compra.objects.create(
                proveedor=prov2,
                fecha_ingreso=datetime.date(2026, 7, 30),
                precio_compra_total=Decimal('210.00'),
                observaciones='Compra de carne de res',
                creado_por=empleado
            )
            DetalleCompra.objects.create(
                compra=c2,
                insumo=insumos_dict['Carne de res'],
                cantidad=Decimal('3.00'),
                precio_unidad=Decimal('70.00')
            )

            c3 = Compra.objects.create(
                proveedor=prov3,
                fecha_ingreso=datetime.date(2026, 7, 30),
                precio_compra_total=Decimal('80.00'),
                observaciones='Compra de papas para guarniciones',
                creado_por=empleado
            )
            DetalleCompra.objects.create(
                compra=c3,
                insumo=insumos_dict['Papas'],
                cantidad=Decimal('10.00'),
                precio_unidad=Decimal('8.00')
            )

        self.stdout.write("Poblando ventas históricas...")
        if not Venta.objects.exists():
            ventas_historicas = [
                (datetime.date(2026, 7, 31), datetime.datetime(2026, 7, 31, 12, 0, 0), Decimal('630.00'), 'Efectivo', 'Hamburguesa Clasica', 18),
                (datetime.date(2026, 7, 30), datetime.datetime(2026, 7, 30, 13, 15, 0), Decimal('960.00'), 'Efectivo', 'Pizza Familiar', 12),
                (datetime.date(2026, 7, 30), datetime.datetime(2026, 7, 30, 19, 30, 0), Decimal('625.00'), 'QR', 'Hot Dog', 25),
                (datetime.date(2026, 7, 29), datetime.datetime(2026, 7, 29, 14, 0, 0), Decimal('450.00'), 'Efectivo', 'Papas Fritas', 30),
                (datetime.date(2026, 7, 28), datetime.datetime(2026, 7, 28, 20, 10, 0), Decimal('750.00'), 'QR', 'Pollo a la Parrilla', 10),
                (datetime.date(2026, 7, 28), datetime.datetime(2026, 7, 28, 21, 0, 0), Decimal('500.00'), 'Efectivo', 'Refresco', 50),
            ]

            for f_venta, f_hora, total, pago, plato_nom, cant in ventas_historicas:
                v = Venta.objects.create(
                    fecha_venta=f_venta,
                    fecha_hora=timezone.make_aware(f_hora) if timezone.is_naive(f_hora) else f_hora,
                    total_venta=total,
                    metodo_pago=pago,
                    usuario=cajero
                )
                plato_obj = platos_dict[plato_nom]
                DetalleVenta.objects.create(
                    venta=v,
                    plato=plato_obj,
                    cantidad=cant,
                    precio_unitario=plato_obj.precio_venta,
                    subtotal=total
                )

        self.stdout.write(self.style.SUCCESS("¡Base de datos poblada exitosamente!"))
