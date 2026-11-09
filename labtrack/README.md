# LabTrack - Sistema de Gestión de Laboratorios
**Curso:** Calidad y Pruebas de Software (Semana 13 / Evaluación T3)

Sistema web para el control de inventario y reservas de equipos de laboratorio universitario en las categorías **Cómputo**, **Electrónica** y **Redes**.

---

## 🚀 Cómo Iniciar la Aplicación

### Opción A: Con Docker (Recomendado)
El proyecto cuenta con `Dockerfile` y `docker-compose.yml` preconfigurados en el puerto **`10500`**:
```bash
# Iniciar contenedor
docker compose up -d

# Ver estado
docker ps

# Detener contenedor
docker compose down
```
Acceder en el navegador a: **`http://localhost:10500`**

---

### Opción B: Ejecución Local en Python
1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Iniciar el servidor web:**
   ```bash
   python run.py
   ```
   El sistema se abrirá en: **`http://127.0.0.1:5000`**

3. **Ejecutar pruebas automáticas de verificación:**
   ```bash
   python smoke_test.py
   ```

---

## 👥 Credenciales de Prueba Precargadas

| Rol | Código | Contraseña | Estado Inicial | Propósito en Pruebas |
| :--- | :--- | :--- | :--- | :--- |
| **Estudiante 1** | `N0001` | `123456` | Activo | Probar bloqueo de 3 intentos fallidos (**HU-01**) |
| **Estudiante 2** | `N0002` | `123456` | Activo | Probar catálogo y solicitudes de reserva (**HU-02**, **HU-03**) |
| **Estudiante 3** | `N0003` | `123456` | Activo | Probar cruces de horario y rechazo (**HU-03**, **HU-04**) |
| **Encargado** | `ADM01` | `admin123` | Activo | Aprobar/rechazar reservas y devoluciones (**HU-04**, **HU-05**) |

---

## 📋 Resumen de Cobertura de Historias de Usuario

* **HU-01: Autenticación Segura:**
  * Login con código y clave. Error exacto: `"Credenciales inválidas"`.
  * Bloqueo temporal automático al 3.er fallo consecutivo con alerta de seguridad.
* **HU-02: Catálogo y Filtrado:**
  * Visualización de inventario con filtros por: `"Cómputo"`, `"Electrónica"`, `"Redes"`.
  * Mensaje condicional ante catálogo vacío: `"No hay equipos disponibles en esta categoría"`.
* **HU-03: Reserva de Equipos (Flujo Crítico):**
  * Validación de selección de fechas y horarios.
  * Bloqueo ante cruces de horario con reservas ya aprobadas.
  * Restricción de máximo 1 equipo en préstamo simultáneo por estudiante.
* **HU-04: Gestión de Solicitudes (Admin):**
  * Tabla de pendientes con acciones **Aprobar** (equipo pasa a *"Prestado"*) y **Rechazar** (con justificación obligatoria).
* **HU-05: Devolución y Penalización Automática:**
  * Registro de devolución física (equipo pasa de inmediato a *"Disponible"*).
  * Si la hora de entrega supera la hora pactada, el estudiante pasa automáticamente al estado **`"Penalizado"`**.
