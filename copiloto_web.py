import streamlit as st
import pandas as pd
from pathlib import Path
import io
import qrcode
from PIL import Image

# Importar lógica del calculador enológico
from calculador_enologico import (
    calcular_metabisulfito,
    calcular_acido_tartarico,
    calcular_nutricion_nitrogenada,
    parsear_ficha_markdown,
    ENOLOGIA_DIR
)

st.set_page_config(
    page_title="Copiloto Enológico & Bodega 4.0",
    page_icon="🍇",
    layout="wide"
)

st.markdown("""
# 🍇 Copiloto Enológico & Bodega 4.0
**Centro de Operaciones Enológicas y Trazabilidad**  
*Enólogo & Operador:* **Cristián González Huenchún** · *Bóveda:* `Obsidian Vault`
""")

tab_monitor, tab_calculadora, tab_barricas = st.tabs([
    "📊 Monitor de Bodega (Fichas Obsidian)",
    "🧮 Calculadora Interactiva de Dosis",
    "🏷️ Generador de QR & Trazabilidad B2B"
])

# ----------------------------------------------------
# TAB 1: MONITOR DE BODEGA EN VIVO
# ----------------------------------------------------
with tab_monitor:
    st.subheader("Estado en Tiempo Real de Cubas y Foudres")
    fichas = sorted(list(ENOLOGIA_DIR.glob("Ficha_Cuba_*.md")))
    
    if not fichas:
        st.warning("No se encontraron fichas de cubas en `02_Enologia_Agro/`.")
    else:
        cubas_data = [parsear_ficha_markdown(f) for f in fichas]
        df = pd.DataFrame(cubas_data)

        # Métricas generales
        vol_total = df["volumen_l"].sum()
        num_cubas = len(df)
        cubas_fa = df[df["estado"].str.contains("Fermentación", case=False, na=False)].shape[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("Volumen Total en Bodega", f"{vol_total:,.0f} L", f"{vol_total/100:.1f} hL")
        col2.metric("Cubas Registradas", f"{num_cubas} unidades")
        col3.metric("Cubas en Fermentación (FA)", f"{cubas_fa} activas")

        st.markdown("### Tabla Resumen de Tanques")
        st.dataframe(
            df[["identificador", "variedad", "volumen_l", "estado", "ph", "so2_libre", "acidez_total", "yan_actual", "densidad"]].rename(columns={
                "identificador": "Tanque",
                "variedad": "Variedad",
                "volumen_l": "Volumen (L)",
                "estado": "Estado",
                "ph": "pH",
                "so2_libre": "SO₂ Libre (mg/L)",
                "acidez_total": "Acidez (g/L)",
                "yan_actual": "YAN (mg N/L)",
                "densidad": "Densidad"
            }),
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("### Inspección y Órdenes de Trabajo por Cuba")
        opciones_cuba = {f"{c['identificador']} ({c['variedad']})": c for c in cubas_data}
        seleccion = st.selectbox("Selecciona una cuba para emitir reporte:", list(opciones_cuba.keys()))
        cuba = opciones_cuba[seleccion]

        litros = cuba["volumen_l"]
        hl = litros / 100.0

        c1, c2, c3 = st.columns(3)
        
        # 1. Sulfuroso
        with c1:
            st.markdown("#### 🧪 Sulfuroso (SO₂)")
            so2_obj = 30.0 if "crianza" not in cuba["estado"].lower() else 32.0
            if cuba["so2_libre"] is not None:
                meta = calcular_metabisulfito(hl, cuba["so2_libre"], so2_obj)
                st.write(f"**Actual:** {cuba['so2_libre']} mg/L $\\rightarrow$ **Obj:** {so2_obj} mg/L")
                if meta["gramos"] > 0:
                    st.error(f"⚠️ **Adicionar:** {meta['gramos']:.1f} g de Metabisulfito de Potasio.")
                    st.caption(f"Dosis: {meta['dosis_g_hl']:.1f} g/hL ({meta['kg']:.3f} kg)")
                else:
                    st.success("✅ Nivel de SO₂ correcto.")
            else:
                st.info("Sin registro de SO₂.")

        # 2. Acidez
        with c2:
            st.markdown("#### 🍋 Acidez Total")
            if cuba["acidez_total"] is not None:
                tart = calcular_acido_tartarico(litros, cuba["acidez_total"], 5.5)
                st.write(f"**Actual:** {cuba['acidez_total']} g/L $\\rightarrow$ **Obj:** 5.5 g/L")
                if tart["kg"] > 0:
                    st.warning(f"⚠️ **Adicionar:** {tart['kg']:.2f} kg de Ácido Tartárico.")
                else:
                    st.success("✅ Acidez dentro de rango.")
            else:
                st.info("Sin registro de acidez.")

        # 3. YAN / Nutrición
        with c3:
            st.markdown("#### 🧬 Nutrición YAN/FAN")
            if cuba["yan_actual"] is not None:
                nut = calcular_nutricion_nitrogenada(
                    volumen_hl=hl,
                    yan_actual=cuba["yan_actual"],
                    alcohol_potencial_o_brix=cuba["grado_alcoholico"],
                    yan_objetivo=cuba["yan_objetivo"],
                    densidad_actual=cuba["densidad"]
                )
                st.write(f"**Actual:** {cuba['yan_actual']} mg N/L $\\rightarrow$ **Obj:** {nut['yan_objetivo']} mg N/L")
                if nut["delta_yan"] > 0:
                    st.error(f"🚨 **Déficit:** {nut['delta_yan']:.1f} mg N/L")
                    st.write(f"• **Orgánico:** {nut['organico_total_kg']} kg ({nut['organico_g_hl']} g/hL)")
                    st.write(f"• **DAP:** {nut['dap_total_kg']} kg ({nut['dap_g_hl']} g/hL)")
                    st.caption(nut["momento"])
                else:
                    st.success("✅ Nutrición nitrogenada óptima.")
            else:
                st.info("No aplica (FA terminada o vino estabilizado).")

# ----------------------------------------------------
# TAB 2: CALCULADORA RÁPIDA DE DOSIS
# ----------------------------------------------------
with tab_calculadora:
    st.subheader("Simulador de Correcciones Rápidas en Bodega")
    
    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        sim_volumen = st.number_input("Volumen de Vino / Mosto (Litros):", min_value=100, max_value=200000, value=10000, step=500)
        sim_hl = sim_volumen / 100.0
        
        st.markdown("##### Corrección de SO₂ Libre")
        sim_so2_act = st.number_input("SO₂ Libre Actual (mg/L):", value=15.0, step=1.0)
        sim_so2_obj = st.number_input("SO₂ Libre Objetivo (mg/L):", value=30.0, step=1.0)

        st.markdown("##### Corrección de Acidez")
        sim_ac_act = st.number_input("Acidez Actual (g/L):", value=4.6, step=0.1)
        sim_ac_obj = st.number_input("Acidez Objetivo (g/L):", value=5.5, step=0.1)

    with col_sim2:
        st.markdown("##### Nutrición Nitrogenada (YAN)")
        aplica_yan = st.checkbox("¿En fermentación alcohólica (calcular YAN)?", value=True)
        if aplica_yan:
            sim_yan_act = st.number_input("YAN / FAN Medido (mg N/L):", value=130.0, step=5.0)
            sim_brix = st.number_input("Azúcar Inicial (°Brix) o Grado Potencial (% vol):", value=13.5, step=0.5)
            sim_densidad = st.number_input("Densidad Actual (g/mL):", value=1.035, step=0.005, format="%.3f")

    if st.button("🚀 Calcular Órdenes de Dosificación", use_container_width=True):
        st.markdown("### 📋 Orden de Trabajo Oficial")
        res_col1, res_col2 = st.columns(2)
        
        with res_col1:
            meta = calcular_metabisulfito(sim_hl, sim_so2_act, sim_so2_obj)
            st.info(f"**Metabisulfito de Potasio:** Pesar **{meta['gramos']:.1f} g** ({meta['kg']:.3f} kg)  \n*Dosis:* {meta['dosis_g_hl']:.1f} g/hL")
            
            tart = calcular_acido_tartarico(sim_volumen, sim_ac_act, sim_ac_obj)
            st.warning(f"**Ácido Tartárico:** Pesar **{tart['kg']:.2f} kg**  \n*Dosis:* {tart['dosis_g_l']:.2f} g/L")

        with res_col2:
            if aplica_yan:
                nut = calcular_nutricion_nitrogenada(
                    volumen_hl=sim_hl,
                    yan_actual=sim_yan_act,
                    alcohol_potencial_o_brix=sim_brix,
                    densidad_actual=sim_densidad
                )
                if nut["delta_yan"] > 0:
                    st.error(f"""
                    **Nutrición Nitrogenada (Δ = {nut['delta_yan']:.1f} mg N/L):**
                    - **Nutriente Orgánico:** {nut['organico_total_kg']:.2f} kg ({nut['organico_g_hl']} g/hL)
                    - **DAP (Fosfato Diamónico):** {nut['dap_total_kg']:.2f} kg ({nut['dap_g_hl']} g/hL)
                    - *Instrucción:* {nut['momento']}
                    """)
                else:
                    st.success("✅ YAN en rango óptimo. No requiere corrección.")

# ----------------------------------------------------
# TAB 3: TRAZABILIDAD DE BARRICAS & GENERADOR QR (B2B MVP)
# ----------------------------------------------------
with tab_barricas:
    st.subheader("Sistema Inteligente de Barricas por QR (MVP B2B)")
    st.markdown("""
    Generación de identificadores únicos para etiquetado físico de barricas en bodega.
    Al escanear el código QR con cualquier teléfono o tablet, el operario accede a la ficha viva en Obsidian o Baserow.
    """)

    b_col1, b_col2 = st.columns(2)
    with b_col1:
        codigo_barrica = st.text_input("Código Único de Barrica:", value="BAR-2026-001")
        vino_barrica = st.text_input("Vino / Cuartel / Lote:", value="Cabernet Sauvignon 2026 - Cuartel 4")
        roble_tipo = st.selectbox("Origen de Madera:", ["Roble Francés (Tronçais)", "Roble Francés (Allier)", "Roble Americano", "Mixto"])
        tostado = st.selectbox("Nivel de Tostado:", ["Ligero", "Medio", "Medio Plus (M+)", "Fuerte"])
        fecha_ouillage = st.date_input("Fecha Último Relleno (Ouillage):")
        notas_barrica = st.text_area("Observaciones Enológicas:", value="Barrica de 1er uso. Excelente microoxigenación. Libre de Brettanomyces.")

    with b_col2:
        # Generar contenido embebido en el QR
        payload_qr = f"""--- REGISTRO BARRICA 4.0 ---
Código: {codigo_barrica}
Vino: {vino_barrica}
Madera: {roble_tipo} | Tostado: {tostado}
Último Ouillage: {fecha_ouillage}
Notas: {notas_barrica}
Verificado por: Cristián González Huenchún
----------------------------"""

        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(payload_qr)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="#2b001a", back_color="white")

        buf = io.BytesIO()
        img_qr.save(buf, format="PNG")
        byte_im = buf.getvalue()

        st.image(byte_im, caption=f"Código QR Generado para {codigo_barrica}", width=250)
        st.download_button(
            label=f"📥 Descargar QR para Imprimir ({codigo_barrica}.png)",
            data=byte_im,
            file_name=f"{codigo_barrica}.png",
            mime="image/png"
        )
