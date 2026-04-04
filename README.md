# Inperia Apps

Esta carpeta es una separacion de `Inperia` preparada para generar dos productos:

- `Inperia Cliente`: acceso exclusivo para internos.
- `Inperia Staff`: acceso para profesionales y administradores.

## Estructura

- `apps/cliente`: entrypoint, login y capas especificas del producto cliente.
- `apps/staff`: entrypoint, login y capas especificas del producto staff.
- `apps/staff/ia`: logica de analisis IA usada por la app de staff.
- `shared`: db, modelos, servicios, utilidades y widgets reutilizados.
- `packaging/pyinstaller`: `.spec` para construir los ejecutables.
- `packaging/installer`: scripts de Inno Setup para generar instaladores.
- `scripts`: automatizacion de build e instalador.

## Ejecucion en desarrollo

Instala dependencias:

```bash
pip install -r requirements.txt
```

Arranca una de las apps:

```bash
python apps/cliente/main.py
python apps/staff/main.py
```

## Requisitos de configuracion

- Base de datos PostgreSQL accesible con la configuracion del archivo `config.json` o, si se necesita sobrescribirla, con las variables `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`.
- API de audio configurada en `shared/config.json`, `%LOCALAPPDATA%\\Inperia Cliente\\config.json`, `%LOCALAPPDATA%\\Inperia Staff\\config.json` o la variable `INPERAUDIO_API_URL`.
- Modelo local de Vosk en `shared/utils/vosk-es/big` para la transcripcion de `Inperia Cliente`.
- Los datos mutables se guardan en `%LOCALAPPDATA%\\Inperia Cliente` y `%LOCALAPPDATA%\\Inperia Staff`.

Formato recomendado de `config.json`:

```json
{
  "server_host": "192.168.1.200",
  "api_scheme": "http",
  "api_port": 8000,
  "api_base_path": "/api",
  "database": {
    "port": 5432,
    "name": "Inperia_db",
    "user": "postgres",
    "password": "1234"
  }
}
```

Con este formato, `server_host` se reutiliza tanto para la API como para la base de datos.

## Build de ejecutables

Los builds usan `PyInstaller` en modo `onedir`.

- `Inperia Cliente` empaqueta `reportlab`, `vosk`, `PyAudio`, `sounddevice` y solo el modelo `big` de Vosk.
- `Inperia Staff` empaqueta `reportlab` y la IA de `apps/staff/ia`, sin Vosk.

```powershell
./scripts/build_cliente.ps1
./scripts/build_staff.ps1
```

Salida esperada:

- `dist/cliente/Inperia Cliente/Inperia Cliente.exe`
- `dist/staff/Inperia Staff/Inperia Staff.exe`

## Build de instaladores

Instala `Inno Setup 6` en Windows y luego ejecuta:

```powershell
./scripts/make_installer_cliente.ps1
./scripts/make_installer_staff.ps1
```

Salida esperada:

- `dist/installer/cliente/Inperia_Cliente_Setup.exe`
- `dist/installer/staff/Inperia_Staff_Setup.exe`

## Politica de acceso

- `Inperia Cliente` solo acepta usuarios con rol `interno`.
- `Inperia Staff` solo acepta usuarios con rol `profesional` o `administrador`.
- Si un usuario entra en la app equivocada, se muestra un mensaje indicando la app correcta.
