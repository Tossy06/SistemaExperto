"""Fachada del MODELO: único objeto que usan los controladores.

Instancia un DAO por tabla y el motor de inferencia, y ofrece las operaciones de negocio
(registrar, autenticar, evaluar, mantener gránulos). Las lecturas simples se hacen directo con los DAO,
p. ej. `sistema.evaluaciones.detalle(5)`.
"""
from app.modelo.dao.evaluacion_dao import EvaluacionDAO
from app.modelo.dao.granulo_dao import GranuloDAO
from app.modelo.dao.hecho_dao import HechoDAO
from app.modelo.dao.hipotesis_dao import HipotesisDAO
from app.modelo.dao.pregunta_dao import PreguntaDAO
from app.modelo.dao.regla_no_concluyente_dao import ReglaNoConcluyenteDAO
from app.modelo.dao.usuario_dao import AspiranteDAO, IngenieroDAO
from app.modelo.motor_inferencia import HechoNoDerivable, MotorInferencia
from app.modelo.seguridad import generar_hash, verificar_contrasena
from app.modelo.validaciones import ErroresFormulario, ErrorNegocio, validar_peso, validar_registro, validar_respuesta


class SistemaExperto:
    def __init__(self, conexion_actual):
        # DAO (uno por tabla o agregado), todos con la misma fuente de conexión.
        self.aspirantes = AspiranteDAO(conexion_actual)
        self.ingenieros = IngenieroDAO(conexion_actual)
        self.preguntas = PreguntaDAO(conexion_actual)
        self.hechos = HechoDAO(conexion_actual)
        self.hipotesis = HipotesisDAO(conexion_actual)
        self.granulos = GranuloDAO(conexion_actual)
        self.reglas = ReglaNoConcluyenteDAO(conexion_actual)
        self.evaluaciones = EvaluacionDAO(conexion_actual)
        # Motor de inferencia: consulta la base de conocimiento a través de los DAO.
        self.motor = MotorInferencia(self.hechos, self.granulos, self.reglas)

    # ---------- CU-01 y CU-02: usuarios ----------
    def registrar_aspirante(self, datos: dict, contrasena: str):
        datos = {campo: valor.strip() for campo, valor in datos.items()}
        datos["correo"] = datos["correo"].lower()
        validar_registro(datos, contrasena)
        return self.aspirantes.insertar(**datos, contrasena_hash=generar_hash(contrasena))

    def autenticar(self, rol: str, correo: str, contrasena: str):
        """Devuelve el Aspirante o el IngenieroConocimiento si el correo y la contraseña coinciden."""
        dao = {"aspirante": self.aspirantes, "ingeniero": self.ingenieros}.get(rol)
        credenciales = dao and dao.credenciales(correo.strip().lower())
        if not credenciales or not verificar_contrasena(contrasena, credenciales[1]):
            raise ErrorNegocio("El correo o la contraseña no coinciden. Revíselos e intente de nuevo.")
        return credenciales[0]

    # ---------- CU-03 y CU-04: evaluación vocacional ----------
    def evaluar(self, id_aspirante: int, textos: dict) -> int:
        """Valida las 11 respuestas, ejecuta el motor y guarda la evaluación. Devuelve su número."""
        preguntas = self.preguntas.activas()
        respuestas, errores = [], {}
        for p in preguntas:
            try:
                respuestas.append(validar_respuesta(p, (textos.get(p.codigo_variable) or "").strip()))
            except ValueError as error:
                errores[p.codigo_variable] = str(error)
        if errores:
            raise ErroresFormulario(errores)
        try:
            resultado = self.motor.inferir(respuestas)
        except HechoNoDerivable as error:
            codigo = next(p.codigo_variable for p in preguntas if p.id_pregunta == error.id_pregunta)
            raise ErroresFormulario({codigo: str(error)})
        return self.evaluaciones.insertar(id_aspirante, respuestas, resultado)

    # ---------- CU-07: mantenimiento de la base de conocimiento ----------
    def crear_granulo(self, id_ingeniero, id_hecho, id_hipotesis, peso_texto) -> str:
        errores = {}
        if not str(id_hecho).isdigit():
            errores["id_hecho"] = "Elija el dato del perfil que activa la regla."
        if not str(id_hipotesis).isdigit():
            errores["id_hipotesis"] = "Elija el programa académico."
        try:
            peso = validar_peso(peso_texto)
        except ErroresFormulario as error:
            errores.update(error.errores)
        if errores:
            raise ErroresFormulario(errores)
        return self.granulos.insertar(int(id_hecho), int(id_hipotesis), peso, id_ingeniero)

    def actualizar_granulo(self, id_ingeniero, id_granulo, peso_texto, activo: bool):
        self.granulos.actualizar(id_granulo, validar_peso(peso_texto), activo, id_ingeniero)

    # ---------- Panel del ingeniero ----------
    def resumen(self) -> dict:
        return {"hipotesis": len(self.hipotesis.activas()), "granulos": self.granulos.contar_activos(),
                "aspirantes": self.aspirantes.contar(), "evaluaciones": self.evaluaciones.contar(),
                "frecuentes": self.evaluaciones.programas_mas_frecuentes(),
                "por_hipotesis": self.granulos.resumen_por_hipotesis()}
