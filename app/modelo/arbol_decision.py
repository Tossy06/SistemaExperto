"""Recorrido del árbol de decisión completo para una evaluación (se muestra animado en la página de resultado).

El árbol no está escrito en el código: se arma con los gránulos de TODAS las hipótesis activas de la base de
conocimiento. Cada camino raíz -> hoja es una hipótesis y cada nivel es uno de sus gránulos (hecho y peso), en el
orden de las preguntas del cuestionario. Los caminos que comparten hechos comparten nodos, como en el árbol del
documento técnico. Una rama adicional agrupa las reglas de resultado no concluyente.
"""
from decimal import Decimal


def construir_recorrido(ramas, respuestas, reglas_rn=()) -> dict:
    """ramas: una fila por gránulo con codigo, programa_academico, posicion (None si no quedó entre las cinco),
    probabilidad y numero_coincidencias (None si no tuvo coincidencias), variable, valor_clasificado, peso,
    coincide y orden (orden de la pregunta de la variable).
    respuestas: filas con variable y valor_clasificado (nivel real del aspirante en cada variable).
    reglas_rn: filas con codigo_regla, descripcion y cumple.
    Devuelve la raíz {"hijos": [...], "niveles": n, "hojas": n}."""
    nivel_del_aspirante = {r["variable"]: r["valor_clasificado"] for r in respuestas}
    por_hipotesis = {}
    for fila in ramas:
        por_hipotesis.setdefault(fila["codigo"], []).append(fila)

    raiz = {"hijos": [], "nivel": 0}
    for codigo in sorted(por_hipotesis):
        granulos = sorted(por_hipotesis[codigo], key=lambda g: (g["orden"], g["variable"]))
        nodo = raiz
        for g in granulos:
            clave = (g["variable"], g["valor_clasificado"])
            hijo = next((h for h in nodo["hijos"] if h.get("clave") == clave), None)
            if hijo is None:
                hijo = {"clave": clave, "variable": g["variable"], "valor": g["valor_clasificado"],
                        "coincide": bool(g["coincide"]), "su_nivel": nivel_del_aspirante.get(g["variable"]),
                        "pesos": set(), "nivel": nodo["nivel"] + 1, "hijos": []}
                nodo["hijos"].append(hijo)
            hijo["pesos"].add(Decimal(g["peso"]))
            nodo = hijo
        primero = granulos[0]
        nodo["hijos"].append({"hoja": True, "nivel": nodo["nivel"] + 1, "codigo": codigo,
                              "programa_academico": primero["programa_academico"], "posicion": primero["posicion"],
                              "probabilidad": primero["probabilidad"],
                              "numero_coincidencias": primero["numero_coincidencias"] or 0,
                              "numero_granulos": len(granulos)})

    def cerrar(nodo):
        # Un nodo compartido muestra su peso solo si es el mismo para todas las hipótesis que lo usan.
        pesos = nodo.pop("pesos", None)
        if pesos is not None:
            nodo["peso"] = next(iter(pesos)) if len(pesos) == 1 else None
        nodo.pop("clave", None)
        profundidad = nodo["nivel"]
        for h in nodo.get("hijos", []):
            profundidad = max(profundidad, cerrar(h))
        return profundidad

    raiz["niveles"] = cerrar(raiz)
    raiz["hojas"] = len(por_hipotesis)
    raiz["niveles_sin_coincidencia"] = _niveles_sin_coincidencia(raiz)
    if reglas_rn:
        raiz["hijos"].append({"condiciones": True, "nivel": 1, "coincide": any(r["cumple"] for r in reglas_rn),
                              "hijos": [{"regla": True, "nivel": raiz["niveles"], "codigo": r["codigo_regla"],
                                         "descripcion": r["descripcion"], "cumple": bool(r["cumple"])}
                                        for r in reglas_rn]})
    return raiz


def _niveles_sin_coincidencia(raiz) -> list:
    """Niveles (columnas) del árbol en los que ningún dato coincide con el perfil del aspirante.
    Para cada uno indica qué valores aportan peso en la base de conocimiento y en qué quedaron las respuestas,
    para explicar por qué toda la columna aparece en gris."""
    por_nivel = {}
    pendientes = list(raiz["hijos"])
    while pendientes:
        nodo = pendientes.pop()
        if "variable" in nodo:
            por_nivel.setdefault(nodo["nivel"], []).append(nodo)
            pendientes.extend(nodo["hijos"])
    salida = []
    for nivel in sorted(por_nivel):
        nodos = por_nivel[nivel]
        if any(n["coincide"] for n in nodos):
            continue
        variables = sorted({n["variable"] for n in nodos})
        primeras = {v.split(" ")[0] for v in variables}
        salida.append({
            "nivel": nivel,
            "grupo": primeras.pop() if len(primeras) == 1 else None,   # p. ej. «Interés» si todas lo comparten
            "variables": variables,
            "valores_con_peso": sorted({n["valor"] for n in nodos}),
            "niveles_aspirante": sorted({n["su_nivel"] for n in nodos if n["su_nivel"]}),
        })
    return salida
