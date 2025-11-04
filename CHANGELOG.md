# 🧾 Changelog – Repsol Vivit + Home Assistant

Integración no oficial para vincular tu cuenta **Repsol Vivit** (antes *Repsol Luz y Gas*) con **Home Assistant**.  
Permite visualizar consumos, costes, facturas y datos de batería virtual directamente desde tu panel.

---

## 🟦 v1.4.3 — 2025-11-04
### 🧩 Estabilidad y experiencia de usuario
- Corregido: el flujo de configuración ya no lee dos veces la respuesta del login (evita falsos `cannot_connect`).
- Añadidos **timeouts de 15 s** para login y descarga de contratos.
- Diferenciación clara de errores:
  - `invalid_auth`: credenciales incorrectas.
  - `cannot_connect`: fallo de conexión.
  - `no_contracts`: cuenta sin contratos disponibles.
  - `unknown`: error inesperado.
- Traducciones completas **ES / EN**.
- Mejora en los mensajes y títulos de formularios de configuración.

### ⚙️ API y cabeceras
- Cabeceras actualizadas a `areacliente.repsol.es`.
- Limpieza de headers innecesarios (`sec-ch-ua*` y similares).
- Firma (`UID`, `signature`, `timestamp`) asignada dinámicamente tras el login.
- Mayor compatibilidad con contratos *Repsol Vivit* recientes.

### 🧱 Integración y sensores
- Estructura `coordinator` consolidada para evitar llamadas duplicadas.
- Manejo de datos flexible (listas/dicts) en facturas.
- Sensores reagrupados por **CUPS** y tipo de contrato.
- Sensor de batería virtual solo para contratos eléctricos.

### 🎨 Branding y HACS
- `manifest.json` actualizado:
  - `"domain": "repsolluzygas_async"`
  - `"name": "Repsol Vivit + Home Assistant"`
  - `"config_flow": true`
  - `"version": "1.4.3"`
- Compatibilidad total con **HACS**.
- Icono y banner renovados.
- Traducciones multi-idioma.

---

## 🟩 v1.4.2 — 2025-11-03
### ✨ Novedades
- Primeras mejoras tras el fork original.
- Refactorización de `__init__.py` y `sensor.py`:
  - Soporte para múltiples contratos simultáneos.
  - Mejora de rendimiento en fetch de datos.
- Añadido `manifest.json` con dominio correcto.
- Integración funcional con la API oficial de Repsol.
- Inicio de soporte para branding y publicación HACS.

---

## 🟨 v1.4.1 — 2025-11-02
### 🧰 Cambios técnicos
- Depuración inicial del fork.
- Limpieza de código, imports y dependencias.
- Compatibilidad verificada con HA 2025.10.x.

---

## 🟧 v1.4.0 — 2025-11-01
### 🧱 Base funcional estable
- Integración base totalmente operativa.
- Acceso a contratos e importación de datos de consumo y factura.
- Preparación para compatibilidad HACS.
- Nombre de dominio: `repsolluzygas_async`.

---

## 🧡 Disclaimer
**Este proyecto no está afiliado, patrocinado ni respaldado por Repsol ni por ninguna de sus filiales.**  
Su uso es únicamente con fines educativos y de automatización doméstica. Los desarrolladores no asumen responsabilidad legal por el uso, funcionamiento o seguridad de los dispositivos conectados.

---

## 👨‍💻 Autor
**Daniel Miguel Tejedor**  
🔗 [GitHub – danielmigueltejedor](https://github.com/danielmigueltejedor)  
📦 [Repositorio HACS](https://github.com/danielmigueltejedor/hass-repsol-vivit-ha)
