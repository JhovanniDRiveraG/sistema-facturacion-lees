# Sistema de Facturación y Tarifario - Telerradiología

Este proyecto es una herramienta interna para la gestión, cálculo de facturación y generación de reportes de exámenes médicos.

##  Tecnologías utilizadas
* **Backend:** Python, FastAPI
* **Frontend:** React (Vite)
* **Generación de PDF:** FPDF2
* **Generación de Excel:** Pandas, OpenPyXL

##  Estructura del Proyecto y Archivos Clave

### Backend (`/backend/app`)
* **`main.py`**: Punto de entrada de la aplicación FastAPI. Configura los CORS y las rutas.
* **`run.py`**: Script para iniciar el servidor de desarrollo (`python run.py`).
* **`/config`**: 
  * **`tarifas/`**: Contiene los archivos `.json` con las reglas de negocio y precios de cada cliente (ej: `cristo_redentor.json`, `inkamay.json`).
  * **`tarifario/`**: Contiene el tarifario especial de Trujillo Chota (`tarifario_chota.json`).
* **`/services`**:
  * **`telerradiologia_client.py`**: Cliente para conectarse a las APIs de los distintos servidores (LEES, Primavera).
  * **`facturacion_service.py`**: Lógica matemática de facturación (Rangos, Umbrales, Productividad).
  * **`excel_service.py`**: Generación de archivos Excel con estilos y totales.
  * **`documento_service.py`**: Generación de reportes en PDF con diseño personalizado.
* **`/routers`**:
  * **`facturacion.py`**: Endpoints de la API (preview, exportar, facturar, documento, etc.).
* **`/utils`**:
  * **`helpers.py`**: Funciones de apoyo (formateo de fechas, filtros, extracción de datos).
* **`/static`**: Imágenes utilizadas para los reportes PDF (logos, encabezados).

### Frontend (`/frontend/src`)
* **`App.jsx`**: Componente principal, manejo de estados y vista de la interfaz.
* **`api.js`**: Configuración de las peticiones `fetch` hacia el backend.
* **`App.css`**: Estilos visuales del sistema.

##  Configuración (.env)
Para que el sistema funcione, es necesario crear un archivo `.env` en la carpeta `backend` con las credenciales y tokens de acceso a los servidores:
* `LEES_API_URL` y `LEES_API_TOKEN`
* `PRIMAVERA_CHIMBOTE_API_URL` y `PRIMAVERA_CHIMBOTE_API_TOKEN`
* `PRIMAVERA_TRUJILLO_API_URL` y `PRIMAVERA_TRUJILLO_API_TOKEN`



##  Cómo ejecutar el proyecto localmente

### Backend
1. Entrar a la carpeta: `cd backend`
2. Instalar dependencias: `pip install -r requirements.txt`
3. Configurar el archivo `.env` (solicitar credenciales de los servidores).
4. Iniciar el servidor: `python run.py`

### Frontend
1. Entrar a la carpeta: `cd frontend`
2. Instalar dependencias: `npm install`
3. Iniciar la aplicación: `npm run dev` (si no dunciona en powershell intenta con el command prompt )