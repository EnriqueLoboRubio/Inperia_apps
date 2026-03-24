def condena_partes_a_double(anos, meses, dias):
    anos_int = int(anos or 0)
    meses_int = int(meses or 0)
    dias_int = int(dias or 0)
    total_dias = (anos_int * 365) + (meses_int * 30) + dias_int
    return total_dias / 365.0


def condena_double_a_partes(valor):
    try:
        total_dias = int(round(float(valor or 0) * 365))
    except (TypeError, ValueError):
        return 0, 0, 0

    anos = total_dias // 365
    resto = total_dias % 365
    meses = resto // 30
    dias = resto % 30
    return anos, meses, dias


def formatear_condena(valor):
    anos, meses, dias = condena_double_a_partes(valor)
    partes = []
    if anos:
        partes.append(f"{anos} año" if anos == 1 else f"{anos} años")
    if meses:
        partes.append(f"{meses} mes" if meses == 1 else f"{meses} meses")
    if dias:
        partes.append(f"{dias} día" if dias == 1 else f"{dias} días")
    return ", ".join(partes) if partes else "0 días"
