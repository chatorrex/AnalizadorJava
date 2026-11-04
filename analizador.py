"""Análisis léxico y sintáctico de un subconjunto didáctico de Java."""
from dataclasses import dataclass
import re


TIPOS = {'int', 'double', 'boolean', 'String'}
RESERVADAS = set('''abstract assert boolean break byte case catch char class const
continue default do double else enum extends final finally float for goto if
implements import instanceof int interface long native new package private
protected public return short static strictfp super switch synchronized this
throw throws transient try void volatile while true false null _'''.split())
ACCESO = {'public', 'private', 'protected'}
MAX_CARACTERES = 30_000

PATRON = re.compile(r'''
    (?P<ESPACIO>[ \t\n\f]+) | (?P<LINEA>//[^\n]*) |
    (?P<BLOQUE>/\*[\s\S]*?\*/) | (?P<BLOQUE_ABIERTO>/\*) |
    (?P<CADENA>"(?:[^"\\\n]|\\[btnfr"'\\])*" ) | (?P<COMILLA>") |
    (?P<NUMERO>[0-9][a-zA-Z0-9_$]*(?:\.[a-zA-Z0-9_$]*)?) |
    (?P<ID>[a-zA-Z_$][a-zA-Z0-9_$]*) |
    (?P<SIMBOLO>==|!=|<=|>=|&&|\|\||\+\+|--|\+=|-=|\*=|/=|%=|[{}()\[\];,.=+*/%!<>-]) |
    (?P<INVALIDO>.)
''', re.VERBOSE)
DECIMAL = re.compile(r'(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z')


@dataclass(frozen=True)
class Token:
    tipo: str
    texto: str
    linea: int
    columna: int

    @property
    def descripcion(self):
        return 'fin de archivo' if self.tipo == 'EOF' else repr(self.texto)


@dataclass(frozen=True)
class Nodo:
    etiqueta: str
    hijos: tuple = ()


@dataclass(frozen=True)
class Paso:
    fase: str
    mensaje: str
    token: Token


class ErrorAnalisis(Exception):
    def __init__(self, fase, mensaje, token):
        super().__init__(mensaje)
        self.fase = fase
        self.token = token


@dataclass(frozen=True)
class Resultado:
    pasos: tuple
    arbol: Nodo | None
    error: ErrorAnalisis | None


def tokenizar(codigo):
    linea, columna = 1, 1
    tokens = []
    for coincidencia in PATRON.finditer(codigo):
        tipo, texto = coincidencia.lastgroup, coincidencia.group()
        token = Token(tipo, texto, linea, columna)
        if tipo == 'BLOQUE_ABIERTO':
            raise ErrorAnalisis('Léxico', 'Comentario de bloque sin cierre */.', token)
        if tipo == 'COMILLA':
            raise ErrorAnalisis('Léxico', 'Cadena sin cierre o escape fuera del subconjunto.', token)
        if tipo == 'INVALIDO':
            raise ErrorAnalisis('Léxico', f'Carácter fuera del subconjunto: {texto!r}.', token)
        if tipo == 'NUMERO' and not DECIMAL.fullmatch(texto):
            raise ErrorAnalisis('Léxico', f'Literal decimal fuera del subconjunto: {texto!r}.', token)
        if tipo in {'ID', 'SIMBOLO'} and (tipo == 'SIMBOLO' or texto in RESERVADAS or texto in TIPOS):
            token = Token(texto, texto, linea, columna)
        if tipo not in {'ESPACIO', 'LINEA', 'BLOQUE'}:
            tokens.append(token)
        saltos = texto.count('\n')
        if saltos:
            linea += saltos
            columna = len(texto.rsplit('\n', 1)[1]) + 1
        else:
            columna += len(texto)
    tokens.append(Token('EOF', '', linea, columna))
    return tokens


class Parser:
    def __init__(self, tokens, pasos):
        self.tokens = tokens
        self.indice = 0
        self.pasos = pasos

    @property
    def actual(self):
        return self.tokens[self.indice]

    def registrar(self, fase, mensaje, token=None):
        self.pasos.append(Paso(fase, mensaje, token or self.actual))

    def tomar(self):
        token = self.actual
        self.registrar('Consume', f'{token.tipo} · {token.descripcion}', token)
        if token.tipo != 'EOF':
            self.indice += 1
        return token

    def aceptar(self, tipo):
        if self.actual.tipo == tipo:
            return self.tomar()
        return None

    def exigir(self, tipo, esperado=None):
        if self.actual.tipo == tipo:
            return self.tomar()
        self.fallar(esperado or repr(tipo))

    def fallar(self, esperado):
        mensaje = f'Se esperaba {esperado}. Se encontró {self.actual.descripcion}.'
        raise ErrorAnalisis('Sintáctico', mensaje, self.actual)

    def programa(self, fragmento):
        self.registrar('Regla', 'Programa → sentencias EOF' if fragmento else 'Programa → clase+ EOF')
        nodos = []
        if fragmento:
            while self.actual.tipo != 'EOF':
                nodos.append(self.sentencia())
        else:
            nodos.append(self.clase())
            while self.actual.tipo != 'EOF':
                nodos.append(self.clase())
        self.exigir('EOF', 'el fin del archivo')
        return Nodo('Fragmento' if fragmento else 'Programa Java', tuple(nodos))

    def clase(self):
        self.registrar('Regla', 'Clase → public? class identificador { método* }')
        self.aceptar('public')
        self.exigir('class', 'la palabra class')
        nombre = self.exigir('ID', 'el nombre de la clase')
        self.exigir('{')
        metodos = []
        while self.actual.tipo not in {'}', 'EOF'}:
            metodos.append(self.metodo())
        self.exigir('}', 'la llave de cierre de la clase')
        return Nodo(f'Clase {nombre.texto}', tuple(metodos))

    def tipo(self, permite_void=False):
        if self.actual.tipo in TIPOS or (permite_void and self.actual.tipo == 'void'):
            return self.tomar().texto
        self.fallar('un tipo admitido (int, double, boolean, String' + (', void)' if permite_void else ')'))

    def parametro(self):
        tipo = self.tipo()
        if self.aceptar('['):
            self.exigir(']')
            tipo += '[]'
        nombre = self.exigir('ID', 'el nombre del parámetro').texto
        return Nodo(f'Parámetro {tipo} {nombre}')

    def metodo(self):
        self.registrar('Regla', 'Método → acceso? static? tipo nombre ( parámetros? ) bloque')
        encabezado = []
        if self.actual.tipo in ACCESO:
            encabezado.append(self.tomar().texto)
        if self.aceptar('static'):
            encabezado.append('static')
        encabezado.append(self.tipo(permite_void=True))
        encabezado.append(self.exigir('ID', 'el nombre del método').texto)
        self.exigir('(', "'(' después del nombre del método")
        parametros = []
        if self.actual.tipo != ')':
            parametros.append(self.parametro())
            while self.aceptar(','):
                parametros.append(self.parametro())
        self.exigir(')')
        cuerpo = self.bloque()
        return Nodo('Método ' + ' '.join(encabezado), (Nodo('Parámetros', tuple(parametros)), cuerpo))

    def bloque(self):
        self.registrar('Regla', 'Bloque → { sentencia* }')
        self.exigir('{')
        sentencias = []
        while self.actual.tipo not in {'}', 'EOF'}:
            sentencias.append(self.sentencia())
        self.exigir('}', 'la llave de cierre del bloque')
        return Nodo('Bloque', tuple(sentencias))

    def sentencia(self, permite_declaracion=True):
        tipo = self.actual.tipo
        self.registrar('Regla', f'Sentencia con anticipación {self.actual.descripcion}')
        if tipo in TIPOS:
            if not permite_declaracion:
                self.fallar('un bloque { ... } para la declaración')
            return self.declaracion()
        if tipo == '{':
            return self.bloque()
        if tipo in {'if', 'while'}:
            return self.control()
        if self.aceptar('return'):
            hijos = () if self.actual.tipo == ';' else (self.expresion(),)
            self.exigir(';')
            return Nodo('Retorno', hijos)
        if tipo == 'ID':
            nombre = self.nombre()
            if self.aceptar('='):
                nodo = Nodo('Asignación', (Nodo(nombre), self.expresion()))
            elif self.actual.tipo == '(':
                nodo = self.llamada(nombre)
            else:
                self.fallar("'=' para asignar o '(' para llamar a un método")
            self.exigir(';', "';' al final de la sentencia")
            return nodo
        if self.aceptar(';'):
            return Nodo('Sentencia vacía')
        self.fallar('una declaración, asignación, llamada, bloque, if, while o return')

    def declaracion(self):
        tipo = self.tipo()
        nombre = self.exigir('ID', 'el identificador de la variable').texto
        hijos = (self.expresion(),) if self.aceptar('=') else ()
        self.exigir(';', "';' al final de la declaración")
        return Nodo(f'Declaración {tipo} {nombre}', hijos)

    def control(self):
        tipo = self.tomar().tipo
        self.exigir('(')
        condicion = self.expresion()
        self.exigir(')', 'el paréntesis de cierre de la condición')
        cuerpo = self.sentencia(permite_declaracion=False)
        if tipo == 'while':
            return Nodo('Mientras', (Nodo('Condición', (condicion,)), cuerpo))
        hijos = [Nodo('Condición', (condicion,)), Nodo('Entonces', (cuerpo,))]
        if self.aceptar('else'):
            hijos.append(Nodo('Si no', (self.sentencia(permite_declaracion=False),)))
        return Nodo('Si', tuple(hijos))

    def nombre(self):
        partes = [self.exigir('ID', 'un identificador').texto]
        while self.aceptar('.'):
            partes.append(self.exigir('ID', 'un identificador después del punto').texto)
        return '.'.join(partes)

    def llamada(self, nombre):
        self.exigir('(')
        argumentos = []
        if self.actual.tipo != ')':
            argumentos.append(self.expresion())
            while self.aceptar(','):
                argumentos.append(self.expresion())
        self.exigir(')', 'el paréntesis de cierre de la llamada')
        return Nodo(f'Llamada {nombre}', tuple(argumentos))

    def expresion(self):
        self.registrar('Regla', 'Expresión → niveles de precedencia')
        return self.binaria(0)

    # Un nivel delega sus operandos a los operadores de mayor precedencia.
    NIVELES = ({'||'}, {'&&'}, {'==', '!='}, {'<', '>', '<=', '>='}, {'+', '-'}, {'*', '/', '%'})

    def binaria(self, nivel):
        if nivel == len(self.NIVELES):
            return self.unaria()
        izquierda = self.binaria(nivel + 1)
        while self.actual.tipo in self.NIVELES[nivel]:
            operador = self.tomar()
            derecha = self.binaria(nivel + 1)
            izquierda = Nodo(f'Operador {operador.texto}', (izquierda, derecha))
            self.registrar('Árbol', f'Construye el nodo binario {operador.texto}', operador)
        return izquierda

    def unaria(self):
        if self.actual.tipo in {'!', '-', '+'}:
            operador = self.tomar()
            return Nodo(f'Unario {operador.texto}', (self.unaria(),))
        return self.primaria()

    def primaria(self):
        if self.actual.tipo in {'NUMERO', 'CADENA', 'true', 'false', 'null'}:
            return Nodo(f'Literal {self.tomar().texto}')
        if self.actual.tipo == 'ID':
            nombre = self.nombre()
            return self.llamada(nombre) if self.actual.tipo == '(' else Nodo(f'Nombre {nombre}')
        if self.aceptar('('):
            nodo = self.expresion()
            self.exigir(')', 'el paréntesis de cierre de la expresión')
            return nodo
        self.fallar('un literal, identificador o expresión entre paréntesis')


def analizar(codigo, fragmento=False):
    """Devuelve la traza y el árbol, o el primer diagnóstico con su ubicación."""
    codigo = codigo.replace('\r\n', '\n').replace('\r', '\n')
    inicio = Token('INICIO', '', 1, 1)
    pasos = [Paso('Léxico', 'Lee el código y separa sus tokens.', inicio)]
    arbol, error = None, None
    try:
        if len(codigo) > MAX_CARACTERES:
            raise ErrorAnalisis('Límite', f'La entrada supera {MAX_CARACTERES} caracteres.', inicio)
        tokens = tokenizar(codigo)
        pasos.append(Paso('Léxico', f'{len(tokens) - 1} tokens de código y una marca EOF.', tokens[0]))
        parser = Parser(tokens, pasos)
        try:
            arbol = parser.programa(fragmento)
        except RecursionError:
            raise ErrorAnalisis('Límite', 'El código tiene demasiado anidamiento.', parser.actual) from None
        pasos.append(Paso('Resultado', 'Sintaxis válida para el subconjunto.', tokens[-1]))
    except ErrorAnalisis as diagnostico:
        error = diagnostico
        pasos.append(Paso(diagnostico.fase, str(diagnostico), diagnostico.token))
    return Resultado(tuple(pasos), arbol, error)
