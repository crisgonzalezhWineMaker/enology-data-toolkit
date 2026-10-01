"""
Copiloto Enológico - Interfaz de Escritorio Nativa (Estilo InfoStat / Software Técnico)
Desarrollado con CustomTkinter para Cristián González Huenchún.
"""

import sys
import customtkinter as ctk
from pathlib import Path

# Configuración visual moderna
ctk.set_appearance_mode("Dark")  # "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

# Importar cálculos del motor enológico
from calculador_enologico import (
    calcular_metabisulfito,
    calcular_acido_tartarico,
    calcular_nutricion_nitrogenada,
    parsear_ficha_markdown,
    ENOLOGIA_DIR
)

class AppCopiloto(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🍇 Copiloto Enológico 4.0 - Estación de Trabajo")
        self.geometry("980x640")
        self.minsize(850, 550)

        # Configurar grid principal (1 columna lateral, 1 columna central)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._crear_panel_lateral()
        self._crear_panel_central()
        self._cargar_fichas_disponibles()

    def _crear_panel_lateral(self):
        self.panel_izq = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.panel_izq.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.panel_izq.grid_rowconfigure(10, weight=1)

        # Título
        lbl_logo = ctk.CTkLabel(
            self.panel_izq, 
            text="🍇 COPILOTO\nENOLÓGICO", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        lbl_logo.grid(row=0, column=0, padx=20, pady=(20, 10))

        lbl_sub = ctk.CTkLabel(
            self.panel_izq, 
            text="Operador: Cristián González H.\nBóveda: Obsidian Activa", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        lbl_sub.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Selector de Ficha
        lbl_sel = ctk.CTkLabel(self.panel_izq, text="📁 Seleccionar Cuba de Bodega:", font=ctk.CTkFont(weight="bold"))
        lbl_sel.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")

        self.combo_fichas = ctk.CTkComboBox(
            self.panel_izq, 
            values=["Cargando..."],
            command=self._al_seleccionar_cuba,
            width=240
        )
        self.combo_fichas.grid(row=3, column=0, padx=20, pady=5)

        btn_recargar = ctk.CTkButton(
            self.panel_izq, 
            text="🔄 Recargar Fichas Obsidian", 
            command=self._cargar_fichas_disponibles,
            fg_color="#2b3e50"
        )
        btn_recargar.grid(row=4, column=0, padx=20, pady=10)

        # Separador
        lbl_sep = ctk.CTkLabel(self.panel_izq, text="--- Modo de Interfaz ---", text_color="gray")
        lbl_sep.grid(row=5, column=0, padx=20, pady=(20, 5))

        self.modo_tema = ctk.CTkOptionMenu(
            self.panel_izq, 
            values=["Dark", "Light"],
            command=lambda m: ctk.set_appearance_mode(m)
        )
        self.modo_tema.grid(row=6, column=0, padx=20, pady=5)

    def _crear_panel_central(self):
        self.panel_der = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.panel_der.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.panel_der.grid_columnconfigure((0, 1), weight=1)

        # Header de la sección
        lbl_header = ctk.CTkLabel(
            self.panel_der, 
            text="⚙️ Parámetros de Entrada & Correcciones Físico-Químicas",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # Inputs en grilla (Estilo formulario InfoStat)
        # 1. Volumen
        lbl_vol = ctk.CTkLabel(self.panel_der, text="Volumen Actual (Litros):", font=ctk.CTkFont(weight="bold"))
        lbl_vol.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.entry_vol = ctk.CTkEntry(self.panel_der, placeholder_text="15000")
        self.entry_vol.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.entry_vol.insert(0, "15000")

        # 2. SO2 Libre
        lbl_so2 = ctk.CTkLabel(self.panel_der, text="SO₂ Libre Actual (mg/L):", font=ctk.CTkFont(weight="bold"))
        lbl_so2.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.entry_so2 = ctk.CTkEntry(self.panel_der, placeholder_text="12.0")
        self.entry_so2.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        self.entry_so2.insert(0, "12.0")

        # 3. SO2 Objetivo
        lbl_so2_obj = ctk.CTkLabel(self.panel_der, text="SO₂ Libre Objetivo (mg/L):", font=ctk.CTkFont(weight="bold"))
        lbl_so2_obj.grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.entry_so2_obj = ctk.CTkEntry(self.panel_der, placeholder_text="30.0")
        self.entry_so2_obj.grid(row=3, column=1, sticky="ew", padx=10, pady=5)
        self.entry_so2_obj.insert(0, "30.0")

        # 4. Acidez Total
        lbl_ac = ctk.CTkLabel(self.panel_der, text="Acidez Total Medida (g/L):", font=ctk.CTkFont(weight="bold"))
        lbl_ac.grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.entry_ac = ctk.CTkEntry(self.panel_der, placeholder_text="4.8")
        self.entry_ac.grid(row=4, column=1, sticky="ew", padx=10, pady=5)
        self.entry_ac.insert(0, "4.8")

        # 5. YAN
        lbl_yan = ctk.CTkLabel(self.panel_der, text="Nitrógeno Asimilable YAN (mg N/L):", font=ctk.CTkFont(weight="bold"))
        lbl_yan.grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.entry_yan = ctk.CTkEntry(self.panel_der, placeholder_text="140.0")
        self.entry_yan.grid(row=5, column=1, sticky="ew", padx=10, pady=5)
        self.entry_yan.insert(0, "140.0")

        # 6. Densidad
        lbl_den = ctk.CTkLabel(self.panel_der, text="Densidad Actual (g/mL):", font=ctk.CTkFont(weight="bold"))
        lbl_den.grid(row=6, column=0, sticky="w", padx=10, pady=5)
        self.entry_den = ctk.CTkEntry(self.panel_der, placeholder_text="1.025")
        self.entry_den.grid(row=6, column=1, sticky="ew", padx=10, pady=5)
        self.entry_den.insert(0, "1.025")

        # Botón de Cálculo Principal
        btn_calcular = ctk.CTkButton(
            self.panel_der, 
            text="🚀 CALCULAR DOSIFICACIÓN EN BODEGA", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._ejecutar_calculo,
            fg_color="#1f77b4",
            hover_color="#145682"
        )
        btn_calcular.grid(row=7, column=0, columnspan=2, sticky="ew", padx=10, pady=15)

        # Área de Reporte y Diagnóstico
        lbl_res = ctk.CTkLabel(
            self.panel_der, 
            text="📋 Orden de Trabajo Oficial Generada:", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        lbl_res.grid(row=8, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        self.txt_resultado = ctk.CTkTextbox(
            self.panel_der, 
            height=180, 
            font=ctk.CTkFont(family="Consolas", size=13)
        )
        self.txt_resultado.grid(row=9, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

    def _cargar_fichas_disponibles(self):
        fichas = sorted(list(ENOLOGIA_DIR.glob("Ficha_Cuba_*.md")))
        self.fichas_map = {}
        nombres = []
        for f in fichas:
            datos = parsear_ficha_markdown(f)
            nombre = f"{datos['identificador']} ({datos['variedad']}) - {f.name}"
            self.fichas_map[nombre] = datos
            nombres.append(nombre)

        if nombres:
            self.combo_fichas.configure(values=nombres)
            self.combo_fichas.set(nombres[0])
            self._al_seleccionar_cuba(nombres[0])
        else:
            self.combo_fichas.configure(values=["No hay fichas .md"])

    def _al_seleccionar_cuba(self, seleccion):
        if seleccion in self.fichas_map:
            cuba = self.fichas_map[seleccion]
            self.entry_vol.delete(0, "end")
            self.entry_vol.insert(0, str(int(cuba["volumen_l"])))

            self.entry_so2.delete(0, "end")
            self.entry_so2.insert(0, str(cuba["so2_libre"] if cuba["so2_libre"] is not None else 15.0))

            self.entry_ac.delete(0, "end")
            self.entry_ac.insert(0, str(cuba["acidez_total"] if cuba["acidez_total"] is not None else 5.0))

            if cuba["yan_actual"] is not None:
                self.entry_yan.delete(0, "end")
                self.entry_yan.insert(0, str(cuba["yan_actual"]))

            if cuba["densidad"] is not None:
                self.entry_den.delete(0, "end")
                self.entry_den.insert(0, str(cuba["densidad"]))

            self._ejecutar_calculo()

    def _ejecutar_calculo(self):
        try:
            litros = float(self.entry_vol.get().replace(",", "."))
            hl = litros / 100.0
            so2_act = float(self.entry_so2.get().replace(",", "."))
            so2_obj = float(self.entry_so2_obj.get().replace(",", "."))
            ac_act = float(self.entry_ac.get().replace(",", "."))
            yan_act = float(self.entry_yan.get().replace(",", "."))
            den_act = float(self.entry_den.get().replace(",", "."))

            meta = calcular_metabisulfito(hl, so2_act, so2_obj)
            tart = calcular_acido_tartarico(litros, ac_act, 5.5)
            nut = calcular_nutricion_nitrogenada(
                volumen_hl=hl,
                yan_actual=yan_act,
                alcohol_potencial_o_brix=13.5,
                densidad_actual=den_act
            )

            reporte = []
            reporte.append("=" * 65)
            reporte.append(f"🍇 ORDEN DE BODEGA | Volumen: {litros:,.0f} L ({hl:.1f} hL)")
            reporte.append("=" * 65)

            # Sulfuroso
            if meta["gramos"] > 0:
                reporte.append(f"1. SULFUROSO: Pesar {meta['gramos']:.1f} g ({meta['kg']:.3f} kg) de Metabisulfito de K.")
                reporte.append(f"   Dosis: {meta['dosis_g_hl']:.1f} g/hL | Delta SO2: {meta['delta_so2']:.1f} mg/L.")
            else:
                reporte.append("1. SULFUROSO: Nivel óptimo. No requiere adición.")

            # Acidez
            if tart["kg"] > 0:
                reporte.append(f"2. ACIDEZ: Pesar {tart['kg']:.2f} kg de Ácido Tartárico (disolver previo).")
                reporte.append(f"   Dosis: {tart['dosis_g_l']:.2f} g/L (Delta Acidez: {tart['delta_acidez']:.2f} g/L).")
            else:
                reporte.append("2. ACIDEZ: Acidez total dentro de rango objetivo.")

            # Nutrición
            if nut["delta_yan"] > 0:
                reporte.append(f"3. NUTRICIÓN LEVADURAS (Delta YAN: {nut['delta_yan']:.1f} mg N/L):")
                reporte.append(f"   • Nutriente Orgánico : {nut['organico_total_kg']:.2f} kg ({nut['organico_g_hl']} g/hL)")
                reporte.append(f"   • DAP (Sales amonio) : {nut['dap_total_kg']:.2f} kg ({nut['dap_g_hl']} g/hL)")
                reporte.append(f"   📌 ALERTA: {nut['momento']}")
            else:
                reporte.append("3. NUTRICIÓN: YAN óptimo. Sin riesgo de estrés nitrogenado.")

            reporte.append("=" * 65)

            self.txt_resultado.delete("1.0", "end")
            self.txt_resultado.insert("1.0", "\n".join(reporte))

        except Exception as e:
            self.txt_resultado.delete("1.0", "end")
            self.txt_resultado.insert("1.0", f"Error en los parámetros ingresados: {e}")

if __name__ == "__main__":
    app = AppCopiloto()
    app.mainloop()
