from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El correo electrónico es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('rol', Usuario.Rol.ADMINISTRADOR)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    class Rol(models.TextChoices):
        ADMINISTRADOR = 'administrador', 'Administrador'
        CAJERO = 'cajero', 'Cajero'
        EMPLEADO = 'empleado', 'Empleado'

    email = models.EmailField('Correo electrónico', unique=True, max_length=150)
    nombre = models.CharField('Nombre o apodo', max_length=100, blank=True)
    rol = models.CharField('Rol', max_length=20, choices=Rol.choices, default=Rol.EMPLEADO)
    is_active = models.BooleanField('Activo', default=True)
    is_staff = models.BooleanField('Acceso a staff', default=False)
    fecha_registro = models.DateTimeField('Fecha de registro', auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['email']

    def __str__(self):
        nombre_mostrar = self.nombre if self.nombre else self.email
        return f"{nombre_mostrar} ({self.get_rol_display()})"

    @property
    def es_admin(self) -> bool:
        return self.rol == self.Rol.ADMINISTRADOR or self.is_superuser

    @property
    def es_cajero(self) -> bool:
        return self.rol == self.Rol.CAJERO

    @property
    def es_empleado(self) -> bool:
        return self.rol == self.Rol.EMPLEADO

    @property
    def puede_acceder_pos(self) -> bool:
        return self.es_admin or self.es_cajero

    @property
    def puede_acceder_inventario(self) -> bool:
        return self.es_admin or self.es_empleado

    @property
    def puede_acceder_recetas(self) -> bool:
        return self.es_admin

    @property
    def puede_acceder_reportes(self) -> bool:
        return self.es_admin or self.es_empleado
