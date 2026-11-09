# LabTrack - Sistema de Gestión de Laboratorios
**Curso:** Calidad y Pruebas de Software | **Evaluación:** Caso T3  
**Docente:** Mark Anthony Arribasplata Palomino | **Estudiante:** Nicolás Loayza Romero

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Nico-LoRRo_Caso_T3&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Nico-LoRRo_Caso_T3)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=Nico-LoRRo_Caso_T3&metric=bugs)](https://sonarcloud.io/summary/new_code?id=Nico-LoRRo_Caso_T3)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=Nico-LoRRo_Caso_T3&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=Nico-LoRRo_Caso_T3)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=Nico-LoRRo_Caso_T3&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=Nico-LoRRo_Caso_T3)

---

## 📌 Descripción del Proyecto
LabTrack es una solución web para la gestión eficiente y segura de préstamos de equipos de laboratorio universitario (**Cómputo**, **Electrónica** y **Redes**), con reglas de negocio estrictas para evitar cruces de horarios y control automatizado de sanciones.

### Historias de Usuario Implementadas:
* **HU-01: Autenticación Segura:** Credenciales cifradas, mensaje exacto `"Credenciales inválidas"` y bloqueo preventivo al 3.er fallo consecutivo.
* **HU-02: Catálogo y Filtrado:** Inventario categorizado con filtros exactos por `"Cómputo"`, `"Electrónica"` y `"Redes"`.
* **HU-03: Reserva de Equipos (Flujo Crítico):** Validación de horarios, restricción a máx. 1 equipo simultáneo y bloqueo automático ante cruces con reservas aprobadas.
* **HU-04: Gestión de Solicitudes (Admin):** Panel de aprobación y rechazo con justificación obligatoria.
* **HU-05: Devolución y Penalización Automática:** Retorno inmediato a estado `"Disponible"` y penalización automática al estudiante si entrega fuera de hora.

---

## 🐳 Ejecución Inmediata con Docker

La aplicación está preconfigurada en el puerto **`10500`**:

```bash
# Iniciar contenedor en segundo plano
docker compose -f labtrack/docker-compose.yml up -d

# Ver estado
docker ps
```
Abrir en el navegador: **[http://localhost:10500](http://localhost:10500)**

---

## 🧪 Pruebas Automatizadas de Verificación
```bash
python labtrack/smoke_test.py
```
Valida de extremo a extremo las 5 historias de usuario (HU-01 a HU-05) con aserciones automáticas.
