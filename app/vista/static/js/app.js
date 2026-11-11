/* Mejoras progresivas de la interfaz. Todo funciona también sin JavaScript. */
(function () {
  "use strict";
  document.documentElement.classList.add("js");

  /* ---------- Pestañas Ingresar / Crear cuenta ---------- */
  document.querySelectorAll("[data-pestanas]").forEach(function (lista) {
    var pestanas = Array.prototype.slice.call(lista.querySelectorAll('[role="tab"]'));
    function activar(pestana, enfocar) {
      pestanas.forEach(function (p) {
        var activa = p === pestana;
        p.setAttribute("aria-selected", activa ? "true" : "false");
        p.tabIndex = activa ? 0 : -1;
        document.getElementById(p.getAttribute("aria-controls")).hidden = !activa;
      });
      if (enfocar) pestana.focus();
      var primerCampo = document.getElementById(pestana.getAttribute("aria-controls")).querySelector("input:not([type=hidden]):not([type=radio])");
      if (primerCampo && !enfocar) primerCampo.focus();
    }
    pestanas.forEach(function (p, i) {
      p.tabIndex = p.getAttribute("aria-selected") === "true" ? 0 : -1;
      p.addEventListener("click", function (e) { e.preventDefault(); activar(p, false); });
      p.addEventListener("keydown", function (e) {
        var destino = { ArrowRight: i + 1, ArrowLeft: i - 1 }[e.key];
        if (destino === undefined) return;
        e.preventDefault();
        activar(pestanas[(destino + pestanas.length) % pestanas.length], true);
      });
    });
  });

  /* ---------- Cuestionario ----------
     Sin JavaScript se ven los tres bloques y se envía desde el panel lateral. Con JavaScript se muestra paso a paso:
     un bloque a la vez, cada bloque se revisa antes de avanzar y al final hay una revisión de todas las respuestas.
     La validación definitiva siempre la hace el servidor. */
  var formulario = document.querySelector("[data-cuestionario]");
  if (formulario) {
    var rangos = JSON.parse(document.getElementById("rangos-clasificacion").textContent);
    var nombres = JSON.parse(document.getElementById("nombres-variables").textContent);
    var ejemplo = JSON.parse(document.getElementById("respuestas-ejemplo").textContent);
    var total = Number(formulario.dataset.total);
    var preguntas = Array.prototype.slice.call(formulario.querySelectorAll("[data-pregunta]"));
    var pasos = Array.prototype.slice.call(formulario.querySelectorAll("[data-paso]"));
    var revision = formulario.querySelector("[data-revision]");
    var lista = formulario.querySelector("[data-pasos-lista]");
    var actual = 0, visitado = 0;

    function numero(texto) {
      var limpio = String(texto).trim().replace(",", ".");
      return limpio === "" || isNaN(limpio) ? null : Number(limpio);
    }
    function decimal(n, decimales) { return n.toFixed(decimales === undefined ? 1 : decimales).replace(".", ","); }
    function claseCss(texto) {
      return texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-");
    }

    // La clasificación se calcula con los rangos de la base de conocimiento (no hay valores fijos aquí).
    // `valor` es el promedio (variables RANGO) o la posición (variables POSICION).
    function clasificar(codigoVariable, valor) {
      var rangosVariable = (rangos[codigoVariable] || {}).rangos || [];
      var redondeado = Math.round(valor * 100) / 100;
      for (var i = 0; i < rangosVariable.length; i++) {
        if (redondeado >= rangosVariable[i].minimo && redondeado <= rangosVariable[i].maximo) return rangosVariable[i].valor;
      }
      return null;
    }

    function etiquetaNivel(clase) {
      var etiqueta = document.createElement("span");
      etiqueta.className = "nivel nivel-" + claseCss(clase);
      etiqueta.textContent = clase;
      return etiqueta;
    }

    // Valor marcado en una pregunta de escala, o null.
    function marcado(bloque) {
      var opcion = bloque.querySelector("input[type=radio]:checked");
      return opcion ? Number(opcion.value) : null;
    }

    function actualizarPregunta(bloque) {
      var campo = bloque.querySelector(".valor-numerico");
      var salida = bloque.querySelector(".clasificacion");
      if (!campo) {   // escala: se clasifica solo si la variable usa rangos (p. ej. el estilo de trabajo)
        if (!salida) return;
        var punto = marcado(bloque);
        var claseEscala = punto === null ? null : clasificar(bloque.dataset.variable, punto);
        salida.innerHTML = "";
        if (claseEscala) salida.appendChild(etiquetaNivel(claseEscala));
        return;
      }
      var deslizador = bloque.querySelector(".deslizador");
      var valor = numero(campo.value);
      var clase = valor === null ? null : clasificar(bloque.dataset.variable, valor);
      salida.innerHTML = "";
      if (clase) salida.appendChild(etiquetaNivel(clase));
      else if (valor !== null) salida.textContent = "Fuera de rango";
      if (valor !== null && deslizador) {
        deslizador.value = valor;
        deslizador.removeAttribute("data-vacio");
      }
    }

    // Mensaje de error de una pregunta, o null si está bien respondida.
    function problema(bloque) {
      var campo = bloque.querySelector(".valor-numerico");
      if (!campo) return bloque.querySelector("input[type=radio]:checked") ? null : "Elija una opción.";
      if (campo.value.trim() === "") return "Responda esta pregunta.";
      var valor = numero(campo.value);
      var minimo = Number(bloque.dataset.minimo), maximo = Number(bloque.dataset.maximo);
      if (valor === null || valor < minimo || valor > maximo || !clasificar(bloque.dataset.variable, valor))
        return "Escriba un número entre " + decimal(minimo) + " y " + decimal(maximo) + ".";
      return null;
    }
    function respondida(bloque) { return problema(bloque) === null; }

    function marcarError(bloque, mensaje) {
      var salida = bloque.querySelector(".campo-error");
      var campo = bloque.querySelector(".valor-numerico");
      bloque.classList.toggle("campo-con-error", !!mensaje);
      if (salida) { salida.textContent = mensaje || ""; salida.hidden = !mensaje; }
      if (campo) {
        if (mensaje) campo.setAttribute("aria-invalid", "true");
        else campo.removeAttribute("aria-invalid");
      }
    }

    // Vista previa del código Holland: promedio de los ítems de cada tipo RIASEC y posición con empates compartidos
    // (como DENSE_RANK en el servidor). La posición se clasifica con los rangos de la base de conocimiento.
    function actualizarHolland() {
      var panel = formulario.querySelector("[data-holland]");
      if (!panel) return;
      var grupos = {}, orden = [];
      panel.closest("fieldset").querySelectorAll("[data-pregunta]").forEach(function (bloque) {
        var codigo = bloque.dataset.variable;
        if (!grupos[codigo]) { grupos[codigo] = []; orden.push(codigo); }
        grupos[codigo].push(marcado(bloque));
      });
      var completos = orden.filter(function (c) { return grupos[c].every(function (v) { return v !== null; }); })
        .map(function (c) {
          var suma = grupos[c].reduce(function (a, v) { return a + v; }, 0);
          return { codigo: c, promedio: Math.round(suma / grupos[c].length * 100) / 100 };
        });
      var distintos = completos.map(function (f) { return f.promedio; })
        .filter(function (v, i, todos) { return todos.indexOf(v) === i; }).sort(function (a, b) { return b - a; });
      var listaHolland = panel.querySelector(".holland-lista");
      listaHolland.innerHTML = "";
      if (completos.length < orden.length) return;   // las posiciones solo tienen sentido con los seis tipos
      completos.sort(function (a, b) { return b.promedio - a.promedio; }).forEach(function (f) {
        var posicion = distintos.indexOf(f.promedio) + 1;
        var li = document.createElement("li");
        var lugar = document.createElement("span"); lugar.className = "cifra"; lugar.textContent = posicion + ".º";
        var nombre = document.createElement("span"); nombre.textContent = (nombres[f.codigo] || f.codigo).replace("Interés ", "");
        var cifra = document.createElement("span"); cifra.className = "cifra"; cifra.textContent = decimal(f.promedio, 2);
        var nivel = document.createElement("span");
        var clase = clasificar(f.codigo, posicion);
        if (clase) nivel.appendChild(etiquetaNivel(clase));
        li.appendChild(lugar); li.appendChild(nombre); li.appendChild(cifra); li.appendChild(nivel);
        listaHolland.appendChild(li);
      });
    }

    function preguntasDe(paso) { return Array.prototype.slice.call(paso.querySelectorAll("[data-pregunta]")); }
    function pasoCompleto(paso) { return preguntasDe(paso).every(respondida); }

    function actualizarProgreso() {
      var n = preguntas.filter(respondida).length;
      formulario.querySelector("[data-respondidas]").textContent = n;
      formulario.querySelector("[data-barra-progreso]").style.width = (n / total * 100) + "%";
      actualizarHolland();
      actualizarLista();
    }

    /* ----- Paso a paso ----- */
    function primerPasoIncompleto(hasta) {
      for (var i = 0; i < hasta; i++) if (pasos[i] !== revision && !pasoCompleto(pasos[i])) return i;
      return -1;
    }

    function actualizarLista() {
      if (!formulario.classList.contains("asistente")) return;
      Array.prototype.forEach.call(lista.querySelectorAll("button"), function (boton, i) {
        var esRevision = pasos[i] === revision;
        var completo = !esRevision && pasoCompleto(pasos[i]);
        var del = esRevision ? [] : preguntasDe(pasos[i]);
        boton.classList.toggle("pasos-completo", completo && i !== actual);
        boton.disabled = i > visitado && primerPasoIncompleto(i) !== -1;
        if (i === actual) boton.setAttribute("aria-current", "step");
        else boton.removeAttribute("aria-current");
        boton.querySelector(".pasos-estado").textContent =
          esRevision ? "" : (completo ? "Listo" : del.filter(respondida).length + "/" + del.length);
      });
    }

    function llenarRevision() {
      var contenedor = revision.querySelector("[data-revision-bloques]");
      contenedor.innerHTML = "";
      pasos.forEach(function (paso, i) {
        if (paso === revision) return;
        var bloque = document.createElement("div");
        bloque.className = "revision-bloque";
        var cabecera = document.createElement("div");
        cabecera.className = "revision-cabecera";
        var titulo = document.createElement("h3");
        titulo.textContent = (i + 1) + ". " + paso.dataset.tituloCorto;
        var editar = document.createElement("button");
        editar.type = "button";
        editar.className = "boton boton-texto";
        editar.textContent = "Editar";
        editar.setAttribute("aria-label", "Editar " + paso.dataset.tituloCorto);
        editar.addEventListener("click", function () { mostrar(i, true); });
        cabecera.appendChild(titulo);
        cabecera.appendChild(editar);
        bloque.appendChild(cabecera);
        var ul = document.createElement("ul");
        ul.className = "revision-lista";
        preguntasDe(paso).forEach(function (p) {
          var li = document.createElement("li");
          var nombre = document.createElement("span");
          nombre.textContent = p.dataset.nombre;
          var cifra = document.createElement("span");
          cifra.className = "cifra";
          var nivel = document.createElement("span");
          var campo = p.querySelector(".valor-numerico");
          if (campo) {
            var valor = numero(campo.value);
            var clase = valor === null ? null : clasificar(p.dataset.variable, valor);
            cifra.textContent = campo.value.trim() === "" ? "—" : campo.value.trim();
            if (clase) nivel.appendChild(etiquetaNivel(clase));
          } else {
            var punto = marcado(p);
            cifra.textContent = punto === null ? "—" : punto + " de 5";
            var claseEscala = punto === null || !p.querySelector(".clasificacion") ? null : clasificar(p.dataset.variable, punto);
            if (claseEscala) nivel.appendChild(etiquetaNivel(claseEscala));
          }
          if (!respondida(p)) { nivel.className = "revision-falta"; nivel.textContent = "Falta"; }
          li.appendChild(nombre); li.appendChild(cifra); li.appendChild(nivel);
          ul.appendChild(li);
        });
        bloque.appendChild(ul);
        contenedor.appendChild(bloque);
      });
    }

    function mostrar(i, enfocar) {
      actual = i;
      visitado = Math.max(visitado, i);
      pasos.forEach(function (paso, j) { paso.hidden = j !== i; });
      if (pasos[i] === revision) llenarRevision();
      actualizarLista();
      if (enfocar) {
        var reducido = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        pasos[i].scrollIntoView({ block: "start", behavior: reducido ? "auto" : "smooth" });
        pasos[i].querySelector("legend, .paso-legend").focus({ preventScroll: true });
      }
    }

    // Marca los errores del paso y lleva el foco al primero. Devuelve true si el paso está completo.
    function validarPaso(i) {
      var primero = null;
      preguntasDe(pasos[i]).forEach(function (p) {
        var mensaje = problema(p);
        marcarError(p, mensaje);
        if (mensaje && !primero) primero = p;
      });
      if (primero) primero.querySelector(".valor-numerico, input[type=radio]").focus();
      return !primero;
    }

    function avanzar() {
      if (validarPaso(actual)) mostrar(actual + 1, true);
    }

    function iniciarAsistente() {
      formulario.classList.add("asistente");
      pasos.forEach(function (paso) {
        var navegacion = paso.querySelector("[data-navegacion]");
        if (navegacion) navegacion.hidden = false;
        var siguiente = paso.querySelector("[data-siguiente]");
        if (siguiente) siguiente.addEventListener("click", avanzar);
        var anterior = paso.querySelector("[data-anterior]");
        if (anterior) anterior.addEventListener("click", function () { mostrar(actual - 1, true); });
      });
      pasos.forEach(function (paso, i) {
        var li = document.createElement("li");
        var boton = document.createElement("button");
        boton.type = "button";
        boton.innerHTML = '<span class="pasos-numero" aria-hidden="true"></span><span class="pasos-nombre"></span><span class="pasos-estado"></span>';
        boton.querySelector(".pasos-numero").textContent = i + 1;
        boton.querySelector(".pasos-nombre").textContent = paso.dataset.tituloCorto;
        boton.addEventListener("click", function () {
          var pendiente = primerPasoIncompleto(i);
          if (i > actual && pendiente !== -1) {  // no se salta un bloque incompleto
            mostrar(pendiente, true);
            validarPaso(pendiente);
          } else {
            mostrar(i, true);
          }
        });
        li.appendChild(boton);
        lista.appendChild(li);
      });
      lista.hidden = false;

      // Enter en un campo pasa al siguiente bloque en lugar de enviar el formulario a medias.
      formulario.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && e.target.tagName === "INPUT" && pasos[actual] !== revision) {
          e.preventDefault();
          avanzar();
        }
      });
      formulario.addEventListener("submit", function (e) {
        var pendiente = primerPasoIncompleto(pasos.length);
        if (pendiente !== -1) {
          e.preventDefault();
          mostrar(pendiente, true);
          validarPaso(pendiente);
        }
      });

      // Al volver del servidor con errores, abrir el primer bloque que los tiene.
      var conError = -1;
      pasos.forEach(function (paso, i) { if (conError < 0 && paso.querySelector(".campo-con-error")) conError = i; });
      if (conError >= 0) visitado = pasos.length - 1;
      mostrar(Math.max(conError, 0), false);
    }

    preguntas.forEach(function (bloque) {
      var campo = bloque.querySelector(".valor-numerico");
      var deslizador = bloque.querySelector(".deslizador");
      function alCambiar() {
        actualizarPregunta(bloque);
        if (bloque.classList.contains("campo-con-error") && respondida(bloque)) marcarError(bloque, null);
        actualizarProgreso();
      }
      if (deslizador && campo) {
        deslizador.addEventListener("input", function () {
          var decimales = deslizador.step.indexOf(".") >= 0 ? 1 : 0;
          campo.value = Number(deslizador.value).toFixed(decimales).replace(".", ",");
          deslizador.removeAttribute("data-vacio");
          alCambiar();
        });
        campo.addEventListener("input", alCambiar);
      }
      bloque.addEventListener("change", alCambiar);
      actualizarPregunta(bloque);
    });

    if (revision && lista) iniciarAsistente();
    actualizarProgreso();

    formulario.querySelector("[data-ejemplo]").addEventListener("click", function () {
      preguntas.forEach(function (bloque) {
        var valor = ejemplo[bloque.dataset.pregunta];
        if (valor === undefined) return;
        var campo = bloque.querySelector(".valor-numerico");
        if (campo) {
          campo.value = String(valor).replace(".", ",");
          actualizarPregunta(bloque);
        } else {
          var opcion = bloque.querySelector('input[type=radio][value="' + valor + '"]');
          if (opcion) opcion.checked = true;
          actualizarPregunta(bloque);
        }
        if (respondida(bloque)) marcarError(bloque, null);
      });
      actualizarProgreso();
      if (formulario.classList.contains("asistente")) {
        visitado = pasos.length - 1;
        mostrar(pasos.indexOf(revision), true);
      }
    });

    formulario.querySelector("[data-limpiar]").addEventListener("click", function () {
      preguntas.forEach(function (bloque) {
        var campo = bloque.querySelector(".valor-numerico");
        if (campo) {
          campo.value = "";
          var deslizador = bloque.querySelector(".deslizador");
          if (deslizador) deslizador.setAttribute("data-vacio", "");
          actualizarPregunta(bloque);
        }
        bloque.querySelectorAll("input[type=radio]").forEach(function (r) { r.checked = false; });
        actualizarPregunta(bloque);
        marcarError(bloque, null);
      });
      if (formulario.classList.contains("asistente")) { visitado = 0; mostrar(0, false); }
      actualizarProgreso();
      preguntas[0].querySelector("input:not([type=range])").focus();
    });

    // Al volver con errores, llevar el foco a la primera respuesta marcada (en el bloque visible).
    var primerError = formulario.querySelector('.paso:not([hidden]) [aria-invalid="true"], .paso:not([hidden]) .campo-con-error input');
    if (primerError) primerError.focus();
  }

  /* ---------- Filtro con envío automático ---------- */
  document.querySelectorAll("[data-envio-automatico] select").forEach(function (lista) {
    lista.addEventListener("change", function () { lista.form.submit(); });
  });

  /* ---------- Imprimir resultado ---------- */
  document.querySelectorAll("[data-imprimir]").forEach(function (boton) {
    boton.addEventListener("click", function () { window.print(); });
  });
  window.addEventListener("beforeprint", function () {
    document.querySelectorAll("details").forEach(function (d) { d.open = true; });
  });
})();
