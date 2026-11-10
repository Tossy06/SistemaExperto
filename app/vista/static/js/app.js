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
    // Las notas (escala hasta 10) se muestran con un decimal; los porcentajes, sin decimales.
    function decimal(n, maximo) { return n.toFixed(maximo <= 10 ? 1 : 0).replace(".", ","); }

    // La clasificación se calcula con los rangos de la base de conocimiento (no hay valores fijos aquí).
    function clasificar(codigo, valor) {
      var rangosVariable = rangos[codigo] || [];
      var redondeado = Math.round(valor * 100) / 100;
      for (var i = 0; i < rangosVariable.length; i++) {
        if (redondeado >= rangosVariable[i].minimo && redondeado <= rangosVariable[i].maximo) return rangosVariable[i].valor;
      }
      return null;
    }

    function etiquetaNivel(clase) {
      var etiqueta = document.createElement("span");
      etiqueta.className = "nivel nivel-" + clase.toLowerCase();
      etiqueta.textContent = clase;
      return etiqueta;
    }

    function actualizarPregunta(bloque) {
      var campo = bloque.querySelector(".valor-numerico");
      if (!campo) return;
      var salida = bloque.querySelector(".clasificacion");
      var deslizador = bloque.querySelector(".deslizador");
      var valor = numero(campo.value);
      var clase = valor === null ? null : clasificar(bloque.dataset.pregunta, valor);
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
      if (valor === null || valor < minimo || valor > maximo || !clasificar(bloque.dataset.pregunta, valor))
        return "Escriba un número entre " + decimal(minimo, maximo) + " y " + decimal(maximo, maximo) + ".";
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

    // Aviso informativo, no bloqueante: si todos los porcentajes respondidos de un paso son menores que 5,
    // probablemente se usó una escala de 1 a 5. El formulario se puede enviar igual.
    function revisarEscala() {
      formulario.querySelectorAll("[data-aviso-escala]").forEach(function (aviso) {
        var valores = Array.prototype.slice.call(aviso.closest("fieldset").querySelectorAll(".valor-numerico"))
          .map(function (campo) { return numero(campo.value); })
          .filter(function (v) { return v !== null; });
        aviso.hidden = !(valores.length >= 3 && valores.every(function (v) { return v < 5; }));
      });
    }

    function preguntasDe(paso) { return Array.prototype.slice.call(paso.querySelectorAll("[data-pregunta]")); }
    function pasoCompleto(paso) { return preguntasDe(paso).every(respondida); }

    function actualizarProgreso() {
      var n = preguntas.filter(respondida).length;
      formulario.querySelector("[data-respondidas]").textContent = n;
      formulario.querySelector("[data-barra-progreso]").style.width = (n / total * 100) + "%";
      revisarEscala();
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
            var clase = valor === null ? null : clasificar(p.dataset.pregunta, valor);
            cifra.textContent = campo.value.trim() === "" ? "—" : campo.value.trim() + (p.querySelector(".unidad") ? " %" : "");
            if (clase) nivel.appendChild(etiquetaNivel(clase));
          } else {
            var marcada = p.querySelector("input[type=radio]:checked");
            if (marcada) nivel.appendChild(etiquetaNivel(marcada.value));
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

  /* ---------- Recorrido animado del árbol de decisión ----------
     Sin JavaScript la animación CSS corre al cargar la página. Con JavaScript espera a que el árbol sea visible
     y el botón «Ver de nuevo» la repite (se quita y se vuelve a poner la clase que la activa). */
  document.querySelectorAll("[data-arbol]").forEach(function (arbol) {
    var seccion = arbol.closest(".recorrido");
    var boton = seccion && seccion.querySelector("[data-repetir-arbol]");
    function reproducir() {
      arbol.classList.remove("arbol-animado", "arbol-espera");
      void arbol.offsetWidth;  // fuerza al navegador a reiniciar las animaciones
      arbol.classList.add("arbol-animado");
    }
    if (boton) {
      boton.hidden = false;
      boton.addEventListener("click", reproducir);
    }
    if ("IntersectionObserver" in window) {
      arbol.classList.remove("arbol-animado");
      arbol.classList.add("arbol-espera");  // oculto hasta que se vea, para que la animación empiece desde la raíz
      var observador = new IntersectionObserver(function (entradas) {
        if (entradas[0].isIntersecting) {
          reproducir();
          observador.disconnect();
        }
      }, { threshold: 0.25 });
      observador.observe(arbol);
    }
  });

  /* ---------- Imprimir resultado ---------- */
  document.querySelectorAll("[data-imprimir]").forEach(function (boton) {
    boton.addEventListener("click", function () { window.print(); });
  });
  window.addEventListener("beforeprint", function () {
    document.querySelectorAll("details").forEach(function (d) { d.open = true; });
  });
})();
