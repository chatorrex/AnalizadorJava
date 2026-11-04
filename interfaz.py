"""Ventana de escritorio para seguir la traza del analizador."""
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, font, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from analizador import MAX_CARACTERES, analizar


CARPETA = Path(__file__).resolve().parent
TINTA = '#16273b'
FONDO = '#f0f4f8'
AZUL = '#2056a8'


class Ventana:
    def __init__(self, raiz):
        self.raiz = raiz
        self.resultado = None
        self.posicion = 0
        self.temporizador = None
        self.modo = tk.StringVar(value='Clase Java')
        self.retardo = tk.DoubleVar(value=280)
        self.estado = tk.StringVar(value='Abre un archivo .java o pega el código en el editor.')
        self.archivo = tk.StringVar(value='Sin archivo')
        self.crear_interfaz()
        self.cargar_ejemplo()

    def crear_interfaz(self):
        self.raiz.title('Analizador sintáctico Java')
        self.raiz.geometry('1130x720')
        self.raiz.minsize(850, 550)
        self.raiz.configure(background=FONDO)
        estilo = ttk.Style(self.raiz)
        estilo.theme_use('clam')
        estilo.configure('TFrame', background=FONDO)
        estilo.configure('TLabel', background=FONDO, foreground=TINTA)
        estilo.configure('TButton', padding=(10, 6))
        estilo.configure('Accion.TButton', background=AZUL, foreground='white')
        estilo.map('Accion.TButton', background=[('active', '#16458b'), ('disabled', '#8094ad')])
        estilo.configure('Treeview', rowheight=25)

        encabezado = tk.Frame(self.raiz, bg=TINTA, padx=20, pady=13)
        encabezado.pack(fill='x')
        tk.Label(encabezado, text='Analizador sintáctico Java', bg=TINTA, fg='white',
                 font=('TkDefaultFont', 18, 'bold')).pack(anchor='w')
        tk.Label(encabezado, text='Lenguajes y Autómatas II   /   Descenso recursivo en Python',
                 bg=TINTA, fg='#c3d6ee').pack(anchor='w', pady=(4, 0))

        barra = ttk.Frame(self.raiz, padding=(14, 9))
        barra.pack(fill='x')
        self.abrir = ttk.Button(barra, text='Abrir .java', command=self.abrir_archivo)
        self.abrir.pack(side='left', padx=(0, 6))
        self.ejemplo = ttk.Button(barra, text='Cargar ejemplo', command=self.cargar_ejemplo)
        self.ejemplo.pack(side='left', padx=(0, 12))
        self.selector = ttk.Combobox(barra, textvariable=self.modo, state='readonly',
                                    values=('Clase Java', 'Fragmento'), width=13)
        self.selector.pack(side='left', padx=(0, 9))
        self.selector.bind('<<ComboboxSelected>>', self.limpiar_resultados)
        self.iniciar = ttk.Button(barra, text='Analizar', command=self.iniciar_analisis,
                                 style='Accion.TButton')
        self.iniciar.pack(side='left', padx=(0, 6))
        self.pausa = ttk.Button(barra, text='Pausar', command=self.alternar_pausa, state='disabled')
        self.pausa.pack(side='left', padx=(0, 6))
        self.paso = ttk.Button(barra, text='Paso', command=self.avanzar_manual)
        self.paso.pack(side='left', padx=(0, 6))
        self.reiniciar = ttk.Button(barra, text='Reiniciar', command=self.limpiar_resultados)
        self.reiniciar.pack(side='left')

        panel = ttk.Panedwindow(self.raiz, orient='horizontal')
        panel.pack(fill='both', expand=True, padx=14, pady=(0, 6))
        izquierda = ttk.Frame(panel, padding=(0, 2, 6, 0))
        derecha = ttk.Frame(panel, padding=(6, 2, 0, 0))
        panel.add(izquierda, weight=1)
        panel.add(derecha, weight=1)
        ttk.Label(izquierda, text='Código fuente', font=('TkDefaultFont', 11, 'bold')).pack(anchor='w')
        ttk.Label(izquierda, textvariable=self.archivo).pack(anchor='w', pady=(2, 8))
        monoespaciada = font.nametofont('TkFixedFont').copy()
        monoespaciada.configure(size=11)
        self.editor = ScrolledText(izquierda, font=monoespaciada, wrap='none', undo=True,
                                   width=38, height=18, padx=10, pady=8, fg=TINTA,
                                   relief='flat', highlightthickness=1, highlightbackground='#ccd8e6')
        self.editor.pack(fill='both', expand=True)
        self.editor.tag_configure('actual', background='#d7e8ff')
        self.editor.tag_configure('error', background='#ffd8d8', foreground='#7a1720')
        self.editor.bind('<<Modified>>', self.al_editar)
        desplazador = ttk.Scrollbar(izquierda, orient='horizontal', command=self.editor.xview)
        desplazador.pack(fill='x')
        self.editor.configure(xscrollcommand=desplazador.set)

        controles = ttk.Frame(derecha)
        controles.pack(fill='x', pady=(0, 7))
        ttk.Label(controles, text='Retardo por paso').pack(side='left')
        self.medida = ttk.Label(controles, text='280 ms', width=8)
        self.medida.pack(side='right')
        ttk.Scale(controles, from_=50, to=1200, variable=self.retardo, length=150,
                  command=lambda valor: self.medida.configure(text=f'{int(float(valor))} ms')).pack(side='right')
        self.tabs = ttk.Notebook(derecha)
        self.tabs.pack(fill='both', expand=True)
        traza_panel = ttk.Frame(self.tabs)
        arbol_panel = ttk.Frame(self.tabs)
        self.tabs.add(traza_panel, text='Traza del análisis')
        self.tabs.add(arbol_panel, text='Árbol sintáctico')
        self.traza = ScrolledText(traza_panel, width=43, height=18, wrap='word', state='disabled',
                                 padx=9, pady=8, relief='flat', font=monoespaciada, fg=TINTA)
        self.traza.pack(fill='both', expand=True)
        self.traza.tag_configure('Regla', foreground=AZUL)
        self.traza.tag_configure('Árbol', foreground='#32614c')
        self.traza.tag_configure('error', foreground='#a1222c')
        self.arbol = ttk.Treeview(arbol_panel, show='tree')
        vertical = ttk.Scrollbar(arbol_panel, orient='vertical', command=self.arbol.yview)
        horizontal = ttk.Scrollbar(arbol_panel, orient='horizontal', command=self.arbol.xview)
        self.arbol.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        arbol_panel.columnconfigure(0, weight=1)
        arbol_panel.rowconfigure(0, weight=1)
        self.arbol.grid(row=0, column=0, sticky='nsew')
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal.grid(row=1, column=0, sticky='ew')

        pie = ttk.Frame(self.raiz, padding=(14, 4, 14, 12))
        pie.pack(fill='x')
        self.progreso = ttk.Progressbar(pie, mode='determinate')
        self.progreso.pack(fill='x', pady=(0, 6))
        self.etiqueta_estado = ttk.Label(pie, textvariable=self.estado, wraplength=810)
        self.etiqueta_estado.pack(anchor='w')
        self.raiz.bind('<Control-o>', lambda evento: self.abrir_archivo())

    def poner_codigo(self, codigo, nombre, modo):
        self.limpiar_resultados()
        self.editor.delete('1.0', 'end')
        self.editor.insert('1.0', codigo)
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self.archivo.set(nombre)
        self.modo.set(modo)

    def cargar_ejemplo(self):
        self.poner_codigo((CARPETA / 'ejemplos' / 'Demo.java').read_text(encoding='utf-8'),
                          'Demo.java', 'Clase Java')

    def abrir_archivo(self):
        if self.resultado is not None and self.posicion < len(self.resultado.pasos):
            return
        ruta = filedialog.askopenfilename(title='Abrir código Java',
                                          filetypes=[('Archivos Java', '*.java'), ('Todos los archivos', '*')])
        if not ruta:
            return
        try:
            with Path(ruta).open(encoding='utf-8-sig') as archivo:
                codigo = archivo.read(MAX_CARACTERES + 1)
            if len(codigo) > MAX_CARACTERES:
                raise ValueError(f'El archivo supera {MAX_CARACTERES} caracteres.')
        except (OSError, UnicodeError, ValueError) as error:
            messagebox.showerror('No se pudo abrir el archivo', str(error))
            return
        self.poner_codigo(codigo, Path(ruta).name, 'Clase Java')

    def al_editar(self, evento):
        if self.editor.edit_modified():
            self.editor.edit_modified(False)
            if self.resultado is not None:
                self.limpiar_resultados()

    def cancelar_temporizador(self):
        if self.temporizador is not None:
            self.raiz.after_cancel(self.temporizador)
            self.temporizador = None

    def bloquear_entrada(self, bloqueado):
        self.editor.configure(state='disabled' if bloqueado else 'normal')
        self.selector.configure(state='disabled' if bloqueado else 'readonly')
        for boton in (self.abrir, self.ejemplo, self.iniciar):
            boton.configure(state='disabled' if bloqueado else 'normal')

    def limpiar_resultados(self, evento=None):
        self.cancelar_temporizador()
        self.resultado = None
        self.posicion = 0
        self.bloquear_entrada(False)
        self.pausa.configure(text='Pausar', state='disabled')
        self.paso.configure(state='normal')
        self.traza.configure(state='normal')
        self.traza.delete('1.0', 'end')
        self.traza.configure(state='disabled')
        self.arbol.delete(*self.arbol.get_children())
        self.editor.tag_remove('actual', '1.0', 'end')
        self.editor.tag_remove('error', '1.0', 'end')
        self.progreso.configure(value=0, maximum=1)
        self.etiqueta_estado.configure(foreground=TINTA)
        self.estado.set('Listo para analizar. Usa Analizar para reproducir o Paso para avanzar manualmente.')

    def preparar_traza(self):
        self.limpiar_resultados()
        self.resultado = analizar(self.editor.get('1.0', 'end-1c'), self.modo.get() == 'Fragmento')
        self.progreso.configure(maximum=len(self.resultado.pasos))
        self.tabs.select(0)
        self.bloquear_entrada(True)
        self.pausa.configure(text='Continuar', state='normal')

    def iniciar_analisis(self):
        self.preparar_traza()
        self.reproducir()

    def reproducir(self):
        self.temporizador = None
        self.mostrar_paso()
        if self.posicion < len(self.resultado.pasos):
            self.pausa.configure(text='Pausar')
            self.temporizador = self.raiz.after(int(self.retardo.get()), self.reproducir)

    def alternar_pausa(self):
        if self.temporizador is None:
            self.reproducir()
        else:
            self.cancelar_temporizador()
            self.pausa.configure(text='Continuar')
            self.estado.set(f'Traza en pausa. Paso {self.posicion} de {len(self.resultado.pasos)}.')

    def avanzar_manual(self):
        if self.resultado is None:
            self.preparar_traza()
        self.cancelar_temporizador()
        self.pausa.configure(text='Continuar')
        self.mostrar_paso()

    def mostrar_paso(self):
        paso = self.resultado.pasos[self.posicion]
        self.posicion += 1
        token = paso.token
        ubicacion = f'L{token.linea}:C{token.columna}'
        total = len(self.resultado.pasos)
        ultimo = self.posicion == total
        fallo = ultimo and self.resultado.error is not None
        etiqueta = 'error' if fallo else 'actual'
        for color in ('actual', 'error'):
            self.editor.tag_remove(color, '1.0', 'end')
        inicio = f'{token.linea}.{token.columna - 1}'
        fin = f'{inicio}+{max(1, len(token.texto))}c'
        self.editor.tag_add(etiqueta, inicio, fin)
        self.editor.see(inicio)
        self.traza.configure(state='normal')
        self.traza.insert('end', f'{self.posicion:03}  {ubicacion}  {paso.fase}  {paso.mensaje}\n',
                          'error' if fallo else paso.fase)
        self.traza.configure(state='disabled')
        self.traza.see('end')
        self.progreso.configure(value=self.posicion)
        self.estado.set(f'Paso {self.posicion}/{total} · {ubicacion} · {paso.mensaje}')
        if ultimo:
            self.finalizar_traza()

    def finalizar_traza(self):
        self.bloquear_entrada(False)
        self.pausa.configure(text='Pausar', state='disabled')
        self.paso.configure(state='disabled')
        error = self.resultado.error
        if error:
            t = error.token
            self.etiqueta_estado.configure(foreground='#a1222c')
            self.estado.set(f'{error.fase} · línea {t.linea}, columna {t.columna} · {error}')
        else:
            self.etiqueta_estado.configure(foreground='#23634b')
            self.estado.set('Sintaxis válida para el subconjunto. El árbol está disponible en la segunda pestaña.')
            self.mostrar_arbol(self.resultado.arbol)

    def mostrar_arbol(self, arbol):
        pendientes = [('', arbol, 0)]
        ancho = 430
        while pendientes:
            padre, nodo, nivel = pendientes.pop()
            identificador = self.arbol.insert(padre, 'end', text=nodo.etiqueta, open=nivel < 7)
            ancho = max(ancho, nivel * 18 + len(nodo.etiqueta) * 8)
            pendientes.extend((identificador, hijo, nivel + 1) for hijo in reversed(nodo.hijos))
        self.arbol.column('#0', minwidth=160, width=ancho, stretch=True)


if __name__ == '__main__':
    raiz = tk.Tk()
    Ventana(raiz)
    raiz.mainloop()
