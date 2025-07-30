# 🚀 Guía de Desarrollo Local

## Configuración Inicial

### 1. Instalar Dependencias
```bash
pip install python-dotenv
pip install -r requirements.txt
```

### 2. Crear archivo `.env`
Crea un archivo `.env` en la raíz del proyecto con:

```env
# Variables de entorno para desarrollo local
SUPABASE_URL=tu_supabase_url_aqui
SUPABASE_KEY=tu_supabase_key_aqui
GOOGLE_CLIENT_ID=tu_google_client_id_aqui
GOOGLE_CLIENT_SECRET=tu_google_client_secret_aqui
SECRET_KEY=una_clave_secreta_para_desarrollo_local
```

## Configuración de Google OAuth

### 3. Configurar Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto o crea uno nuevo
3. Ve a **APIs & Services** → **Credentials**
4. Edita tu **OAuth 2.0 Client ID**

#### URLs de JavaScript autorizadas:
```
http://localhost:8080
```

#### URIs de redirección autorizados:
```
http://localhost:8080/auth/callback
```

### 4. ⚠️ IMPORTANTE: Acceso por localhost

**SIEMPRE accede a la aplicación usando:**
```
http://localhost:8080
```

**❌ NO uses:**
- `http://192.168.x.x:8080`
- `http://127.0.0.1:8080` (aunque funciona, usar localhost es mejor)

## Ejecutar la Aplicación

### 5. Iniciar el servidor
```bash
python main.py
```

### 6. Abrir en el navegador
```
http://localhost:8080
```

## Solución de Problemas

### Error: "device_id and device_name are required for private IP"

**Causa:** Estás accediendo por IP privada (192.168.x.x)

**Solución:** Usa `http://localhost:8080`

### Error: "redirect_uri_mismatch"

**Causa:** La URL de callback no está configurada en Google Cloud Console

**Solución:** 
1. Ve a Google Cloud Console → APIs & Services → Credentials
2. Agrega `http://localhost:8080/auth/callback` a los URIs de redirección autorizados

### Error: "InsecureTransportError: OAuth 2 MUST utilize https"

**Causa:** oauthlib requiere HTTPS por seguridad, pero en desarrollo local usamos HTTP

**Solución:** ✅ **Ya solucionado automáticamente**
- La aplicación detecta automáticamente si está en desarrollo local
- Solo en desarrollo permite HTTP para OAuth
- En producción mantiene la seguridad HTTPS

### Para acceso desde otros dispositivos de la red

Si necesitas que otros accedan a tu aplicación de desarrollo:

#### Opción 1: ngrok (Recomendado)
```bash
# Instalar ngrok
# Windows: choco install ngrok
# Mac: brew install ngrok
# Linux: descargar desde https://ngrok.com/download

# Ejecutar tu app
python main.py

# En otra terminal
ngrok http 8080
```

Luego configura la URL de ngrok en Google Cloud Console.

#### Opción 2: Modificar dominio permitido (temporal)
En `main.py`, línea 33, agrega temporalmente:
```python
ALLOWED_DOMAINS = ["primary.com.ar", "gmail.com"]  # Solo para desarrollo
```

## Estructura del Proyecto

```
chequeos-disponibilidad-matrizoms/
├── checks/               # Módulos de chequeos
├── static/
│   ├── css/style.css    # Estilos principales
│   └── js/              # JavaScript
├── templates/           # Templates HTML
├── .env                 # Variables de entorno (crear este archivo)
├── main.py             # Aplicación principal
└── requirements.txt    # Dependencias
```

## Features del Frontend

✅ **Diseño moderno** con tema azul oscuro
✅ **Responsive** para móviles y tablets  
✅ **Autenticación OAuth** con Google
✅ **Dashboard interactivo** con cards de servicios
✅ **Ejecutar chequeos** individuales o en lote
✅ **Modales** para mostrar resultados
✅ **Notificaciones toast** para feedback
✅ **Animaciones suaves** y transiciones
✅ **Indicadores de estado** en tiempo real

## Notas de Desarrollo

- El código está configurado para detectar automáticamente si estás en desarrollo local
- En producción (Render), usa las variables de entorno del servicio
- Los archivos estáticos se sirven desde `/static/`
- Las sesiones se almacenan en el filesystem para desarrollo

## Despliegue a Producción

Para despliegue en Render:
1. Las variables de entorno se configuran en el dashboard de Render
2. La detección automática usa las URLs de producción
3. No se requiere el archivo `.env` en producción 