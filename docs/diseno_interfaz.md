# Diseño de la interfaz

La interfaz se diseñó con la skill oficial **frontend-design** de Anthropic
(<https://github.com/anthropics/skills/tree/main/skills/frontend-design>), instalada localmente en `.claude/skills/frontend-design` (esa carpeta no se sube al repositorio).

## Tema, público y tarea principal

- **Tema:** orientación vocacional para aspirantes a la universidad.
- **Público:** aspirantes de 16 a 18 años. El público secundario son los ingenieros del conocimiento que mantienen la base.
- **Tarea principal:** responder 23 preguntas (4 notas por área, 18 actividades RIASEC y el estilo de trabajo) y entender cuáles son los cinco programas con mayor afinidad, y por qué.

## Tokens

| Token | Valor | Uso |
|---|---|---|
| Papel salvia | `#EEF2EC` | Fondo |
| Tinta azul noche | `#172A3A` | Texto y panel de progreso |
| Cobalto | `#2443B8` | Acciones, barras de afinidad, foco |
| Resaltador | `#FFD447` | Solo el programa con mayor afinidad |
| Línea | `#CBD5CC` | Bordes y divisiones |
| Ámbar | `#FFF1C9` / `#D99A00` | Resultado no concluyente |

- **Tipografía:** *Schibsted Grotesk* para títulos y *Atkinson Hyperlegible Next* para el texto. Atkinson se diseñó para la máxima legibilidad.
- **Elemento distintivo:** el nombre del programa n.º 1 se muestra en tipografía grande con un trazo de resaltador amarillo detrás, como cuando un estudiante subraya un libro. Es el único movimiento automático de la aplicación: el resaltador se "dibuja" y después crecen las barras de los programas 2 a 5. Con `prefers-reduced-motion` no hay animación.
- **Numeración:** solo donde hay una secuencia real, es decir, los tres pasos del cuestionario y el ranking del 1 al 5.

## Decisiones de experiencia de uso

- Las notas por área (P01–P04) tienen un deslizador y un campo de texto sincronizados, y al lado se muestra la clasificación (Alto, Medio o Bajo). Las 18 actividades RIASEC (P05–P22) y el estilo de trabajo (P23) se responden en una escala de 1 a 5; el estilo se clasifica como Independiente, Indistinto o Equipo, y los intereses por la posición de su promedio frente a las demás categorías (Primera, Segunda, Tercera o Posterior). Los rangos vienen de la base de conocimiento.
- El panel lateral muestra el progreso ("7 de 23 respondidas") y deja el botón principal siempre a la vista.
- La validación ocurre en el servidor y marca cada respuesta con su error. El foco va a la primera respuesta con error.
- El resultado explica cada programa con los datos del perfil y las reglas RG que lo respaldan.
- Todo funciona sin JavaScript (mejora progresiva), con foco visible y etiquetas accesibles. Es adaptable hasta 360 px y tiene una hoja de estilos para imprimir o guardar en PDF.
