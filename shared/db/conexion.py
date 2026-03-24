import os

import psycopg2
from psycopg2 import pool


def _obtener_env(nombre, default=None):
    valor = os.getenv(nombre, default)
    if valor is None or valor == "":
        raise RuntimeError(f"Falta configurar la variable de entorno {nombre}.")
    return valor


_POOL = None


class _ConexionPoolProxy:
    def __init__(self, pool_conexiones, conexion_real):
        self._pool = pool_conexiones
        self._conexion = conexion_real
        self._devuelta = False

    def close(self):
        if self._devuelta:
            return
        self._pool.putconn(self._conexion)
        self._devuelta = True

    def __getattr__(self, nombre):
        return getattr(self._conexion, nombre)

    def __enter__(self):
        self._conexion.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        self._conexion.__exit__(exc_type, exc, tb)
        self.close()
        return False


def _parametros_conexion():
    return {
        "host": _obtener_env("PGHOST", "127.0.0.1"),
        "port": int(_obtener_env("PGPORT", "5432")),
        "dbname": _obtener_env("PGDATABASE", "Inperia_db"),
        "user": _obtener_env("PGUSER", "postgres"),
        "password": _obtener_env("PGPASSWORD", "1234"),
    }


def _obtener_pool():
    global _POOL
    if _POOL is not None:
        return _POOL

    try:
        _POOL = pool.SimpleConnectionPool(1, 10, **_parametros_conexion())
    except Exception as e:
        print(f"Advertencia: no se pudo inicializar el pool de conexiones. {e}")
        _POOL = None
    return _POOL


def obtener_conexion():
    pool_conexiones = _obtener_pool()
    if pool_conexiones is None:
        return psycopg2.connect(**_parametros_conexion())

    conexion_real = pool_conexiones.getconn()
    return _ConexionPoolProxy(pool_conexiones, conexion_real)


def cerrar_pool_conexiones():
    global _POOL
    if _POOL is not None:
        _POOL.closeall()
        _POOL = None
