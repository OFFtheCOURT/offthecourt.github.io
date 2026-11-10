# Offcourt: cómo publicar tu web en GitHub Pages

Tiempo: unos 15 minutos. No hace falta instalar nada: todo se hace desde el navegador.

## 1. Crea una cuenta en GitHub
1. Entra en https://github.com/signup y crea tu cuenta (es gratis).
2. Confirma el correo que te envían.

## 2. Crea el repositorio
1. Arriba a la derecha pulsa **+** → **New repository**.
2. Nombre: `offcourt`.
3. Marca **Public** (GitHub Pages gratis necesita que sea público).
4. Pulsa **Create repository**.

## 3. Sube los archivos
1. Descomprime `offcourt.zip` en tu ordenador.
2. En la página del repositorio pulsa el enlace **uploading an existing file**.
3. Arrastra **todo el contenido** de la carpeta `offcourt` (no la carpeta en sí): `index.html`, los `.py`, `app.js`, `tpl_head.html`, `run.sh`, `actualizar.yml` y las carpetas `acb` y `lgl`.
4. Abajo pulsa **Commit changes**.

## 4. Crea el archivo de la automatización
GitHub no deja subir arrastrando la carpeta oculta `.github`, así que este archivo se crea a mano:
1. En el repositorio pulsa **Add file** → **Create new file**.
2. En el nombre escribe exactamente: `.github/workflows/actualizar.yml`
   (al escribir cada `/` GitHub crea la carpeta).
3. Abre `actualizar.yml` de tu ordenador con el Bloc de notas, copia todo el texto y pégalo.
4. Pulsa **Commit changes**.
5. (Opcional) Borra el `actualizar.yml` suelto de la raíz: ya no hace falta.

## 5. Da permiso a la automatización para guardar cambios
1. **Settings** → **Actions** → **General**.
2. Abajo, en *Workflow permissions*, marca **Read and write permissions** y pulsa **Save**.

## 6. Activa la web
1. **Settings** → **Pages**.
2. En *Source* elige **Deploy from a branch**.
3. En *Branch* elige **main** y la carpeta **/ (root)**. Pulsa **Save**.
4. Espera 1-2 minutos y recarga: arriba aparecerá tu dirección,
   `https://TU-USUARIO.github.io/offcourt/`

## 7. Prueba la actualización automática
1. Pestaña **Actions** → si te lo pide, pulsa **I understand my workflows, go ahead and enable them**.
2. A la izquierda elige **Actualizar Offcourt** → **Run workflow** → **Run workflow**.
3. En 1-2 minutos debe salir un círculo verde ✅. La web se actualizará sola en 1-2 minutos más.

## Qué hace sola a partir de ahora
- **Cada día** a las 10:37 y 14:37 (hora de España, invierno): resultados, clasificaciones, líderes y próximos partidos de las tres ligas.
- **Sábados y domingos** de 12:00 a 21:59: cada 10 minutos (ACB).
- **Martes a viernes** de 18:00 a 22:59: cada 15 minutos (EuroLiga y ACB).
- **Cada madrugada** de 01:00 a 07:59: cada 15 minutos (NBA).
- **Directo en la propia web**: mientras la tienes abierta, el bloque "Hoy" consulta el marcador de EuroLiga y NBA cada 30 segundos.

GitHub puede retrasar unos minutos las ejecuciones programadas cuando tiene mucha carga; es normal.

## Si algo falla
- En **Actions**, una ejecución con ❌: ábrela y mira el paso en rojo. Suele ser que una de las webs de datos no respondió; la siguiente ejecución lo arregla sola.
- Si sale el error `Permission denied` al guardar: revisa el paso 5.
