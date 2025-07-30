# 🚀 Guía de Desarrollo Local

## Configuración Inicial

### 1. Instalar Dependencias
```bash
pip install python-dotenv
pip install -r config/requirements.txt
```

### 2. Crear archivo `.env`
Crea un archivo `.env` en la **raíz del proyecto** con:

```env
# Variables de entorno para desarrollo local
SUPABASE_URL=tu_supabase_url_aqui
SUPABASE_KEY=tu_supabase_key_aqui
GOOGLE_CLIENT_ID=tu_google_client_id_aqui
GOOGLE_CLIENT_SECRET=tu_google_client_secret_aqui
SECRET_KEY=una_clave_secreta_para_desarrollo_local

# Opcional: Variables de desarrollo  
FLASK_ENV=development
FLASK_DEBUG=1
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
# Desde la raíz del proyecto
python main.py
```

### 6. Abrir en el navegador
```
http://localhost:8080
```

**Rutas disponibles:**
- `/` - Página de login (si no estás autenticado) o redirección a `/home`
- `/home` - Dashboard principal con módulos del sistema
- `/checks` - Panel de chequeos de disponibilidad

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
cd src && python app.py

# En otra terminal
ngrok http 8080
```

Luego configura la URL de ngrok en Google Cloud Console.

#### Opción 2: Modificar dominio permitido (temporal)
En `src/app.py`, línea 53, agrega temporalmente:
```python
ALLOWED_DOMAINS = ["primary.com.ar", "gmail.com"]  # Solo para desarrollo
```

## Nueva Estructura del Proyecto

```
chequeos-disponibilidad-matrizoms/
├── src/                     # 🎯 Código fuente
│   ├── app.py              # Aplicación principal
│   ├── checks/             # Módulos de chequeos
│   ├── static/
│   │   ├── css/style.css   # Estilos principales
│   │   ├── js/             # JavaScript
│   │   └── images/         # Imágenes y assets
│   └── templates/          # Templates HTML
├── config/                  # ⚙️ Configuración
│   ├── requirements.txt    # Dependencias Python
│   ├── render.yaml         # Configuración Render
│   └── .env.example        # Ejemplo de variables
├── docs/                    # 📚 Documentación
│   ├── DESARROLLO_LOCAL.md # Esta guía
│   └── README.md           # Documentación principal
├── temp/                    # 🗂️ Archivos temporales
│   └── flask_session/      # Sesiones de Flask
├── .env                     # Variables de entorno (crear este archivo)
├── .gitignore              # Archivos ignorados por Git
└── pyproject.toml          # Configuración del proyecto
```

## Ventajas de la Nueva Estructura

✅ **Mejor organización** - Separación clara entre código, configuración y documentación
✅ **Más profesional** - Estructura estándar de proyectos Python
✅ **Fácil mantenimiento** - Archivos organizados por propósito
✅ **Escalabilidad** - Preparado para crecimiento del proyecto
✅ **Despliegue limpio** - Configuración separada del código

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

- La aplicación detecta automáticamente si está en desarrollo local
- En producción (Render), usa las variables de entorno del servicio
- Los archivos estáticos se sirven desde `src/static/`
- Las sesiones se almacenan en `temp/flask_session/` para desarrollo
- La nueva estructura mejora la organización y mantenibilidad

## Despliegue a Producción

Para despliegue en Render:
1. Las variables de entorno se configuran en el dashboard de Render
2. La detección automática usa las URLs de producción
3. Se ejecuta desde `src/app.py` con gunicorn
4. Configuración en `config/render.yaml` 