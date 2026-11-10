"""Genera los diagramas nuevos del documento en SVG y los convierte a PDF vectorial (PyMuPDF)."""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import pymupdf as fitz

SALIDA = Path(sys.argv[1])
SALIDA.mkdir(parents=True, exist_ok=True)
FUENTE = "Helvetica, Arial, sans-serif"

AZUL, AZUL_CLARO = "#1F4E79", "#DCE8F5"
VERDE, VERDE_CLARO = "#2E6B3A", "#E2F0E4"
AMBAR, AMBAR_CLARO = "#9A6B00", "#FFF4D6"
GRIS, GRIS_CLARO = "#5F6B73", "#F1F3F4"
TINTA = "#1B2631"


class Svg:
    def __init__(self, ancho, alto):
        self.ancho, self.alto, self.p = ancho, alto, []

    def add(self, s):
        self.p.append(s)

    def texto(self, x, y, t, tam=13, peso="normal", anc="start", color=TINTA, estilo="normal"):
        sangria = len(t) - len(t.lstrip(" "))
        x, t = x + sangria * tam * 0.3, t.strip(" ")
        self.add(f'<text x="{x}" y="{y}" font-family="{FUENTE}" font-size="{tam}" font-weight="{peso}" '
                 f'font-style="{estilo}" text-anchor="{anc}" fill="{color}">{escape(t)}</text>')

    def rect(self, x, y, w, h, fill="#fff", stroke=TINTA, sw=1.2, rx=0, dash=None):
        if dash:
            self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="none"/>')
            self.linea([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)], stroke, sw, dash)
            return
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def _seg(self, a, b, color, sw):
        self.add(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{color}" stroke-width="{sw}"/>')

    def linea(self, pts, color=TINTA, sw=1.2, dash=None, fin=None, ini=None):
        import math
        if dash:
            on, off = (float(v) for v in dash.split())
            for a, b in zip(pts, pts[1:]):
                L = math.dist(a, b); ux, uy = (b[0]-a[0])/L, (b[1]-a[1])/L; t = 0.0
                while t < L:
                    e = min(t + on, L)
                    self._seg((a[0]+ux*t, a[1]+uy*t), (a[0]+ux*e, a[1]+uy*e), color, sw); t = e + off
        else:
            pts_s = " ".join(f"{x},{y}" for x, y in pts)
            self.add(f'<polyline points="{pts_s}" fill="none" stroke="{color}" stroke-width="{sw}"/>')
        if fin:
            self.punta(pts[-2], pts[-1], fin, color)
        if ini:
            self.punta(pts[1], pts[0], ini, color)

    def punta(self, desde, hacia, tipo, color=TINTA):
        """Dibuja la punta en `hacia`, orientada desde `desde`."""
        import math
        L = math.dist(desde, hacia); ux, uy = (hacia[0]-desde[0])/L, (hacia[1]-desde[1])/L
        nx, ny = -uy, ux; x, y = hacia
        def P(a, b): return f"{x + ux*a + nx*b:.1f},{y + uy*a + ny*b:.1f}"
        if tipo == "flecha":
            self.add(f'<polygon points="{P(0,0)} {P(-11,5)} {P(-11,-5)}" fill="{color}"/>')
        elif tipo == "abierta":
            self.add(f'<polyline points="{P(-11,6)} {P(0,0)} {P(-11,-6)}" fill="none" stroke="{color}" stroke-width="1.3"/>')
        elif tipo == "herencia":
            self.add(f'<polygon points="{P(0,0)} {P(-15,8)} {P(-15,-8)}" fill="#fff" stroke="{color}" stroke-width="1.2"/>')
        elif tipo == "rombo":
            self.add(f'<polygon points="{P(0,0)} {P(-10,6)} {P(-20,0)} {P(-10,-6)}" fill="{color}"/>')

    def guardar(self, nombre):
        defs = f"""<defs>
  <marker id="flecha" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 Z" fill="{TINTA}"/></marker>
  <marker id="abierta" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="10" markerHeight="10" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10" fill="none" stroke="{TINTA}" stroke-width="1.3"/></marker>
  <marker id="herencia" viewBox="0 0 14 14" refX="14" refY="7" markerWidth="14" markerHeight="14" orient="auto-start-reverse" markerUnits="userSpaceOnUse">
    <path d="M0,0 L14,7 L0,14 Z" fill="#fff" stroke="{TINTA}" stroke-width="1.2"/></marker>
  <marker id="rombo" viewBox="0 0 20 10" refX="20" refY="5" markerWidth="20" markerHeight="10" orient="auto-start-reverse" markerUnits="userSpaceOnUse">
    <path d="M0,5 L10,0 L20,5 L10,10 Z" fill="{TINTA}"/></marker>
</defs>"""
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.ancho}" height="{self.alto}" '
               f'viewBox="0 0 {self.ancho} {self.alto}">\n{defs}\n<rect width="100%" height="100%" fill="#fff"/>\n'
               + "\n".join(self.p) + "\n</svg>\n")
        ruta = SALIDA / f"{nombre}.svg"
        ruta.write_text(svg, encoding="utf-8")
        pdf = fitz.open("pdf", fitz.open(str(ruta)).convert_to_pdf())
        pdf.save(str(SALIDA.parent / f"{nombre}.svg.pdf"), garbage=4, deflate=True)
        print("ok", nombre)


# ---------------------------------------------------------------------------------------------
# 1. Diagrama de casos de uso de alto nivel (Figura 7, actualizado con la aplicación web)
# ---------------------------------------------------------------------------------------------
def actor(s, x, y, nombre, sub="", color=TINTA):
    s.add(f'<circle cx="{x}" cy="{y}" r="13" fill="#fff" stroke="{color}" stroke-width="1.6"/>')
    s.linea([(x, y + 13), (x, y + 50)], color, 1.6)
    s.linea([(x - 24, y + 26), (x + 24, y + 26)], color, 1.6)
    s.linea([(x - 20, y + 82), (x, y + 50), (x + 20, y + 82)], color, 1.6)
    yy = y + 102
    for i, linea in enumerate(nombre.split("\n")):
        s.texto(x, yy + i * 16, linea, 13, "bold", "middle", color)
    if sub:
        s.texto(x, yy + 16 * len(nombre.split("\n")) + 2, sub, 11, "normal", "middle", GRIS, "italic")


def caso(s, cx, cy, codigo, texto, fill=AZUL_CLARO, stroke=AZUL, rx=112, ry=36):
    s.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')
    lineas = texto.split("\n")
    y0 = cy - (len(lineas) * 15) / 2 + 2
    s.texto(cx, y0, codigo, 12, "bold", "middle", stroke)
    for i, l in enumerate(lineas):
        s.texto(cx, y0 + 15 * (i + 1), l, 12, "normal", "middle")


def casos_de_uso():
    s = Svg(1200, 760)
    s.rect(230, 20, 740, 690, "#FBFCFD", AZUL, 1.6, 6)
    s.texto(600, 46, "Sistema Experto de Apoyo a la Orientación Académica (aplicación web)", 15, "bold", "middle", AZUL)
    C = {  # codigo: (cx, cy)
        "CU-02": (600, 105), "CU-01": (380, 250), "CU-03": (380, 360), "CU-05": (380, 470), "CU-08": (380, 580),
        "CU-04": (600, 430), "CU-06": (820, 250), "CU-07": (820, 360), "CU-09": (820, 470), "CU-10": (820, 580)}
    asp, ing, exp_ = (90, 280), (1110, 280), (1110, 590)
    # Asociaciones (se dibujan primero para quedar debajo de las elipses)
    for c in ("CU-01", "CU-03", "CU-05", "CU-08"):
        s.linea([(asp[0] + 26, asp[1] + 30), C[c]], TINTA, 1.1)
    for c in ("CU-06", "CU-07", "CU-09", "CU-10"):
        s.linea([(ing[0] - 26, ing[1] + 30), C[c]], TINTA, 1.1)
    s.linea([(asp[0] + 26, asp[1] + 30), (C["CU-02"][0] - 112, C["CU-02"][1])], TINTA, 1.1)
    s.linea([(ing[0] - 26, ing[1] + 30), (C["CU-02"][0] + 112, C["CU-02"][1])], TINTA, 1.1)
    s.linea([(exp_[0] - 26, exp_[1] + 30), C["CU-07"]], GRIS, 1.1, "6 4")
    caso(s, *C["CU-02"], "CU-02", "Iniciar sesión")
    caso(s, *C["CU-01"], "CU-01", "Registrarse como\naspirante")
    caso(s, *C["CU-03"], "CU-03", "Responder el cuestionario\nde evaluación")
    caso(s, *C["CU-05"], "CU-05", "Consultar el resultado\nde la evaluación")
    caso(s, *C["CU-08"], "CU-08", "Consultar el historial\nde evaluaciones")
    caso(s, *C["CU-04"], "CU-04", "Ejecutar la inferencia\nprobabilística", AMBAR_CLARO, AMBAR, 100, 36)
    caso(s, *C["CU-06"], "CU-06", "Consultar gránulos\npor hipótesis", VERDE_CLARO, VERDE)
    caso(s, *C["CU-07"], "CU-07", "Cargar y mantener el\nconocimiento del experto", VERDE_CLARO, VERDE)
    caso(s, *C["CU-09"], "CU-09", "Consultar reglas RN\ny rangos RC", VERDE_CLARO, VERDE)
    caso(s, *C["CU-10"], "CU-10", "Supervisar las\nevaluaciones", VERDE_CLARO, VERDE)
    # include
    s.linea([(455, 387), (528, 404)], TINTA, 1.2, "6 4", "abierta")
    s.texto(462, 418, "«include»", 11, "normal", "middle", TINTA, "italic")
    actor(s, *asp, "Aspirante", "rol del sistema")
    actor(s, *ing, "Ingeniero del\nconocimiento", "rol del sistema")
    actor(s, *exp_, "Experto en\norientación\nvocacional", "actor externo (simulado con IA)", GRIS)
    # Convenciones
    s.rect(250, 640, 700, 56, "#fff", GRIS, 0.8, 4)
    s.texto(262, 660, "Convenciones:", 11, "bold")
    s.add(f'<ellipse cx="290" cy="681" rx="18" ry="8" fill="{AZUL_CLARO}" stroke="{AZUL}"/>')
    s.texto(314, 685, "Aspirante", 11)
    s.add(f'<ellipse cx="400" cy="681" rx="18" ry="8" fill="{VERDE_CLARO}" stroke="{VERDE}"/>')
    s.texto(424, 685, "Ingeniero del conocimiento", 11)
    s.add(f'<ellipse cx="600" cy="681" rx="18" ry="8" fill="{AMBAR_CLARO}" stroke="{AMBAR}"/>')
    s.texto(624, 685, "Ejecutado por el sistema", 11)
    s.linea([(770, 681), (810, 681)], GRIS, 1.1, "6 4")
    s.texto(818, 685, "Actor externo", 11)
    s.guardar("CasosDeUso")


# ---------------------------------------------------------------------------------------------
# 2. Diagrama de clases DAO
# ---------------------------------------------------------------------------------------------
def clase(s, x, y, w, nombre, atributos=(), metodos=(), estereotipo="", nota="", color=AZUL, fondo=AZUL_CLARO):
    alto_cab = 30 + (16 if estereotipo else 0) + (15 if nota else 0)
    h = alto_cab + 10 + 17 * len(atributos) + (10 if atributos else 0) + 17 * len(metodos) + (8 if metodos else 0)
    s.rect(x, y, w, h, "#fff", color, 1.4)
    s.rect(x, y, w, alto_cab, fondo, color, 1.4)
    yy = y + 20
    if estereotipo:
        s.texto(x + w / 2, yy, estereotipo, 11, "normal", "middle", color, "italic")
        yy += 16
    s.texto(x + w / 2, yy, nombre, 14, "bold", "middle", TINTA, "italic" if "abstract" in estereotipo else "normal")
    if nota:
        s.texto(x + w / 2, yy + 15, nota, 10, "normal", "middle", GRIS, "italic")
    yy = y + alto_cab + 17
    for a in atributos:
        s.texto(x + 8, yy, a, 11.5)
        yy += 17
    if atributos:
        s.linea([(x, yy - 9), (x + w, yy - 9)], color, 1)
        yy += 6
    for m in metodos:
        s.texto(x + 8, yy, m, 11.5)
        yy += 17
    return h


def clases_dao():
    s = Svg(1200, 1330)
    # Fila superior: controladores, fachada y motor
    hc = clase(s, 20, 40, 300, "Controladores Flask", (),
               ("publico.bp: inicio, ingresar, registro, salir", "aspirante.bp: cuestionario, evaluar,", "    evaluacion, inicio",
                "ingeniero.bp: panel, granulos, granulo_*,", "    reglas, evaluaciones"),
               "«controlador»", "app/controlador", GRIS, GRIS_CLARO)
    hs = clase(s, 400, 20, 400, "SistemaExperto",
               ("+aspirantes: AspiranteDAO", "+ingenieros: IngenieroDAO", "+preguntas: PreguntaDAO",
                "+hechos: HechoDAO   +hipotesis: HipotesisDAO", "+granulos: GranuloDAO", "+reglas: ReglaNoConcluyenteDAO",
                "+evaluaciones: EvaluacionDAO", "+motor: MotorInferencia"),
               ("+registrar_aspirante(datos, contrasena): Aspirante", "+autenticar(rol, correo, contrasena)",
                "+evaluar(id_aspirante, textos): int", "+crear_granulo(id_ing, id_hecho, id_hip, peso): str",
                "+actualizar_granulo(id_ing, id_granulo, peso, activo)", "+resumen(): dict"),
               "«fachada del modelo»", "app/modelo/sistema_experto.py", AZUL, AZUL_CLARO)
    hm = clase(s, 880, 20, 300, "MotorInferencia",
               ("-_hechos: HechoDAO", "-_granulos: GranuloDAO", "-_reglas: ReglaNoConcluyenteDAO"),
               ("-_derivar(respuesta): Hecho", "+inferir(respuestas): ResultadoInferencia"),
               "«servicio»", "motor_inferencia.py", AMBAR, AMBAR_CLARO)
    ht = clase(s, 880, 230, 300, "TablaContabilizacion", ("-_conteos: dict",),
               ("+registrar(granulo, hecho)", "+calcular_probabilidades(): list"), "", "", AMBAR, AMBAR_CLARO)
    s.linea([(320, 40 + hc / 2), (400, 40 + hc / 2)], TINTA, 1.2, "6 4", "abierta")
    s.texto(360, 40 + hc / 2 - 6, "usa", 11, "normal", "middle", TINTA, "italic")
    s.linea([(800, 80), (880, 80)], TINTA, 1.2, None, None, "rombo")
    s.texto(840, 74, "1", 11, "normal", "middle")
    s.linea([(1030, 20 + hm), (1030, 230)], TINTA, 1.2, "6 4", "abierta")
    s.texto(1038, 20 + hm + (230 - 20 - hm) / 2 + 4, "crea", 11, "normal", "start", TINTA, "italic")

    # Paquete DAO
    top = 400
    s.rect(15, top, 1170, 590, "#FAFBFC", AZUL, 1.2, 4, "8 4")
    s.rect(15, top - 24, 210, 24, AZUL_CLARO, AZUL, 1.2)
    s.texto(26, top - 7, "paquete app.modelo.dao", 12, "bold", "start", AZUL)
    # composición fachada -> paquete
    s.linea([(600, 20 + hs), (600, top)], TINTA, 1.4, None, None, "rombo")
    s.texto(610, top - 12, "1 instancia de cada DAO (comparten la conexión de la petición)", 11, "normal", "start", TINTA, "italic")
    # motor -> DAO
    s.linea([(1030, 230 + ht), (1030, top)], TINTA, 1.2, "6 4", "abierta")
    s.texto(1038, top - 12, "consulta", 11, "normal", "start", TINTA, "italic")

    w, xs = 270, (30, 322, 614, 906)
    fila_a = [
        ("AspiranteDAO", "transaccional.aspirantes",
         ("+insertar(documento, nombres, apellidos,", "    correo, contrasena_hash): Aspirante", "+credenciales(correo): tuple", "+contar(): int")),
        ("IngenieroDAO", "conocimiento.ingenieros_conocimiento", ("+credenciales(correo): tuple",)),
        ("PreguntaDAO", "conocimiento.preguntas_cuestionario_...", ("+activas(): list<Pregunta>",)),
        ("HipotesisDAO", "conocimiento.hipotesis_programas", ("+activas(): list",)),
    ]
    ya = top + 30
    alturas_a = [clase(s, x, ya, w, n, (), m, "", t) for x, (n, t, m) in zip(xs, fila_a)]
    # BaseDAO en el centro
    yb = ya + max(alturas_a) + 60
    hb = clase(s, 420, yb, 360, "BaseDAO",
               ("#_conexion: callable  (conexion_actual)",),
               ("#_consultar(sql, parametros): list", "#_consultar_uno(sql, parametros): dict | None",
                "#_transaccion(): cursor  (COMMIT / ROLLBACK)"), "«abstract»", "base_dao.py", AZUL, "#C9DBEF")
    # herencia fila A -> BaseDAO (triángulo en el borde superior)
    bus_a = yb - 28
    for x, h in zip(xs, alturas_a):
        s.linea([(x + w / 2, ya + h), (x + w / 2, bus_a)], TINTA, 1.1)
    s.linea([(xs[0] + w / 2, bus_a), (xs[-1] + w / 2, bus_a)], TINTA, 1.1)
    s.linea([(600, bus_a), (600, yb)], TINTA, 1.1, None, "herencia")
    fila_b = [
        ("HechoDAO", "conocimiento.hechos_perfil (RC)",
         ("+derivar(respuesta): Hecho | None", "+listar(): list", "+rangos_por_variable(): dict")),
        ("GranuloDAO", "conocimiento.granulos_hecho_hipotesis (RG)",
         ("+por_hecho(id_hecho): list<Granulo>", "+listar(codigo_hipotesis): list", "+obtener(id_granulo): dict",
          "+resumen_por_hipotesis(): list", "+contar_activos(): int", "+insertar(id_hecho, id_hip, peso, id_ing): str",
          "+actualizar(id_granulo, peso, activo, id_ing)")),
        ("ReglaNoConcluyenteDAO", "conocimiento.reglas_resultado_no_... (RN)", ("+activas(): list<ReglaNoConcluyente>",)),
        ("EvaluacionDAO", "transaccional: 5 tablas de la evaluación",
         ("+insertar(id_asp, respuestas, resultado): int", "+listar_por_aspirante(id_aspirante): list",
          "+listar_todas(texto, limite): list", "+detalle(id_evaluacion): dict", "+contar(): int",
          "+programas_mas_frecuentes(limite): list")),
    ]
    yb2 = yb + hb + 60
    alturas_b = [clase(s, x, yb2, w, n, (), m, "", t) for x, (n, t, m) in zip(xs, fila_b)]
    bus_b = yb2 - 28
    for x in xs:
        s.linea([(x + w / 2, yb2), (x + w / 2, bus_b)], TINTA, 1.1)
    s.linea([(xs[0] + w / 2, bus_b), (xs[-1] + w / 2, bus_b)], TINTA, 1.1)
    s.linea([(600, bus_b), (600, yb + hb)], TINTA, 1.1, None, "herencia")

    # Conexión y base de datos
    yf = top + 610
    hf = clase(s, 420, yf + 20, 360, "FabricaConexion",
               ("-_pool: ThreadedConnectionPool (psycopg2)",),
               ("+obtener(): connection", "+devolver(conexion)", "+verificar()", "+cerrar()"),
               "", "app/modelo/conexion.py", GRIS, GRIS_CLARO)
    s.linea([(300, top + 590), (300, yf + 20 + hf / 2), (420, yf + 20 + hf / 2)], TINTA, 1.2, "6 4", "abierta")
    s.texto(310, yf + 20 + hf / 2 - 8, "usa la conexión", 11, "normal", "start", TINTA, "italic")
    # cilindro PostgreSQL
    cx, cy = 1000, yf + 40
    s.add(f'<path d="M{cx-110},{cy} v110 a110,18 0 0,0 220,0 v-110" fill="{AZUL_CLARO}" stroke="{AZUL}" stroke-width="1.4"/>')
    s.add(f'<ellipse cx="{cx}" cy="{cy}" rx="110" ry="18" fill="#C9DBEF" stroke="{AZUL}" stroke-width="1.4"/>')
    s.texto(cx, cy + 48, "PostgreSQL", 14, "bold", "middle", AZUL)
    s.texto(cx, cy + 68, "sistema_experto_orientacion", 11, "normal", "middle")
    s.texto(cx, cy + 86, "esquemas: conocimiento", 11, "normal", "middle")
    s.texto(cx, cy + 102, "y transaccional", 11, "normal", "middle")
    s.linea([(780, yf + 20 + hf / 2), (890, yf + 20 + hf / 2)], TINTA, 1.2, None, "flecha")
    s.texto(835, yf + 20 + hf / 2 - 8, "SQL", 11, "normal", "middle", TINTA, "italic")
    # Entidades
    ye = yf + 20 + hf + 30
    ent = ["Aspirante", "IngenieroConocimiento", "Pregunta", "Respuesta", "Hecho", "Granulo", "ReglaNoConcluyente",
           "ConteoHipotesis", "ResultadoInferencia"]
    s.rect(20, ye, 1160, 62, "#fff", GRIS, 1.2)
    s.texto(32, ye + 20, "«dataclass» entidades.py — objetos que devuelven los DAO y el motor:", 12, "bold", "start", GRIS)
    x = 32
    for e in ent:
        ancho = 12 + len(e) * 7.4
        s.rect(x, ye + 30, ancho, 22, GRIS_CLARO, GRIS, 0.9, 3)
        s.texto(x + ancho / 2, ye + 46, e, 11.5, "normal", "middle")
        x += ancho + 9
    s.linea([(120, top + 590), (120, ye)], TINTA, 1.2, "6 4", "abierta")
    s.texto(128, ye - 10, "devuelve", 11, "normal", "start", TINTA, "italic")
    s.alto = ye + 75
    s.guardar("Clases_DAO")


# ---------------------------------------------------------------------------------------------
# 3. Arquitectura de la aplicación web (MVC)
# ---------------------------------------------------------------------------------------------
def caja(s, x, y, w, h, titulo, lineas, color, fondo, sub=""):
    s.rect(x, y, w, h, "#fff", color, 1.5, 6)
    s.rect(x, y, w, 32, fondo, color, 1.5, 6)
    s.rect(x + 1, y + 20, w - 2, 12, fondo, fondo, 0)
    s.texto(x + w / 2, y + 21, titulo, 14, "bold", "middle", color)
    yy = y + 52
    if sub:
        s.texto(x + w / 2, yy - 2, sub, 11, "normal", "middle", GRIS, "italic")
        yy += 18
    for l in lineas:
        s.texto(x + 12, yy, l, 12)
        yy += 18


def arquitectura():
    s = Svg(1200, 560)
    # Navegador
    caja(s, 20, 150, 170, 200, "Navegador", ["Usuarios:", "", "Aspirante", "Ingeniero del", "conocimiento"],
         GRIS, GRIS_CLARO, "cliente HTTP")
    # Servidor
    s.rect(230, 20, 690, 520, "#FAFBFC", AZUL, 1.3, 6, "8 4")
    s.texto(245, 42, "Servidor de aplicación Python 3 — Flask (desarrollo) o waitress (producción)", 13, "bold", "start", AZUL)
    caja(s, 250, 60, 300, 210, "CONTROLADOR", ["publico.py: inicio, ingresar, registro, salir",
                                              "aspirante.py: cuestionario, resultado,", "    historial",
                                              "ingeniero.py: panel, gránulos, reglas,", "    evaluaciones",
                                              "sesion.py: sesión por rol y token CSRF"],
         VERDE, VERDE_CLARO, "app/controlador (Blueprints por rol)")
    caja(s, 250, 300, 300, 220, "VISTA", ["templates/publico, aspirante, ingeniero", "componentes/macros.html", "static/css/app.css, js/app.js",
                                         "filtros.py: porcentajes y fechas", "Mejora progresiva: funciona", "sin JavaScript"],
         AMBAR, AMBAR_CLARO, "app/vista (Jinja2 + CSS + JS)")
    caja(s, 600, 60, 300, 460, "MODELO", ["sistema_experto.py", "    SistemaExperto (fachada)", "motor_inferencia.py",
                                         "    MotorInferencia,", "    TablaContabilizacion", "dao/ (8 DAO + BaseDAO)",
                                         "    consultas parametrizadas", "entidades.py (dataclasses)", "validaciones.py",
                                         "    ErrorNegocio, ErroresFormulario", "seguridad.py (hash scrypt)", "conexion.py",
                                         "    FabricaConexion (pool)", "", "No conoce Flask ni HTML"],
         AZUL, AZUL_CLARO, "app/modelo")
    # BD
    cx, cy = 1060, 170
    s.add(f'<path d="M{cx-115},{cy} v190 a115,20 0 0,0 230,0 v-190" fill="{AZUL_CLARO}" stroke="{AZUL}" stroke-width="1.5"/>')
    s.add(f'<ellipse cx="{cx}" cy="{cy}" rx="115" ry="20" fill="#C9DBEF" stroke="{AZUL}" stroke-width="1.5"/>')
    for i, (t, b) in enumerate([("PostgreSQL 16/17", "bold"), ("local, Docker o Neon", "normal"), ("", "normal"),
                                ("esquema conocimiento", "bold"), ("hipótesis, hechos, gránulos,", "normal"),
                                ("reglas RN, ingenieros", "normal"), ("", "normal"), ("esquema transaccional", "bold"),
                                ("aspirantes, evaluaciones,", "normal"), ("contabilización, resultado", "normal")]):
        s.texto(cx, cy + 45 + i * 17, t, 12, b, "middle", AZUL if b == "bold" else TINTA)
    # Flechas numeradas
    def paso(n, x, y):
        s.add(f'<circle cx="{x}" cy="{y}" r="11" fill="{TINTA}"/>')
        s.texto(x, y + 4.5, str(n), 12, "bold", "middle", "#fff")
    s.linea([(190, 200), (250, 200)], TINTA, 1.5, None, "flecha"); paso(1, 220, 185)
    s.texto(220, 222, "petición", 10, "normal", "middle", TINTA, "italic")
    s.linea([(550, 140), (600, 140)], TINTA, 1.5, None, "flecha"); paso(2, 575, 125)
    s.linea([(900, 230), (945, 230)], TINTA, 1.5, None, "flecha", "flecha"); paso(3, 922, 212)
    s.texto(922, 252, "SQL", 10, "normal", "middle", TINTA, "italic")
    s.linea([(600, 230), (550, 230)], TINTA, 1.5, None, "flecha"); paso(4, 575, 215)
    s.linea([(400, 270), (400, 300)], TINTA, 1.5, None, "flecha"); paso(5, 420, 285)
    s.linea([(250, 420), (105, 420), (105, 350)], TINTA, 1.5, None, "flecha"); paso(6, 175, 420)
    s.texto(175, 445, "HTML", 10, "normal", "middle", TINTA, "italic")
    s.texto(1060, 470, "1 petición → 1 conexión del pool", 11, "normal", "middle", GRIS, "italic")
    s.texto(1060, 487, "compartida por todos los DAO", 11, "normal", "middle", GRIS, "italic")
    s.guardar("Arquitectura_Web_MVC")


casos_de_uso()
clases_dao()
arquitectura()
