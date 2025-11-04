![banner](https://raw.githubusercontent.com/danielmigueltejedor/hass-repsolluzygas-daniel/main/banner.png)

# 🟠 Repsol Vivit + Home Assistant (Daniel Fork)

> Integración mejorada y actualizada para **Repsol Luz y Gas** en Home Assistant.  
> Permite visualizar todos tus contratos de electricidad y gas con datos de consumo, costes y facturación en tiempo real.

---

## ✨ Características principales

✅ Autenticación actualizada con el sistema UID de Repsol  
⚡ Compatibilidad con **múltiples contratos** (electricidad y gas)  
💶 Sensores para **costes**, **facturas** y **batería virtual**  
🧭 Interfaz de configuración que permite elegir el contrato desde el flujo de configuración  
🧱 Datos agrupados en dispositivos únicos por contrato (CUPS)  
🧩 Compatible con **Home Assistant 2025.x**

---

## 🧰 Instalación (HACS)

1. En Home Assistant abre **HACS → Integraciones → Menú (⋮) → Repositorios personalizados**
2. Añade: https://github.com/danielmigueltejedor/hass-repsolluzygas-daniel
3. Categoría → **Integration**
4. Instala la integración y reinicia Home Assistant
5. Añade una nueva integración:  
**Repsol Luz y Gas (Daniel Fork)**
6. Introduce tus credenciales del área de cliente Repsol y selecciona el contrato

> 💡 Puedes repetir el proceso para añadir varios contratos (uno por instancia).

---

## 📊 Sensores disponibles

| Tipo | Descripción |
|------|--------------|
| 💡 **Costes** | Importe total, variable, fijo, consumo y media diaria |
| 📄 **Facturas** | Última factura y próxima factura (importe y desglose) |
| ⚙️ **Contrato** | Estado, potencia, tarifa, precios punta/valle |
| 🔋 **Batería Virtual** | Pendiente, canjeada, total kWh y excedentes |
| 🔧 **SVA** | Servicios adicionales asociados (si existen) |

---

## ⚙️ Configuración avanzada

Para habilitar logs de depuración:

```yaml
logger:
default: warning
logs:
 custom_components.repsolluzygas_async: debug
```
El archivo de log mostrará los contratos detectados y la información obtenida desde la API de Repsol.

🧑‍💻 Autor

Daniel Miguel Tejedor
Desarrollador de Nodalia Smart Systems￼
📍 León, España

📜 Créditos

Basado en el proyecto original ad-ha/repsolluzygas-async￼
Modificado, optimizado y mantenido por Daniel Miguel Tejedor (Nodalia)
Distribuido bajo licencia MIT

![icon](https://github.com/danielmigueltejedor/hass-repsolluzygas-daniel/raw/main/icon.png)
