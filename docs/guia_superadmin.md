# Guía del Super Administrador (Dueño del SaaS) - Panel BAPE

¡Bienvenido al manual del Super Administrador! 

Como dueño de la plataforma o responsable de gestionar a los clientes SaaS (Software as a Service), tú tienes el nivel de acceso más alto. Este documento te explica cómo gestionar múltiples empresas y cómo darles acceso al sistema para que puedan operar su propio Bot y panel de control.

---

## 1. Concepto de "Compañía" (Company) en BAPE
El sistema BAPE es **Multi-Tenant** (Multi-empresa). Esto significa que la base de datos almacena la información de muchos clientes dentro de una misma instalación. 

Para que los datos de un cliente (ej. *Veterinaria Huellas*) no se mezclen con los datos de otro cliente (ej. *Zapatería El Paso*), **todo en el sistema está asociado a un ID de Compañía (`company_id`)**.

Como SuperAdmin, tu labor principal es gestionar estas "Compañías".

---

## 2. Creación de un Nuevo Cliente (Empresa)

Actualmente, por seguridad, **el registro público en la pantalla de Login suele estar desactivado o restringido** para evitar que cualquier persona de internet cree una cuenta en tu servidor. 

Cuando consigues un nuevo cliente, debes crearle su espacio manualmente utilizando herramientas como **Postman**, el panel interactivo **Swagger UI**, o scripts de base de datos.

### Usando la API (Swagger UI) para dar de alta a un cliente:

1. Ingresa a la url de la documentación interactiva: `http://<tu-vps-o-localhost>:8000/docs`
2. Si la ruta está protegida, deberás iniciar sesión primero.
3. Busca el Endpoint **POST `/auth/register`**.
4. Haz clic en *"Try it out"* (Pruébalo).
5. Completa el JSON con los datos del nuevo dueño de la empresa:
   ```json
   {
     "usuario_correo": "nuevo_cliente@ejemplo.com",
     "clave_acceso": "una_clave_segura_123"
   }
   ```
6. Haz clic en **Execute** (Ejecutar).

> **¿Qué ocurre internamente?**
> Al ejecutar este registro, el sistema BAPE **crea automáticamente una nueva Compañía (Company)**, asigna a este usuario como su dueño, y crea una bóveda vacía de configuraciones (Settings) lista para que el cliente la personalice.

### Entregando las credenciales
Una vez devuelta la respuesta exitosa por la API:
1. Entrega el enlace de tu plataforma (ej: `https://panel.tubot.com/login`) al cliente.
2. Entrégale el `usuario_correo` y la `clave_acceso` genérica que creaste.
3. El cliente podrá iniciar sesión y verá su propio panel de control, aislado de los demás.

---

## 3. Gestión de Permisos y Usuarios

### El Rol del Dueño de la Empresa
El usuario que acabas de crear tiene el rol de administrador de **esa** empresa específica. Él, desde su panel ("Usuarios"), podrá invitar a sus propios empleados (ayudantes). Tú no necesitas hacerlo por él.

### Revisar cuentas en la Base de Datos
Si necesitas suspender a una empresa por falta de pago, restablecer una constraseña o eliminar datos, debes intervenir la base de datos.
- Puedes utilizar **DBeaver**, **PgAdmin**, o la consola del VPS para conectarte a la base de datos PostgreSQL.
- **Tabla `users`**: Puedes cambiar el campo `is_active` de `true` a `false` para impedir que un usuario inicie sesión en el panel.

---

## 4. Notas de Mantenimiento y Facturación

- **Límites Financieros:** Dado que el motor de IA llama a proveedores de pago (OpenAI, Groq), debes instruir a los clientes a que *coloquen sus propias API Keys* en el módulo de Configuración (Settings). Así, el consumo de Inteligencia Artificial se cobrará a sus respectivas tarjetas de crédito y no a cuenta tuya.
- **WhatsApp Engine:** Monitorea que tu VPS o servidor de Baileys tenga suficiente memoria RAM a medida que conectes a decenas de negocios simultáneamente.

¡Estás listo para comercializar el sistema!
