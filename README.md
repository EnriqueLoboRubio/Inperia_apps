# Inperia Apps

Esta carpeta es una separación de `Inperia` preparada para generar dos productos:

- `Inperia Cliente`: acceso exclusivo para internos.
- `Inperia Staff`: acceso para profesionales y administradores.

## Estructura

- `apps/cliente`: entrypoint, login y capas específicas del producto cliente.
- `apps/staff`: entrypoint, login y capas específicas del producto staff.
- `shared`: db, modelos, servicios, utilidades, IA y widgets reutilizados.
- `packaging/pyinstaller`: `.spec` para construir los ejecutables.
- `packaging/installer`: scripts de Inno Setup para generar instaladores.
- `scripts`: automatización de build e instalador.

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

## Requisitos de configuración

- Base de datos PostgreSQL accesible vía variables de entorno `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`.
- API de audio configurada en `apps/cliente/config/config.json`, `apps/staff/config/config.json`, `shared/config.json` o la variable `INPERAUDIO_API_URL`.
- Modelos locales de Vosk en `shared/utils/` para la transcripción.

## Build de ejecutables

Los builds usan `PyInstaller` en modo `onedir`.

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
