# Analizador sintáctico Java

Proyecto para Lenguajes y Autómatas II. Implementa en Python el descenso recursivo propuesto en la investigación de la actividad 1. La interfaz muestra cómo se reconocen las reglas, se consumen los tokens y se construyen los nodos de las expresiones. La traza se reproduce con un retardo configurable para observar cada paso.

## Ejecutar

Se requiere Python 3.10 o posterior con Tkinter. En Ubuntu o Debian, si falta Tkinter, instala el paquete `python3-tk`.

```bash
sudo apt install python3-tk
```

Desde la carpeta extraída del ZIP, ejecuta lo siguiente.

```bash
python3 interfaz.py
```

En Windows puedes usar `py interfaz.py` con una instalación de Python que incluya Tcl/Tk.

## Demostración

1. Abre el programa. La ventana carga `ejemplos/Demo.java`.
2. Pulsa **Analizar** y observa la traza junto al código. Ajusta el retardo o usa **Pausar** y **Paso**. **Reiniciar** limpia la traza y permite editar.
3. Al terminar, abre **Árbol sintáctico**. En `int total = 2 + 3 * 4;` el nodo `+` tiene como hijo derecho a `*`. Los paréntesis de la segunda asignación agrupan la resta antes de la división.
4. Usa **Abrir .java** para cargar `ejemplos/Error.java`. El diagnóstico señala el punto y coma de la línea 3, columna 25, donde se esperaba el operando derecho de `+`.
5. Carga `ejemplos/Control.java` para observar una llamada, una condición, un ciclo `while` y un `if` con `else`. También puedes pegar sentencias como `int x = 10 - 3 - 2;` y seleccionar **Fragmento**.

## Alcance

**Clase Java** analiza una o más clases con métodos, como `public static void main(String[] args)`. **Fragmento** analiza una secuencia de sentencias como la del caso de estudio. En ambos modos se comprueba el final de la entrada.

Se admiten declaraciones locales de una variable de tipo `int`, `double`, `boolean` o `String`, asignaciones simples, llamadas por nombre simple o calificado, bloques, `if`, `else`, `while` y `return`. Las expresiones aceptan identificadores ASCII, números decimales simples, cadenas, booleanos, `null`, paréntesis y operadores aritméticos, relacionales y lógicos. Los comentarios de una línea y de bloque se descartan conservando la ubicación de los tokens. El límite de entrada es de 30 000 caracteres.

Se cubre un subconjunto didáctico de Java. Clases con campos, constructores, `import`, `package`, `for`, genéricos, acceso a arreglos y operadores compuestos quedan fuera del alcance. El resultado describe la forma del código. La resolución de nombres, la comprobación de tipos y la ejecución corresponden a otras etapas del compilador. El análisis se detiene en el primer error léxico o sintáctico y muestra su ubicación.

## Gramática resumida

`*`, `+` y `?` indican repetición u opcionalidad cuando aparecen fuera de comillas. `Sentencia` puede incluir una declaración local. El cuerpo inmediato de `if` y `while` admite una sentencia sin declaración, o un bloque que contenga declaraciones.

```text
Programa    → Clase+ EOF | Sentencia* EOF (modo Fragmento)
Clase       → 'public'? 'class' ID '{' Método* '}'
Método      → Acceso? 'static'? (Tipo | 'void') ID '(' Parámetros? ')' Bloque
Acceso      → 'public' | 'private' | 'protected'
Parámetros  → Parámetro (',' Parámetro)*
Parámetro   → Tipo ('[' ']')? ID
Tipo        → 'int' | 'double' | 'boolean' | 'String'
Bloque      → '{' Sentencia* '}'
Sentencia   → Declaración | Simple
Declaración → Tipo ID ('=' Expr)? ';'
Simple      → Bloque | Nombre ('=' Expr | Argumentos) ';'
            | 'if' '(' Expr ')' Simple ('else' Simple)?
            | 'while' '(' Expr ')' Simple | 'return' Expr? ';' | ';'
Nombre      → ID ('.' ID)*
Argumentos  → '(' (Expr (',' Expr)*)? ')'
Expr        → Or
Or          → And ('||' And)*
And         → Igualdad ('&&' Igualdad)*
Igualdad    → Relación (('==' | '!=') Relación)*
Relación    → Suma (('<' | '>' | '<=' | '>=') Suma)*
Suma        → Término (('+' | '-') Término)*
Término     → Unaria (('*' | '/' | '%') Unaria)*
Unaria      → ('!' | '-' | '+') Unaria | Primaria
Primaria    → Literal | Nombre Argumentos? | '(' Expr ')'
Literal     → NUMERO | CADENA | 'true' | 'false' | 'null'
```

El `else` se asocia al `if` abierto más cercano. Los operadores binarios de igual precedencia se agrupan de izquierda a derecha. `analizador.py` contiene los tokens, las reglas y el árbol. `interfaz.py` maneja la carga de archivos, el editor y la reproducción de la traza con el temporizador de Tkinter.

## Entrega en GitLab

1. En la instancia de GitLab de la clase, crea un **proyecto vacío** llamado `analizador-sintactico-java`. Selecciona visibilidad **Privada** y deja sin marcar la inicialización con README, ya que el proyecto incluye el suyo. Copia la URL de clonación que te dé GitLab. [Documentación para crear un proyecto](https://docs.gitlab.com/user/project/)
2. En una terminal abierta en la carpeta extraída, ejecuta lo siguiente. Sustituye `URL_DE_CLONACION` por la URL que copiaste.

   ```bash
   git init -b main
   git add .
   git commit -m "Agregar analizador sintáctico Java en Python"
   git remote add origin URL_DE_CLONACION
   git push -u origin main
   ```

3. Abre **Manage → Members**. Si los equipos 7 y 4 están configurados como grupos y tienes permiso para compartir con ellos, usa **Invite a group**. Si deben recibir acceso individual, usa **Invite members** con los usuarios de GitLab que te confirme cada equipo. El rol **Reporter** permite consultar el código. [Documentación para invitar grupos](https://docs.gitlab.com/user/project/members/sharing_projects_groups/) · [Documentación para añadir miembros](https://docs.gitlab.com/user/project/members/)
4. Comprueba que los dos equipos figuren con acceso y entrega el enlace del proyecto en la actividad.
