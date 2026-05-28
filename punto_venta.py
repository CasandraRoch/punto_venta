import customtkinter as ctk
from CTkTable import *
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tkinter import filedialog, messagebox
from datetime import datetime
import os
from PIL import Image

# Librerías para el PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# --- CONFIGURACIÓN VISUAL ---
ctk.set_appearance_mode("light") 
ctk.set_default_color_theme("green")

class AppConsultorio(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Consultorio Naturista - Punto de Venta")
        self.icon_path = "logo.ico"
        try: self.iconbitmap(self.icon_path) 
        except: pass 
            
        self.after(0, lambda: self.state('zoomed')) 
        
        # Variables de Estilo y Control
        self.color_fondo = "#F2F2F7"
        self.color_verde_titulo = "#25751B" 
        self.color_verde_tabla_head = "#76BA1B" 
        
        # Datos en Memoria (Cache para velocidad)
        self.datos_locales = {"Pastillas": [], "Varios": []}
        self.filtro_actual = None
        self.filtro_busqueda = ""
        self.carrito_items = {} 
        self.ultima_accion = None
        self.nombre_original_seleccionado = None
        
        self.libro = self.conectar_google()
        self.selector_ho_set = "Pastillas"
        try: 
            self.hoja = self.libro.worksheet("Pastillas") if self.libro else None
            self.precargar_datos() 
        except: self.hoja = None

        self.configure(fg_color=self.color_fondo)

        # GRID LAYOUT PRINCIPAL
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR (BARRA LATERAL) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="white")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        # Texto MENÚ
        ctk.CTkLabel(self.sidebar_frame, text="MENÚ", font=("SF Pro Display", 22, "bold"), text_color=self.color_verde_titulo).pack(pady=(30, 5))
        
        # ICONO DEBAJO DE MENÚ
        try:
            # Cargamos la imagen con PIL y la adaptamos a CustomTkinter
            img_pil = Image.open(self.icon_path)
            self.logo_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(90, 90))
            self.lbl_logo = ctk.CTkLabel(self.sidebar_frame, image=self.logo_img, text="")
            self.lbl_logo.pack(pady=(0, 20))
        except Exception as e:
            print(f"No se pudo cargar el logo en el menú: {e}")

        self.btn_nav_inv = ctk.CTkButton(self.sidebar_frame, text="📦 INVENTARIO", height=45, fg_color="#444444", command=self.mostrar_inventario)
        self.btn_nav_inv.pack(padx=20, pady=10)

        self.btn_nav_ventas = ctk.CTkButton(self.sidebar_frame, text="🛒 VENTAS", height=45, fg_color="transparent", text_color="black", hover_color="#E0E0E0", command=self.mostrar_ventas)
        self.btn_nav_ventas.pack(padx=20, pady=10)

        # --- CONTENEDORES ---
        self.frame_inventario = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_ventas = ctk.CTkFrame(self, fg_color="transparent")

        self.setup_inventario_ui()
        self.setup_ventas_ui()
        self.mostrar_inventario()

    def precargar_datos(self):
        try:
            self.datos_locales["Pastillas"] = self.libro.worksheet("Pastillas").get_all_values()[1:]
            self.datos_locales["Varios"] = self.libro.worksheet("Varios").get_all_values()[1:]
        except: pass

    # --- NAVEGACIÓN ---
    def mostrar_inventario(self):
        self.precargar_datos()
        self.selector_ho_set = "Pastillas"
        self.filtro_actual = None
        self.filtro_busqueda = ""
        self.hoja = self.libro.worksheet("Pastillas")
        if hasattr(self, 'selector_hoja_i'): self.selector_hoja_i.set("Pastillas")
        if hasattr(self, 'search_inv'): self.search_inv.delete(0, 'end')
        self.frame_ventas.grid_forget()
        self.frame_inventario.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.btn_nav_inv.configure(fg_color="#444444", text_color="white")
        self.btn_nav_ventas.configure(fg_color="transparent", text_color="black")
        self.actualizar_tabla(self.scroll_inv)

    def mostrar_ventas(self):
        self.precargar_datos()
        self.selector_ho_set = "Pastillas"
        self.filtro_actual = None
        self.filtro_busqueda = ""
        self.hoja = self.libro.worksheet("Pastillas")
        if hasattr(self, 'selector_hoja_v'): self.selector_hoja_v.set("Pastillas")
        if hasattr(self, 'search_ventas'): self.search_ventas.delete(0, 'end')
        self.frame_inventario.grid_forget()
        self.frame_ventas.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.btn_nav_ventas.configure(fg_color="#444444", text_color="white")
        self.btn_nav_inv.configure(fg_color="transparent", text_color="black")
        self.actualizar_tabla(self.scroll_ventas)

    # --- UI INVENTARIO ---
    def setup_inventario_ui(self):
        self.frame_inventario.grid_columnconfigure(1, weight=1)
        self.frame_inventario.grid_rowconfigure(0, weight=1)
        inv_left = ctk.CTkFrame(self.frame_inventario, fg_color="transparent", width=400)
        inv_left.grid(row=0, column=0, sticky="nsew", padx=(0, 10)); inv_left.grid_propagate(False)
        self.tabview = ctk.CTkTabview(inv_left, corner_radius=20, fg_color="white", segmented_button_selected_color="#444444", height=450)
        self.tabview.pack(fill="x", pady=(0, 10))
        self.tab_nuevo = self.tabview.add("🆕 NUEVO"); self.tab_suma = self.tabview.add("➕ AGREGAR"); self.tab_gestion = self.tabview.add("🛠️ GESTIÓN")
        self.setup_inventario_tabs()
        self.ctrl_inv = ctk.CTkFrame(inv_left, fg_color="white", corner_radius=20, height=80)
        self.ctrl_inv.pack(fill="x")
        self.lbl_notif_inv = ctk.CTkLabel(self.ctrl_inv, text="", font=("SF Pro", 13, "bold"))
        self.lbl_notif_inv.place(relx=0.5, rely=0.3, anchor="center")
        self.btn_undo = ctk.CTkButton(self.ctrl_inv, text="⟲ DESHACER ÚLTIMO", fg_color="#5856d6", state="disabled", command=self.deshacer_accion)
        self.btn_undo.place(relx=0.5, rely=0.7, anchor="center")
        inv_right = ctk.CTkFrame(self.frame_inventario, fg_color="transparent")
        inv_right.grid(row=0, column=1, sticky="nsew")
        self.setup_right_common(inv_right, "inv")

    def setup_inventario_tabs(self):
        # Campos Nuevo
        ctk.CTkLabel(self.tab_nuevo, text="Producto:", font=("SF Pro", 12, "bold")).pack(pady=(15,0))
        self.entry_p_nuevo = ctk.CTkEntry(self.tab_nuevo, width=300, height=35); self.entry_p_nuevo.pack(pady=5)
        ctk.CTkLabel(self.tab_nuevo, text="Cantidad Inicial:", font=("SF Pro", 12, "bold")).pack()
        self.entry_c_nuevo = ctk.CTkEntry(self.tab_nuevo, width=300, height=35); self.entry_c_nuevo.pack(pady=5)
        ctk.CTkButton(self.tab_nuevo, text="REGISTRAR NUEVO", fg_color="#1c41b9", height=40, command=self.registrar_nuevo).pack(pady=20)
        # Campos Suma
        ctk.CTkLabel(self.tab_suma, text="Producto Seleccionado:", font=("SF Pro", 12, "bold")).pack(pady=(15,0))
        self.entry_p_suma = ctk.CTkEntry(self.tab_suma, width=300, height=35); self.entry_p_suma.pack(pady=5)
        ctk.CTkLabel(self.tab_suma, text="Cantidad a Añadir:", font=("SF Pro", 12, "bold")).pack()
        self.entry_c_suma = ctk.CTkEntry(self.tab_suma, width=300, height=35); self.entry_c_suma.pack(pady=5)
        ctk.CTkButton(self.tab_suma, text="SUMAR STOCK (+)", fg_color="#63b91c", height=40, command=self.ejecutar_suma).pack(pady=20)
        # Campos Gestión
        ctk.CTkLabel(self.tab_gestion, text="Nombre del Producto:", font=("SF Pro", 12, "bold")).pack(pady=(15,0))
        self.entry_p_gest = ctk.CTkEntry(self.tab_gestion, width=300, height=35); self.entry_p_gest.pack(pady=5)
        ctk.CTkLabel(self.tab_gestion, text="Stock Actual (Editar):", font=("SF Pro", 12, "bold")).pack()
        self.entry_c_gest = ctk.CTkEntry(self.tab_gestion, width=300, height=35); self.entry_c_gest.pack(pady=5)
        f_btns = ctk.CTkFrame(self.tab_gestion, fg_color="transparent"); f_btns.pack(pady=20)
        ctk.CTkButton(f_btns, text="GUARDAR", fg_color="#d58e13", width=140, height=40, command=self.corregir_valor).pack(side="left", padx=5)
        ctk.CTkButton(f_btns, text="ELIMINAR", fg_color="#ff3b30", width=140, height=40, command=self.eliminar_producto).pack(side="left", padx=5)

    # --- UI VENTAS ---
    def setup_ventas_ui(self):
        self.frame_ventas.grid_columnconfigure(1, weight=1)
        self.frame_ventas.grid_rowconfigure(0, weight=1)
        v_left = ctk.CTkFrame(self.frame_ventas, fg_color="white", width=420, corner_radius=20)
        v_left.grid(row=0, column=0, sticky="nsew", padx=(0, 10)); v_left.grid_propagate(False)
        ctk.CTkLabel(v_left, text="🛒 CARRITO DE VENTAS", font=("SF Pro", 18, "bold"), text_color=self.color_verde_titulo).pack(pady=15)
        self.lbl_notif_ventas = ctk.CTkLabel(v_left, text="", font=("SF Pro", 13, "bold")); self.lbl_notif_ventas.pack(pady=2)
        ctk.CTkLabel(v_left, text="Nombre del paciente:", font=("SF Pro", 12, "bold")).pack(anchor="w", padx=25)
        self.ent_paciente = ctk.CTkEntry(v_left, width=370, height=35, placeholder_text="Ingrese nombre..."); self.ent_paciente.pack(pady=5)
        self.scroll_carrito = ctk.CTkScrollableFrame(v_left, fg_color="#F9F9F9", height=380); self.scroll_carrito.pack(fill="both", expand=True, padx=15, pady=10)
        self.btn_finalizar = ctk.CTkButton(v_left, text="✅ FINALIZAR VENTA", fg_color="#2FB932", height=45, command=self.finalizar_venta)
        self.btn_finalizar.pack(fill="x", padx=30, pady=5)
        ctk.CTkButton(v_left, text="🗑️ VACIAR TODO", fg_color="#FF3B30", height=30, command=self.vaciar_carrito).pack(fill="x", padx=30, pady=(0, 15))
        v_right = ctk.CTkFrame(self.frame_ventas, fg_color="transparent")
        v_right.grid(row=0, column=1, sticky="nsew")
        self.setup_right_common(v_right, "ventas")

    def setup_right_common(self, parent, tipo):
        top_bar = ctk.CTkFrame(parent, fg_color="white", corner_radius=15, height=75)
        top_bar.pack(fill="x", pady=(0, 10)); top_bar.pack_propagate(False)
        ctk.CTkLabel(top_bar, text="CATEGORÍA:", font=("SF Pro", 11, "bold"), text_color="gray").pack(side="left", padx=(15, 5))
        cb = ctk.CTkComboBox(top_bar, values=["Pastillas", "Varios"], command=self.cambiar_categoria, width=120); cb.set("Pastillas"); cb.pack(side="left", padx=5)
        
        search_container = ctk.CTkFrame(top_bar, fg_color="transparent"); search_container.pack(side="left", padx=20)
        ctk.CTkLabel(search_container, text="BUSCADOR:", font=("SF Pro", 10, "bold"), text_color=self.color_verde_titulo).pack(anchor="w")
        
        if tipo == "ventas": 
            self.selector_hoja_v = cb
            self.search_ventas = ctk.CTkEntry(search_container, placeholder_text="Buscar en todo...", width=220); self.search_ventas.pack()
            self.search_ventas.bind("<KeyRelease>", lambda e: self.filtrar_teclado(self.search_ventas.get(), self.scroll_ventas))
        else: 
            self.selector_hoja_i = cb
            self.search_inv = ctk.CTkEntry(search_container, placeholder_text="Buscar en todo...", width=220); self.search_inv.pack()
            self.search_inv.bind("<KeyRelease>", lambda e: self.filtrar_teclado(self.search_inv.get(), self.scroll_inv))
            pdf_container = ctk.CTkFrame(top_bar, fg_color="transparent"); pdf_container.pack(side="right", padx=10)
            ctk.CTkLabel(pdf_container, text="GENERAR PDF:", font=("SF Pro", 10, "bold"), text_color=self.color_verde_titulo).pack(anchor="w")
            btn_f = ctk.CTkFrame(pdf_container, fg_color="transparent"); btn_f.pack()
            ctk.CTkButton(btn_f, text="POCO STOCK", fg_color="#ff9f0a", width=95, height=30, font=("SF Pro", 10, "bold"), command=lambda: self.generar_pdf_inventario(True)).pack(side="left", padx=2)
            ctk.CTkButton(btn_f, text="COMPLETO", fg_color="#34c759", width=95, height=30, font=("SF Pro", 10, "bold"), command=lambda: self.generar_pdf_inventario(False)).pack(side="left", padx=2)

        az = ctk.CTkFrame(parent, fg_color="white", corner_radius=10, height=45); az.pack(fill="x", pady=(0, 10))
        for l in ["#"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            ctk.CTkButton(az, text=l, width=28, fg_color="transparent", text_color="black", font=("SF Pro", 10, "bold"), command=lambda letra=l: self.filtrar_az(letra)).pack(side="left", expand=True)

        if tipo == "inv": self.scroll_inv = ctk.CTkScrollableFrame(parent, fg_color="white"); self.scroll_inv.pack(fill="both", expand=True)
        else: self.scroll_ventas = ctk.CTkScrollableFrame(parent, fg_color="white"); self.scroll_ventas.pack(fill="both", expand=True)

    # --- LÓGICA BUSCADOR ---
    def filtrar_teclado(self, texto, target_scroll):
        self.filtro_busqueda = texto.upper()
        self.actualizar_tabla(target_scroll)

    def actualizar_tabla(self, target):
        for w in target.winfo_children(): w.destroy()
        try:
            vis = []; alertas = []; cont = 1
            if self.filtro_busqueda:
                vis = [["#", "PRODUCTO", "STOCK", "CATEGORÍA"]]
                for cat in ["Pastillas", "Varios"]:
                    for f in self.datos_locales[cat]:
                        if self.filtro_busqueda in f[0].upper():
                            vis.append([str(cont), f[0].upper(), f[1], cat])
                            if int(f[1]) <= 4: alertas.append(cont)
                            cont += 1
            else:
                vis = [["#", "PRODUCTO", "STOCK"]]
                for f in self.datos_locales[self.selector_ho_set]:
                    if self.filtro_actual and not f[0].upper().startswith(self.filtro_actual): continue
                    vis.append([str(cont), f[0].upper(), f[1]])
                    if int(f[1]) <= 4: alertas.append(cont)
                    cont += 1
            self.active_table = CTkTable(master=target, values=vis, header_color=self.color_verde_tabla_head, command=self.al_hacer_clic)
            self.active_table.pack(expand=True, fill="both", padx=10, pady=10)
            for r in alertas: self.active_table.edit_row(r, fg_color="#FFE5E5", text_color="#D32F2F")
        except: pass

    def al_hacer_clic(self, v):
        if v['row'] == 0: return
        fila = self.active_table.get_row(v['row'])
        if len(fila) > 3: 
            nueva_cat = fila[3]
            if nueva_cat != self.selector_ho_set:
                self.cambiar_categoria(nueva_cat)
                if hasattr(self, 'selector_hoja_v'): self.selector_hoja_v.set(nueva_cat)
                if hasattr(self, 'selector_hoja_i'): self.selector_hoja_i.set(nueva_cat)
        if self.frame_ventas.winfo_viewable():
            self.agregar_al_carrito(fila[1], fila[2])
        else:
            self.nombre_original_seleccionado = fila[1].lower()
            for e, val in [(self.entry_p_suma, fila[1]), (self.entry_p_gest, fila[1]), (self.entry_c_gest, fila[2])]:
                e.delete(0, "end"); e.insert(0, val)

    def filtrar_az(self, l):
        self.filtro_actual = None if l == "#" else l
        self.filtro_busqueda = ""
        self.actualizar_tabla(self.scroll_inv if self.frame_inventario.winfo_viewable() else self.scroll_ventas)

    def cambiar_categoria(self, n):
        self.hoja = self.libro.worksheet(n); self.selector_ho_set = n
        self.actualizar_tabla(self.scroll_inv if self.frame_inventario.winfo_viewable() else self.scroll_ventas)

    # --- VENTAS ---
    def agregar_al_carrito(self, nombre, stock):
        nombre = nombre.upper()
        if int(stock) <= 0: self.mostrar_notif_ventas("⚠ Inventario insuficiente", "#FF3B30"); return
        if nombre in self.carrito_items: return
        item_frame = ctk.CTkFrame(self.scroll_carrito, fg_color="white", corner_radius=10); item_frame.pack(fill="x", pady=2, padx=5)
        lbl_nombre = ctk.CTkLabel(item_frame, text=nombre, font=("SF Pro", 10, "bold"), width=120, anchor="w", justify="left", wraplength=110); lbl_nombre.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(item_frame, text="-", width=25, height=25, fg_color="#E0E0E0", text_color="black", command=lambda n=nombre: self.cambiar_cant(n, -1)).pack(side="left", padx=2)
        ent_cant = ctk.CTkEntry(item_frame, width=40, height=25, justify="center"); ent_cant.insert(0, "1"); ent_cant.pack(side="left", padx=2)
        ctk.CTkButton(item_frame, text="+", width=25, height=25, fg_color="#E0E0E0", text_color="black", command=lambda n=nombre: self.cambiar_cant(n, 1)).pack(side="left", padx=2)
        lbl_err = ctk.CTkLabel(item_frame, text="", font=("SF Pro", 9, "bold"), text_color="#FF3B30"); lbl_err.pack(side="left", padx=5)
        ctk.CTkButton(item_frame, text="🗑️", width=30, height=25, fg_color="#FFE5E5", text_color="#D32F2F", command=lambda n=nombre: self.quitar_item(n)).pack(side="right", padx=5)
        self.carrito_items[nombre] = {"cant_ent": ent_cant, "stock_max": int(stock), "frame": item_frame, "lbl_error": lbl_err}

    def cambiar_cant(self, nombre, delta):
        item = self.carrito_items[nombre]
        try:
            actual = int(item["cant_ent"].get()); nuevo = actual + delta
            if 1 <= nuevo <= item["stock_max"]:
                item["cant_ent"].delete(0, "end"); item["cant_ent"].insert(0, str(nuevo)); item["lbl_error"].configure(text="")
            elif nuevo > item["stock_max"]:
                item["lbl_error"].configure(text="¡SIN STOCK!"); self.after(2000, lambda: item["lbl_error"].configure(text=""))
        except: item["cant_ent"].delete(0, "end"); item["cant_ent"].insert(0, "1")

    def finalizar_venta(self):
        pac = self.ent_paciente.get().strip().upper()
        if not pac: self.mostrar_notif_ventas("⚠ Ingrese nombre de paciente", "#FF9F0A"); self.ent_paciente.configure(border_color="#FF9F0A"); return
        if not self.carrito_items: self.mostrar_notif_ventas("⚠ Carrito vacío", "#FF3B30"); return
        ruta = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Ticket_{pac}_{datetime.now().strftime('%d%m%y_%H%M')}.pdf")
        if not ruta: return
        try:
            doc = SimpleDocTemplate(ruta, pagesize=letter); styles = getSampleStyleSheet(); elementos = []
            try: logo = RLImage(self.icon_path, width=50, height=50); logo.hAlign='CENTER'; elementos.append(logo)
            except: pass
            elementos.append(Paragraph("CONSULTORIO NATURISTA", styles['Title']))
            elementos.append(Paragraph(f"Paciente: {pac}", styles['Normal']))
            elementos.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal'])); elementos.append(Spacer(1,15))
            datos = [["PRODUCTO", "CANTIDAD"]]
            h_p = self.libro.worksheet("Pastillas")
            h_v = self.libro.worksheet("Varios")
            for nombre, d in self.carrito_items.items():
                cant_v = int(d["cant_ent"].get()); datos.append([nombre, str(cant_v)])
                c = h_p.find(nombre.lower())
                if c: h_p.update_cell(c.row, 2, int(h_p.cell(c.row, 2).value) - cant_v)
                else:
                    c = h_v.find(nombre.lower())
                    if c: h_v.update_cell(c.row, 2, int(h_v.cell(c.row, 2).value) - cant_v)
            t = Table(datos, colWidths=[320, 80]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0), colors.limegreen), ('GRID',(0,0),(-1,-1), 1, colors.grey)]))
            elementos.append(t); doc.build(elementos)
            self.vaciar_carrito(); self.precargar_datos(); self.actualizar_tabla(self.scroll_ventas); self.mostrar_notif_ventas("✔ Venta confirmada", "#25751B")
        except Exception as e: messagebox.showerror("Error PDF", f"Error: {e}")

    # --- LÓGICA INVENTARIO ---
    def registrar_nuevo(self):
        p, c = self.entry_p_nuevo.get().strip().lower(), self.entry_c_nuevo.get().strip()
        if p and c.isdigit():
            if self.hoja.find(p): self.mostrar_notif_inv("Producto ya existe", "#FF9F0A"); return
            self.ultima_accion = ("nuevo", p, None); self.hoja.append_row([p, c]); self.hoja.sort((1, 'asc'), range='A2:B1000')
            self.precargar_datos(); self.actualizar_tabla(self.scroll_inv); self.mostrar_notif_inv(f"Registrado: {p.upper()}", "#0a84ff"); self.vaciar_campos()

    def ejecutar_suma(self):
        p, c = self.entry_p_suma.get().strip().lower(), self.entry_c_suma.get().strip()
        if p and c.isdigit():
            celda = self.hoja.find(p)
            if celda:
                v = self.hoja.cell(celda.row, 2).value; self.ultima_accion = ("suma", p, v)
                self.hoja.update_cell(celda.row, 2, int(v or 0) + int(c)); self.precargar_datos(); self.actualizar_tabla(self.scroll_inv); self.mostrar_notif_inv("Stock Sumado", "#34c759"); self.vaciar_campos()

    def corregir_valor(self):
        pn, cn = self.entry_p_gest.get().strip().lower(), self.entry_c_gest.get().strip()
        if self.nombre_original_seleccionado and pn and cn.isdigit():
            celda = self.hoja.find(self.nombre_original_seleccionado)
            if celda:
                v = self.hoja.cell(celda.row, 2).value; self.ultima_accion = ("edit", self.nombre_original_seleccionado, (pn, v))
                self.hoja.update_cell(celda.row, 1, pn); self.hoja.update_cell(celda.row, 2, cn); self.hoja.sort((1, 'asc'), range='A2:B1000')
                self.precargar_datos(); self.actualizar_tabla(self.scroll_inv); self.mostrar_notif_inv("Actualizado", "#ff9f0a"); self.vaciar_campos()

    def eliminar_producto(self):
        p = self.entry_p_gest.get().strip().lower()
        if p:
            celda = self.hoja.find(p)
            if celda:
                v = self.hoja.cell(celda.row, 2).value; self.ultima_accion = ("borrado", p, v)
                self.hoja.delete_rows(celda.row); self.precargar_datos(); self.actualizar_tabla(self.scroll_inv); self.mostrar_notif_inv("Eliminado", "#ff3b30"); self.vaciar_campos()

    def deshacer_accion(self):
        if not self.hoja or not self.ultima_accion: return
        t, n, v = self.ultima_accion
        try:
            if t == "nuevo": c = self.hoja.find(n); self.hoja.delete_rows(c.row) if c else None
            elif t == "suma": c = self.hoja.find(n); self.hoja.update_cell(c.row, 2, v) if c else None
            elif t == "edit":
                nn, va = v; c = self.hoja.find(nn)
                if c: self.hoja.update_cell(c.row, 1, n); self.hoja.update_cell(c.row, 2, va)
            elif t == "borrado": self.hoja.append_row([n, v])
            self.ultima_accion = None; self.btn_undo.configure(state="disabled"); self.hoja.sort((1, 'asc'), range='A2:B1000')
            self.actualizar_tabla(self.scroll_inv); self.mostrar_notif_inv("Deshecho", "#5856d6")
        except: pass

    # --- AUXILIARES ---
    def quitar_item(self, nombre): self.carrito_items[nombre]["frame"].destroy(); del self.carrito_items[nombre]
    def vaciar_carrito(self): [self.quitar_item(n) for n in list(self.carrito_items.keys())]; self.ent_paciente.delete(0, "end")
    def mostrar_notif_inv(self, m, c): self.lbl_notif_inv.configure(text=m, text_color=c); self.btn_undo.configure(state="normal") if "Prod" not in m else None; self.after(3000, lambda: self.lbl_notif_inv.configure(text=""))
    def mostrar_notif_ventas(self, m, c): self.lbl_notif_ventas.configure(text=m, text_color=c); self.after(3000, lambda: self.lbl_notif_ventas.configure(text=""))
    def vaciar_campos(self): [e.delete(0, "end") for e in [self.entry_p_nuevo, self.entry_c_nuevo, self.entry_p_suma, self.entry_c_suma, self.entry_p_gest, self.entry_c_gest]]; self.nombre_original_seleccionado = None
    
    def conectar_google(self): 
        try: return gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name('credenciales.json', ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])).open("Consultorio_prueba")
        except: return None
    def generar_pdf_inventario(self, filtro=False):
        ahora = datetime.now(); timestamp = ahora.strftime("%d-%m-%Y_%H-%M"); tipo = "Poco_Stock" if filtro else "Completo"
        sug = f"Inventario_{self.selector_ho_set}_{tipo}_{timestamp}.pdf"; ruta = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=sug)
        if not ruta: return
        try:
            doc = SimpleDocTemplate(ruta, pagesize=letter); styles = getSampleStyleSheet(); elementos = []
            elementos.append(Paragraph(f"REPORTE DE INVENTARIO - {self.selector_ho_set.upper()}", styles['Title']))
            elementos.append(Paragraph(f"Generado: {ahora.strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal'])); elementos.append(Spacer(1, 15))
            datos = [["PRODUCTO", "STOCK"]]
            for f in self.datos_locales[self.selector_ho_set]:
                if filtro and int(f[1]) > 4: continue
                datos.append([f[0].upper(), f[1]])
            h_col = colors.red if filtro else colors.limegreen; t_col = colors.white if filtro else colors.black
            t = Table(datos, colWidths=[300, 80]); t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), h_col),('TEXTCOLOR', (0, 0), (-1, 0), t_col),('GRID', (0, 0), (-1, -1), 0.5, colors.grey),('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
            elementos.append(t); doc.build(elementos); self.mostrar_notif_inv("Reporte generado con éxito", "#25751B")
        except Exception as e: messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = AppConsultorio()
    app.mainloop()