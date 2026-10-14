# MisePlace - Versión Django (Python)

Sistema integral de gestión para restaurantes recreado con arquitectura moderna en **Django 5.2**, diseño minimalista y profesional, y control estricto de concurrencia e inventario.

---

## Mejoras sobre la versión PHP original

1. **Arquitectura Limpia y Modular**:
   - Dividido en aplicaciones desacopladas: `usuarios`, `inventario`, `recetas`, `ventas` y `reportes`.
   - Modelo de usuario personalizado con autenticación por correo electrónico y roles tipados (`administrador`, `cajero`, `empleado`).
2. **Integridad de Datos y Concurrencia (ACID)**:
   - Descuento y adición atómica de stock mediante `transaction.atomic()` y bloqueos de fila con `select_for_update()`.
   - Evita condiciones de carrera que en PHP dependían exclusivamente de triggers en MariaDB.
3. **Cálculo en Tiempo Real de Disponibilidad de Platos**:
   - En el Menú POS, cada plato muestra dinámicamente cuántas porciones pueden prepararse según el stock actual de sus insumos.
4. **Diseño Minimalista y Profesional**:
   - Paleta sobria basada en grises refinados (`Slate`), acentos en borgoña/carmín gastronómico (`#991b1b`) e indicadores de estado (`Emerald` para óptimo, `Amber` para bajo mínimo, `Rose` para crítico).
   - Tipografía limpia con Inter, controles accesibles, modales fluidos y tickets de venta optimizados para impresión térmica o estándar.
5. **Sincronización en Tiempo Real**:
   - Endpoint ligero `/reportes/api/estado-sistema/` y script cliente que alerta al usuario cuando otro terminal realiza ventas, compras o modificaciones de stock.
6. **Flexibilidad de Base de Datos**:
   - SQLite listo para usar sin requerir servidores externos o XAMPP.
   - Soporte automático para MySQL / MariaDB configurable mediante variables de entorno (`MISEPLACE_DB_HOST`, `MISEPLACE_DB_NAME`, `MISEPLACE_DB_USER`, `MISEPLACE_DB_PASSWORD`).

---

## Roles y Permisos

| Rol | Vistas y Funcionalidades |
| --- | --- |
| `cajero` | Menú virtual POS, armado de pedidos, observaciones por plato, cobro en Efectivo o QR, comprobantes imprimibles e historial diario. |
| `empleado` | Gestión de inventario, registro de compras y mermas, alertas de stock bajo y compras sugeridas. |
| `administrador` | Acceso total a todos los módulos: Menú POS, Inventario, Recetas dinámicas, Reportes ejecutivos y Métricas semanales. |

### Cuentas de demostración

| Rol | Correo | Contraseña |
| --- | --- | --- |
| **Administrador** | `admin@miseplace.com` | `Admin123!` |
| **Cajero** | `caja@miseplace.com` | `Caja123!` |
| **Empleado** | `empleado@miseplace.com` | `Empleado123!` |

*(La pantalla de inicio de sesión incluye botones de acceso rápido para rellenar estas credenciales con un solo clic durante pruebas locales).*

---

## Puesta en marcha con Conda (`ds_env`)

1. **Activar el entorno virtual**:
   ```powershell
   conda activate ds_env
   ```

2. **Ingresar al directorio del proyecto Django**:
   ```powershell
   cd c:\Users\josia\MisePlace\django
   ```

3. **(Opcional) Repoblar los datos de prueba**:
   ```powershell
   python manage.py poblar_datos
   ```

4. **Ejecutar el servidor de desarrollo**:
   ```powershell
   python manage.py runserver
   ```

5. **Acceder a la aplicación**:
   Abre en tu navegador: [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/)

---

## Ejecución de Pruebas Automatizadas

Para validar todos los casos de prueba de negocio, roles y transacciones de stock:
```powershell
python manage.py test
```
