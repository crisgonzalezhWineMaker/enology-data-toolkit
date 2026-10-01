"""
Script Operativo: Calculador Enológico Conectado a Obsidian (Versión 2.0)
Automatización para bodega:
1. Corrección de Sulfuroso ($SO_2$ Libre con Metabisulfito de Potasio)
2. Acidificación (Ajuste de Acidez Total con Ácido Tartárico)
3. Nutrición Nitrogenada (YAN/FAN - DAP y Nutriente Orgánico) para prevención de reducciones y paradas de FA.

Lee fichas vivas en Markdown (.md) desde 02_Enologia_Agro/ y genera órdenes de bodega directas.
"""

import sys
import re
from pathlib import Path

# Asegurar codificación UTF-8 en terminal de Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

VAULT_DIR = Path(__file__).resolve().parent.parent
ENOLOGIA_DIR = VAULT_DIR / "02_Enologia_Agro"

def calcular_metabisulfito(volumen_hl: float, so2_actual: float, so2_objetivo: float) -> dict:
    """
    Fórmula enológica: Metabisulfito (g) = (Delta SO2 libre * hL) / 5
    El metabisulfito de potasio (K2S2O5) aporta aprox 50% de SO2 molecular/activo.
    """
    delta_so2 = max(0.0, so2_objetivo - so2_actual)
    gramos = (delta_so2 * volumen_hl) / 5.0
    return {
        "delta_so2": delta_so2,
        "gramos": gramos,
        "kg": gramos / 1000.0,
        "dosis_g_hl": (delta_so2 / 5.0) * 10.0 if volumen_hl > 0 else 0.0
    }

def calcular_acido_tartarico(volumen_l: float, acidez_actual: float, acidez_objetivo: float) -> dict:
    """
    Fórmula: Kg Ácido Tartárico = (Delta Acidez en g/L * Litros) / 1000
    Expresado comúnmente en equivalentes de ácido tartárico o sulfúrico.
    """
    delta_acidez = max(0.0, acidez_objetivo - acidez_actual)
    kg = (delta_acidez * volumen_l) / 1000.0
    return {
        "delta_acidez": delta_acidez,
        "kg": kg,
        "gramos": kg * 1000.0,
        "dosis_g_l": delta_acidez
    }

def calcular_acidez_total_titulacion(ml_naoh: float) -> float:
    """Fórmula volumétrica: Acidez Total (g/L Ácido Tartárico) = n * 0.75"""
    return round(ml_naoh * 0.75, 2)

def calcular_indices_glories(a420: float, a520: float, a620: float) -> dict:
    """
    Método de Glories:
    Intensidad Colorante (IC) = A420 + A520 + A620
    Tonalidad (N) = (A420 / A520) * 100
    """
    ic = a420 + a520 + a620
    tonalidad = (a420 / a520) * 100.0 if a520 > 0 else 0.0
    comp_amarillo = (a420 / ic) * 100.0 if ic > 0 else 0.0
    comp_rojo = (a520 / ic) * 100.0 if ic > 0 else 0.0
    comp_azul = (a620 / ic) * 100.0 if ic > 0 else 0.0
    return {
        "intensidad_colorante": round(ic, 3),
        "tonalidad": round(tonalidad, 2),
        "pct_amarillo": round(comp_amarillo, 1),
        "pct_rojo": round(comp_rojo, 1),
        "pct_azul": round(comp_azul, 1)
    }

def calcular_antocianos_totales(a520: float, factor_dilucion: float = 1.0) -> float:
    """Fórmula Puissant-León: Antocianos (mg/L) = A520 * 20 * Factor Dilución"""
    return round(a520 * 20.0 * factor_dilucion, 1)

def calcular_taninos_condensados(a1: float, a2: float) -> float:
    """
    Método de hidrólisis ácida a 100°C:
    Taninos Condensados (g/L) = (A1 - A2) * 19.33
    Donde A1 es absorbancia tras tubo a 100°C y A2 es el testigo a temperatura ambiente.
    """
    return round(max(0.0, (a1 - a2) * 19.33), 2)


def calcular_nutricion_nitrogenada(
    volumen_hl: float, 
    yan_actual: float, 
    alcohol_potencial_o_brix: float = 13.5, 
    yan_objetivo: float = None,
    densidad_actual: float = None
) -> dict:
    """
    Cálculo de Requerimientos de Nitrógeno Asimilable por Levaduras (YAN / FAN / NAL).
    
    Regla enológica:
    - Mostos con < 21 °Brix (< 12.5% vol): YAN mín = 150 mg N/L.
    - Mostos 21-23 °Brix (12.5-13.5% vol): YAN mín = 200 mg N/L.
    - Mostos 23-25 °Brix (13.5-14.5% vol): YAN mín = 250 mg N/L.
    - Mostos > 25 °Brix (> 14.5% vol): YAN mín = 300 mg N/L.
    
    Aportes comerciales estándar:
    - DAP (Fosfato Diamónico): 10 g/hL aportan ~21 mg N/L de nitrógeno amoniacal puro.
    - Nutriente Orgánico (derivados levadura): 10 g/hL aportan ~10 mg N/L de FAN (aminoácidos).
    
    Estrategia recomendada: 50% Orgánico al inicio de FA + 50% DAP al tercio de FA (densidad 1.050-1.030).
    """
    if yan_objetivo is None:
        if alcohol_potencial_o_brix < 12.5:
            yan_objetivo = 160.0
        elif alcohol_potencial_o_brix <= 13.5:
            yan_objetivo = 210.0
        elif alcohol_potencial_o_brix <= 14.5:
            yan_objetivo = 250.0
        else:
            yan_objetivo = 300.0

    delta_yan = max(0.0, yan_objetivo - yan_actual)

    if delta_yan == 0:
        return {
            "delta_yan": 0.0,
            "yan_objetivo": yan_objetivo,
            "estado": "Óptimo",
            "dap_g_hl": 0.0,
            "dap_total_kg": 0.0,
            "organico_g_hl": 0.0,
            "organico_total_kg": 0.0,
            "instruccion": "YAN suficiente. No requiere adición de sales amoniacales."
        }

    # Distribución enológica: 40% Orgánico + 60% Mineral (DAP) para cinética suave sin shock térmico
    yan_organico_necesario = delta_yan * 0.40
    yan_dap_necesario = delta_yan * 0.60

    # 1 g/hL orgánico aporta aprox 1.0 mg N/L
    dosis_organico_g_hl = min(40.0, yan_organico_necesario / 1.0)
    # 1 g/hL DAP aporta aprox 2.1 mg N/L
    dosis_dap_g_hl = min(40.0, yan_dap_necesario / 2.1)

    total_organico_kg = (dosis_organico_g_hl * volumen_hl) / 1000.0
    total_dap_kg = (dosis_dap_g_hl * volumen_hl) / 1000.0

    # Determinar momento según densidad
    if densidad_actual is not None:
        if densidad_actual > 1.060:
            momento = "FA Temprana: Adicionar Nutriente Orgánico ahora. Reservar DAP para tercio de FA (1.040)."
        elif 1.020 <= densidad_actual <= 1.060:
            momento = "🚨 FASE CRÍTICA (1/3 FA): Adicionar DAP disuelto en mosto ahora para evitar síntesis de H2S (reducción)."
        else:
            momento = "FA Terminal (Densidad < 1.020): ¡PRECAUCIÓN! Las levaduras ya no asimilan bien amonio. Usar solo cortezas de levadura/soporte si hay riesgo de parada."
    else:
        momento = "Estrategia estándar: Dosificar Nutriente Orgánico en siembra y DAP a densidad 1.040."

    return {
        "delta_yan": delta_yan,
        "yan_objetivo": yan_objetivo,
        "estado": "Déficit Nitrogenado",
        "dap_g_hl": round(dosis_dap_g_hl, 1),
        "dap_total_kg": round(total_dap_kg, 2),
        "organico_g_hl": round(dosis_organico_g_hl, 1),
        "organico_total_kg": round(total_organico_kg, 2),
        "momento": momento
    }

def parsear_ficha_markdown(ruta_ficha: Path) -> dict:
    texto = ruta_ficha.read_text(encoding="utf-8")
    
    # 1. Intentar extraer de Frontmatter YAML
    datos = {
        "archivo": ruta_ficha.name,
        "identificador": ruta_ficha.stem,
        "variedad": "Desconocida",
        "volumen_l": 10000.0,
        "so2_libre": None,
        "acidez_total": None,
        "ph": None,
        "yan_actual": None,
        "yan_objetivo": None,
        "densidad": None,
        "grado_alcoholico": 13.5,
        "estado": "Activo"
    }

    # Búsqueda regex tolerante tanto a YAML como a texto en prosa
    vol_m = re.search(r"(?:volumen_l:\s*|Volumen Actual:\*\*.*?)([\d\.]+)", texto, re.IGNORECASE)
    if vol_m:
        val_str = vol_m.group(1).replace(".", "")
        datos["volumen_l"] = float(val_str)

    id_m = re.search(r"(?:identificador:\s*\"?|Identificador:\*\*.*?)(Cuba\s*\d+|Foudre\s*\d+|[A-Za-z0-9_\-]+)", texto)
    if id_m:
        datos["identificador"] = id_m.group(1).strip('"')

    var_m = re.search(r"(?:variedad:\s*\"?|Variedad:\*\*.*?)([A-Za-z\s]+)(?:\"|\(|$|\n)", texto)
    if var_m:
        datos["variedad"] = var_m.group(1).strip()

    so2_m = re.search(r"(?:so2_libre_mg_l:\s*|\$SO_2\$ Libre:\*\*.*?)([\d\.]+)", texto, re.IGNORECASE)
    if so2_m:
        datos["so2_libre"] = float(so2_m.group(1))

    ac_m = re.search(r"(?:acidez_total_g_l:\s*|Acidez Total:\*\*.*?)([\d\.]+)", texto, re.IGNORECASE)
    if ac_m:
        datos["acidez_total"] = float(ac_m.group(1))

    ph_m = re.search(r"(?:ph:\s*|\$pH\$:\*\*.*?)([\d\.]+)", texto, re.IGNORECASE)
    if ph_m:
        datos["ph"] = float(ph_m.group(1))

    yan_m = re.search(r"(?:yan_actual_mg_l:\s*|YAN.*?Actual:\*\*.*?)([\d\.]+)", texto, re.IGNORECASE)
    if yan_m:
        datos["yan_actual"] = float(yan_m.group(1))

    yan_obj_m = re.search(r"(?:yan_objetivo_mg_l:\s*|YAN.*?Objetivo:\*\*.*?)([\d\.]+)", texto, re.IGNORECASE)
    if yan_obj_m:
        datos["yan_objetivo"] = float(yan_obj_m.group(1))

    den_m = re.search(r"(?:densidad:\s*|Densidad:\*\*.*?)([\d\.]+)", texto, re.IGNORECASE)
    if den_m:
        datos["densidad"] = float(den_m.group(1))

    alc_m = re.search(r"(?:grado_alcoholico:\s*|Grado Alcoh\u00f3lico:\*\*.*?)([\d\.]+)", texto, re.IGNORECASE)
    if alc_m:
        datos["grado_alcoholico"] = float(alc_m.group(1))

    est_m = re.search(r"(?:estado:\s*\"?|Estado Actual:\*\*.*?)([A-Za-z\u00e1\u00e9\u00ed\u00f3\u00fa\s\(\)/]+)(?:\"|\n|$)", texto)
    if est_m:
        datos["estado"] = est_m.group(1).strip()

    return datos

def generar_reporte_cuba(datos: dict):
    litros = datos["volumen_l"]
    hl = litros / 100.0

    print("=" * 70)
    print(f"🍇 COPILOTO ENOLÓGICO: {datos['identificador']} ({datos['variedad']})")
    print(f"   Archivo: {datos['archivo']} | Volumen: {litros:,.0f} L ({hl:.1f} hL)")
    print(f"   Estado Actual: {datos['estado']}")
    print("=" * 70)

    # 1. Corrección de SO2
    if datos["so2_libre"] is not None:
        so2_obj = 30.0 if "crianza" not in datos["estado"].lower() else 32.0
        meta = calcular_metabisulfito(hl, datos["so2_libre"], so2_obj)
        print(f"🔹 AJUSTE DE SULFUROSO:")
        print(f"   SO₂ Libre: {datos['so2_libre']} mg/L  -->  Objetivo: {so2_obj} mg/L  (Δ = {meta['delta_so2']:.1f} mg/L)")
        if meta["gramos"] > 0:
            print(f"   👉 DOSIS: Pesar {meta['gramos']:.1f} g ({meta['kg']:.3f} kg) de Metabisulfito de Potasio.")
            print(f"             Equivale a {meta['dosis_g_hl']:.1f} g/hL.")
        else:
            print("   ✅ SO₂ en nivel adecuado o superior al objetivo.")
        print("-" * 70)

    # 2. Corrección de Acidez
    if datos["acidez_total"] is not None:
        ac_obj = 5.5
        tart = calcular_acido_tartarico(litros, datos["acidez_total"], ac_obj)
        print(f"🔹 AJUSTE DE ACIDEZ TOTAL:")
        print(f"   Acidez Total: {datos['acidez_total']} g/L  -->  Objetivo: {ac_obj} g/L")
        if tart["kg"] > 0:
            print(f"   👉 DOSIS: Disolver {tart['kg']:.2f} kg de Ácido Tartárico en mosto previo al remontaje.")
        else:
            print("   ✅ Acidez total adecuada para el perfil.")
        print("-" * 70)

    # 3. Nutrición Nitrogenada (YAN/FAN)
    if datos["yan_actual"] is not None:
        nut = calcular_nutricion_nitrogenada(
            volumen_hl=hl,
            yan_actual=datos["yan_actual"],
            alcohol_potencial_o_brix=datos["grado_alcoholico"],
            yan_objetivo=datos["yan_objetivo"],
            densidad_actual=datos["densidad"]
        )
        print(f"🔹 DIAGNÓSTICO NUTRICIONAL LEVADURAS (YAN/FAN):")
        print(f"   YAN Actual: {datos['yan_actual']} mg N/L  -->  Objetivo: {nut['yan_objetivo']} mg N/L (Δ = {nut['delta_yan']:.1f} mg N/L)")
        print(f"   Densidad: {datos['densidad']} | Diagnóstico: {nut['estado']}")
        if nut["delta_yan"] > 0:
            print(f"   👉 DOSIS RECOMENDADA:")
            print(f"      1. Nutriente Orgánico (aminoácidos): {nut['organico_g_hl']} g/hL  -->  Total: {nut['organico_total_kg']} kg")
            print(f"      2. DAP (Fosfato Diamónico):        {nut['dap_g_hl']} g/hL  -->  Total: {nut['dap_total_kg']} kg")
            print(f"   📌 MOMENTO OPERATIVO: {nut['momento']}")
        else:
            print(f"   ✅ {nut['instruccion']}")
        print("-" * 70)

    print()

def procesar_todas():
    fichas = sorted(list(ENOLOGIA_DIR.glob("Ficha_Cuba_*.md")))
    if not fichas:
        print("[-] No se encontraron fichas vivas en 02_Enologia_Agro/")
        return
    for f in fichas:
        datos = parsear_ficha_markdown(f)
        generar_reporte_cuba(datos)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ruta = Path(sys.argv[1])
        if ruta.exists():
            datos = parsear_ficha_markdown(ruta)
            generar_reporte_cuba(datos)
        else:
            print(f"[-] Archivo no encontrado: {ruta}")
    else:
        procesar_todas()
