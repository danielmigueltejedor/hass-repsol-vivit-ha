![banner](https://raw.githubusercontent.com/danielmigueltejedor/hass-repsol-vivit-ha/main/banner.png)

# 🟠 repsol vivit + Home Assistant (Daniel Fork)

![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-41BDF5?style=for-the-badge&logo=homeassistant)
![Version](https://img.shields.io/badge/Version-1.4.1-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

Integración **mejorada y actualizada** para **Repsol Luz y Gas** en Home Assistant.  
Basada en el proyecto original [`ad-ha/repsolluzygas-async`](https://github.com/ad-ha/repsolluzygas-async), esta versión corrige y amplía funcionalidades clave:

- 🔑 Compatibilidad con **múltiples contratos** (electricidad y gas).
- ⚡ Corrección completa del **login y autenticación UID**.
- 💶 Nuevos sensores para costes, facturación y batería virtual.
- 🧱 Refactor del flujo de configuración (`config_flow`) para elegir contrato directamente.
- 🧭 Revisión total de las entidades: mejor estructura, nombres más claros y datos actualizados.
- 🛠️ Código adaptado para mantener compatibilidad con **Home Assistant 2025.x**.

---

## 📦 Instalación mediante HACS

1. Abre **HACS → Integraciones → Menú (⋮) → Repositorios personalizados**
2. Añade el siguiente repositorio: https://github.com/danielmigueltejedor/hass-repsol-vivit-ha
3. Categoría → **Integration**
4. Pulsa **Añadir**, después busca **repsol vivit + Home Assistant** y **haz clic en Instalar**.
5. Reinicia Home Assistant.
6. Ve a **Configuración → Dispositivos e Integraciones → Añadir integración** → busca `Repsol Luz y Gas (Daniel Fork)`.

---

## ⚙️ Configuración

1. Introduce tus credenciales del área cliente de Repsol.
2. La integración mostrará todos los contratos disponibles (según el CUPS).
3. Elige el contrato deseado (p. ej. electricidad vivienda o gas).
4. Se crearán las entidades correspondientes a ese contrato.

> Puedes repetir la instalación varias veces para añadir **otros contratos**, cada uno con su propio conjunto de sensores.

---

## 🧾 Sensores disponibles

| Tipo | Descripción |
|------|--------------|
| 💡 **Costes** | Importe total, variable, fijo, consumo, media diaria |
| 📊 **Facturas** | Última factura, próxima factura (importe y desglose) |
| ⚙️ **Contrato** | Estado, potencia, tarifa, precios punta/valle |
| 🔋 **Batería virtual** | Pendiente, canjeada, total kWh, excedentes |
| 🔧 **SVA** | Servicios vinculados adicionales (si existen) |

---

## 🧠 Estructura de datos

Los sensores utilizan la información proporcionada por la API oficial de Repsol:
- Endpoint de login (`LOGIN_URL`)
- Contratos (`CONTRACTS_URL`)
- Costes (`COSTS_URL`)
- Facturas (`INVOICES_URL`, `NEXT_INVOICE_URL`)
- Batería virtual (`VIRTUAL_BATTERY_HISTORY_URL`)

Los datos se actualizan automáticamente mediante un **`DataUpdateCoordinator`** con un intervalo definido por `UPDATE_INTERVAL`.

---

## 🧩 Archivos principales

| Archivo | Descripción |
|----------|--------------|
| `__init__.py` | Inicialización y actualización periódica de datos |
| `config_flow.py` | Interfaz de configuración y selección de contrato |
| `sensor.py` | Creación de todas las entidades (costes, facturas, batería, etc.) |
| `const.py` | Definición de URLs, cabeceras y constantes |
| `manifest.json` | Información de integración para Home Assistant |

---

## 🧰 Desarrollo

Si quieres probar cambios:

```bash
cd /config/custom_components/
git clone https://github.com/danielmigueltejedor/hass-repsol-vivit-ha.git
ha core restart
```
Los logs detallados se pueden activar en tu configuration.yaml:

```bash
logger:
  default: warning
  logs:
    custom_components.repsolluzygas_async: debug
```
🧑‍💻 Autor

Daniel Miguel Tejedor
Desarrollador de Nodalia Smart Systems￼
📍 León, España

📜 Créditos

Basado en el proyecto original ad-ha/repsolluzygas-async￼
Modificado, optimizado y mantenido por Daniel Miguel Tejedor (Nodalia)
Distribuido bajo licencia MIT

---

## ⚠️ Descargo de responsabilidad

Este proyecto **no está afiliado ni asociado de ninguna manera con el Grupo Repsol ni con ninguna de sus filiales**.  
La información aquí presentada se ofrece únicamente con fines educativos y de recursos.  
Los desarrolladores **no respaldan ni promueven ningún uso inapropiado del código**,  
y **no asumen responsabilidad legal alguna** sobre el funcionamiento o la seguridad de los dispositivos conectados.

![icon](https://github.com/danielmigueltejedor/hass-repsol-vivit-ha/raw/main/icon.png)
