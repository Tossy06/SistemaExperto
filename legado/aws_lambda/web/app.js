const API = window.API_URL.replace(/\/$/, "");

// Mismos grupos de la aplicación de escritorio.
const GRUPOS = [
  { tipo: "AREA", titulo: "Desempeño por área académica", ayuda: "Promedio de 1.0 a 5.0", columnas: 1 },
  { tipo: "INTERES", titulo: "Intereses vocacionales (test RIASEC)", ayuda: "Porcentaje de 0 a 100", columnas: 2 },
  { tipo: "ESTILO", titulo: "Estilo de trabajo", ayuda: "Seleccione una opción", columnas: 1 },
];

const EJEMPLO = {
  "DES-LM": "4.5", "DES-CI": "3.7", "DES-SH": "3.0", "DES-AF": "3.6",
  "INT-R": "50", "INT-I": "85", "INT-A": "20", "INT-S": "45", "INT-E": "30", "INT-C": "55",
  "EST": "Independiente",
};

const estado = document.getElementById("estado");
const formulario = document.getElementById("cuestionario");
const botonEvaluar = document.getElementById("evaluar");
const pestanas = {
  cuestionario: [document.getElementById("tab-cuestionario"), document.getElementById("panel-cuestionario")],
  resultado: [document.getElementById("tab-resultado"), document.getElementById("panel-resultado")],
};

function crear(etiqueta, texto, clase) {
  const elemento = document.createElement(etiqueta);
  if (texto !== undefined) elemento.textContent = texto;
  if (clase) elemento.className = clase;
  return elemento;
}

function porcentaje(valor) {
  return `${valor.toFixed(2)} %`;
}

function mostrarPestana(nombre) {
  Object.entries(pestanas).forEach(([clave, [boton, panel]]) => {
    boton.setAttribute("aria-selected", String(clave === nombre));
    panel.hidden = clave !== nombre;
  });
}

function crearCampo(pregunta) {
  if (pregunta.tipo_respuesta === "OPCION") {
    const lista = crear("select");
    lista.append(new Option("Seleccione…", ""));
    pregunta.opciones.forEach((opcion) => lista.append(new Option(opcion, opcion)));
    return lista;
  }
  const campo = crear("input");
  campo.type = "text";
  campo.inputMode = "decimal";
  campo.autocomplete = "off";
  return campo;
}

function crearCelda(pregunta) {
  const celda = crear("div", undefined, "celda");
  const etiqueta = crear("label", pregunta.nombre.replace("Desempeño ", "").replace("Interés ", ""));
  const campo = crearCampo(pregunta);
  campo.id = `campo-${pregunta.codigo}`;
  campo.name = pregunta.codigo;
  campo.title = pregunta.enunciado;
  etiqueta.htmlFor = campo.id;
  const error = crear("p", "", "error");
  error.id = `error-${pregunta.codigo}`;
  celda.append(etiqueta, campo, error);
  return celda;
}

function mostrarPreguntas(preguntas) {
  const contenedor = document.getElementById("grupos");
  GRUPOS.forEach((grupo) => {
    const marco = crear("fieldset", undefined, `grupo grupo-${grupo.columnas}`);
    const campos = crear("div", undefined, "campos");
    campos.append(...preguntas.filter((p) => p.tipo_variable === grupo.tipo).map(crearCelda));
    marco.append(crear("legend", grupo.titulo), crear("p", grupo.ayuda, "ayuda"), campos);
    contenedor.append(marco);
  });
}

function mostrarErrores(errores) {
  document.querySelectorAll(".error").forEach((e) => { e.textContent = ""; });
  document.querySelectorAll("[aria-invalid]").forEach((c) => c.removeAttribute("aria-invalid"));
  Object.entries(errores).forEach(([codigo, mensaje]) => {
    document.getElementById(`error-${codigo}`).textContent = mensaje;
    document.getElementById(`campo-${codigo}`).setAttribute("aria-invalid", "true");
  });
}

function filaTabla(celdas) {
  const fila = crear("tr");
  celdas.forEach(([texto, clase]) => fila.append(crear("td", texto, clase)));
  return fila;
}

function mostrarGrafico(recomendaciones) {
  const maximo = Math.max(...recomendaciones.map((h) => h.probabilidad)) || 1;
  document.getElementById("grafico").replaceChildren(...recomendaciones.map((h, indice) => {
    const fila = crear("div", undefined, indice === 0 ? "barra-fila primera" : "barra-fila");
    const pista = crear("div", undefined, "pista");
    const relleno = crear("div", undefined, "relleno");
    relleno.style.width = `${(h.probabilidad / maximo) * 100}%`;
    pista.append(relleno);
    fila.append(crear("span", `${indice + 1}.  ${h.codigo}  ${h.programa}`, "barra-nombre"), pista,
                crear("span", porcentaje(h.probabilidad), "barra-valor"));
    return fila;
  }));
}

function mostrarResultado(datos) {
  mostrarGrafico(datos.recomendaciones);

  document.getElementById("marcas").replaceChildren(...datos.marcas.map(
    (m) => crear("p", `Resultado no concluyente (${m.codigo}): ${m.descripcion}`, "marca")));

  document.getElementById("contabilizacion").replaceChildren(...datos.contabilizacion.map((h) => filaTabla([
    [h.codigo], [h.programa], [String(h.coincidencias), "centro"],
    [h.suma_pesos.toFixed(2), "centro"], [porcentaje(h.probabilidad), "derecha"],
  ])));

  document.getElementById("coincidencias").replaceChildren(...datos.recomendaciones.flatMap(
    (h) => h.reglas.map((r) => filaTabla([[h.codigo], [r.regla], [r.hecho], [r.peso.toFixed(2), "derecha"]]))));

  document.getElementById("traza").replaceChildren(...datos.traza.map(
    (c) => crear("li", `Ciclo ${c.ciclo}: ${c.reglas.length} reglas disparadas (${c.reglas.join(", ")})`)));

  pestanas.resultado[0].disabled = false;
  mostrarPestana("resultado");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function enviar(evento) {
  evento.preventDefault();
  botonEvaluar.disabled = true;
  estado.textContent = "Analizando sus respuestas…";
  try {
    const respuesta = await fetch(`${API}/inferir`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ respuestas: Object.fromEntries(new FormData(formulario)) }),
    });
    const datos = await respuesta.json();
    if (respuesta.status === 422 && datos.detail.errores) {
      mostrarErrores(datos.detail.errores);
      estado.textContent = "Revise las respuestas marcadas.";
      return;
    }
    if (!respuesta.ok) throw new Error(`La API respondió ${respuesta.status}`);
    mostrarErrores({});
    estado.textContent = "";
    mostrarResultado(datos);
  } catch (error) {
    console.error(error);
    estado.textContent = "No se pudo obtener el resultado. Intente de nuevo.";
  } finally {
    botonEvaluar.disabled = false;
  }
}

function limpiar() {
  formulario.reset();
  mostrarErrores({});
  estado.textContent = "";
}

function cargarEjemplo() {
  limpiar();
  Object.entries(EJEMPLO).forEach(([codigo, valor]) => {
    document.getElementById(`campo-${codigo}`).value = valor;
  });
}

async function iniciar() {
  try {
    const respuesta = await fetch(`${API}/preguntas`);
    if (!respuesta.ok) throw new Error(`La API respondió ${respuesta.status}`);
    mostrarPreguntas(await respuesta.json());
    estado.textContent = "";
    formulario.hidden = false;
  } catch (error) {
    console.error(error);
    estado.textContent = "No se pudo conectar con la API. Recargue la página en un momento.";
  }
}

formulario.addEventListener("submit", enviar);
document.getElementById("limpiar").addEventListener("click", limpiar);
document.getElementById("ejemplo").addEventListener("click", cargarEjemplo);
Object.entries(pestanas).forEach(([nombre, [boton]]) => {
  boton.addEventListener("click", () => mostrarPestana(nombre));
});
iniciar();
