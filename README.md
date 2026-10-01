# 🍇 Enology Data Toolkit & Winery Copilot (Copiloto Enológico)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)
[![CustomTkinter](https://img.shields.io/badge/Desktop-CustomTkinter-blue.svg)](https://github.com/TomSchimansky/CustomTkinter)

> **Autonomous enological calculation, nutrient optimization (YAN/FAN), and batch cellar management toolkit designed for modern wineries.**

---

## 👨‍🔬 Author & Domain Background
- **Lead Developer & Viticulturist:** **Cristián González Huenchún**
- **Title:** Agronomist Engineer & Master's Student in Enology & Viticulture — *Universidad de Chile*.
- **Cellar Experience:** Assistant Winemaker at *Viña VIK* (Vintage 2026), Cellar Hand at *Viña El Principal* (Vintage 2025). 2nd Place in *VIK Wine Lab 3*.
- **Contact:** [LinkedIn](https://www.linkedin.com/in/cristian-ignacio-gonzalez-huenchun) · Email: `cristian.gonzalez.h@ug.uchile.cl`

---

## 🚀 Key Features

### 1. 🧪 Active Sulfur Dioxide ($SO_2$) Balancing
Calculates the precise amount of Potassium Metabisulfite ($K_2S_2O_5$) needed based on must or wine volume in hectoliters (hL) and desired free $SO_2$ targets:
$$\text{Metabisulfite (g)} = \frac{(\text{Target } SO_2 - \text{Actual } SO_2) \times \text{Volume (hL)}}{5}$$

### 2. 🍋 Tartaric Acid & Total Acidity Correction
Determines exact acid supplementation to safeguard microbial stability, lower pH, and enhance aging longevity:
$$\text{Tartaric Acid (kg)} = \frac{(\text{Target Acidity} - \text{Actual Acidity}) \times \text{Volume (L)}}{1000}$$

### 3. 🧬 Yeast Assimilable Nitrogen (YAN / FAN) Fermentation Rescue
- Evaluates nutritional deficits based on must initial density and potential alcohol (°Brix / % vol).
- Allocates balanced dosing between **Organic Yeast Derivatives (FAN / Amino acids)** and **DAP (Diammonium Phosphate)**.
- Provides critical stage alerts (e.g., **1/3 Fermentation Phase / Density 1.050 - 1.025**) to prevent stuck fermentations and volatile sulfur defect synthesis ($H_2S$ reduction).

### 4. 🖥️ Dual Interactive User Interfaces
- **Desktop Application (InfoStat / RStudio style):** Native Windows dark-mode software powered by `CustomTkinter` for cellar technicians.
- **Web Dashboard (Streamlit):** Reactive web interface with tank KPIs, live dosage simulator, and **QR Code Generator for barrel traceability**.

---

## 📦 Installation & Quickstart

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/enology-data-toolkit.git
cd enology-data-toolkit

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch Desktop GUI (InfoStat style)
python copiloto_desktop.py

# 4. Or launch Web Dashboard
streamlit run copiloto_web.py
```

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
