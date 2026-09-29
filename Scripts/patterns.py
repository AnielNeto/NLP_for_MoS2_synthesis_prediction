"""
KEYWORDS e PATTERNS para select_periods (filtro de períodos de abstracts sobre MoS2).
 
- KEYWORDS: comparação por substring, em minúsculas (também cobre plurais e sufixos).
- PATTERNS: REGEX aplicados com re.IGNORECASE; (?-i:...) reativa a distinção de caixa
  (siglas e símbolos químicos).
"""
 
NUM = r"\d+(?:\.\d+)?"
DASH = r"[-–−]"   # hífen, en dash e sinal de menos unicode
VAC_ATOM = r"(?:sul(?:f|ph)ur\b|molybdenum\b|(?-i:S|Mo)\b)"
 
# ---------------------------------------------------------------- KEYWORDS
KEYWORDS = [
    # 1. Métodos de síntese
    "hydrothermal", "solvothermal",
    "autoclave method", "autoclave synthesis",
    "mechanical exfoliation",              # cobre "micromechanical exfoliation"
    "sticky tape", "scotch tape", "adhesive tape",
    "ball milling", "ball-milling",
    "chemical exfoliation", "solvent-based exfoliation",
    "intercalation exfoliation",           # cobre "ion-intercalation exfoliation"
    "electrochemical exfoliation",
    "chemical vapor deposition", "chemical vapour deposition",
    "microwave-driven exfoliation", "microwave exfoliation",
    "exfoliation through microwave",
    "liquid phase exfoliation", "liquid-phase exfoliation",
    "exfoliation in liquid phase",
    "cryo-mediated exfoliation",
    "bottom-up", "bottom up", "top-down", "top down",
 
    # 2. Modificações pós-síntese
    "heterojunction", "heterointerface",
    "support", "substrate", "scaffold",
    "phase adjustment", "phase regulation",
    "defect engineering", "strain engineering",
 
    # 3. Qualidades morfológicas
    "bulk synthesis",
    "multilayer", "monolayer", "monosheet", "bilayer",
    "ribbon", "nanoflower", "nanoflake", "nanoparticle", "nanotube",
    "quantum dot",
 
    # 4. Aplicações
    "hydrogen evolution reaction",
    "oxygen evolution reaction",
    "nitrogen reduction reaction",
    "carbon oxide reduction reaction", "carbon monoxide reduction reaction",
    "carbon dioxide reduction reaction",
    "air pollution treatment", "air pollution degradation",
    "aqueous pollution treatment", "aqueous pollution degradation",
    "water pollution treatment", "water pollution degradation",
    "treatment of air pollutant", "degradation of air pollutant",
    "treatment of aqueous pollutant", "degradation of aqueous pollutant",
    "treatment of water pollutant", "degradation of water pollutant",
    "wastewater",
    "removal of organic pollutant",
    "organic pollutants removal", "organic pollutant removal",
    "electrocatal", "photocatal",
]
 
# ---------------------------------------------------------------- DOPANTES
# Cada placeholder: (nomes, símbolos). Lantanídeos, actinídeos, metais
# pós-transição e gases nobres ficam de fora.
DOPANTS = {
    "alcalinos_alcalinoterrosos": (
        ["lithium", "sodium", "potassium", "rubidium", "cesium", "caesium", "francium",
         "beryllium", "magnesium", "calcium", "strontium", "barium", "radium"],
        ["Li", "Na", "K", "Rb", "Cs", "Fr", "Be", "Mg", "Ca", "Sr", "Ba", "Ra"]),
    "metais_transicao": (
        ["scandium", "titanium", "vanadium", "chromium", "manganese", "iron", "cobalt",
         "nickel", "copper", "zinc", "yttrium", "zirconium", "niobium", "molybdenum",
         "technetium", "ruthenium", "rhodium", "palladium", "silver", "cadmium",
         "hafnium", "tantalum", "tungsten", "rhenium", "osmium", "iridium", "platinum",
         "gold", "mercury"],
        ["Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Y", "Zr", "Nb", "Mo",
         "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt",
         "Au", "Hg"]),
    "ametais": (
        ["hydrogen", "carbon", "nitrogen", "oxygen", "phosphorus", "sulfur", "sulphur",
         "selenium", "fluorine", "chlorine", "bromine", "iodine"],
        ["H", "C", "N", "O", "P", "S", "Se", "F", "Cl", "Br", "I"]),
    "semimetais": (
        ["boron", "silicon", "germanium", "arsenic", "antimony", "tellurium"],
        ["B", "Si", "Ge", "As", "Sb", "Te"]),
}
 
 
def dopant_patterns(names, symbols):
    """Gera padrões '[Z]-doped' e 'doped with [Z]'. Símbolos são case-sensitive."""
    el = rf"(?:{'|'.join(names)}|(?-i:{'|'.join(symbols)}))"
    return [
        rf"\b{el}[\s-]dop(?:ed|ing)\b",
        rf"\bdop(?:ed|ing)\s+with\s+(?:the\s+)?{el}\b",
    ]
 
 
# ---------------------------------------------------------------- PATTERNS
PATTERNS = [
    r"\bthermal\s+(?:synthesis|treatment)",    # \b exclui hydro-/solvothermal
    r"(?-i:\b(?:SA)?CVD\b)",
    r"(?-i:\bLPE\b)",
    r"\bdop(?:ing|ed)\b",
    rf"\b{VAC_ATOM}[\s-]vacanc(?:y|ies)",
    rf"\bvacanc(?:y|ies)\s+of\s+{VAC_ATOM}",
    r"\b(?:metal|(?-i:Mo))[\s-]cluster(?:s|ization|ing)?",
    r"\bload(?:ed)?\s+on\b",
    r"(?<!MoS2)(?<!MoS₂)-based\b",             # "-based", exceto "MoS2-based"
    r"\bfew[\s-]+(?:layer(?:s|ed)?|sheets?)",
    rf"\b{NUM}[\s-]?layers?\b",
    rf"\b{NUM}\s*[A-Za-zμÅ]+\s+(?:thickness|depth)\b",
    rf"\b(?:thickness|depth)\s+of\s+{NUM}\s*[A-Za-zμÅ]+",
    r"\bsingle[\s-]layer",
    # "double layer" (exceto capacitância); "bilayer" está em KEYWORDS
    r"(?<!electrical\s)(?<!electric\s)\bdouble[\s-]layer(?![\s-]*capacit)",
    r"\btwo[\s-]layers?\b",
    r"(?-i:\bHER\b)",
    r"(?-i:\bOER\b)",
    r"(?-i:\bNRR\b)",
    r"(?-i:\bCORR\b)",
    r"(?-i:\bCO[2₂]RR\b)",
    # Tafel
    rf"\b{NUM}\s*mV(?:\s*[/.]\s*|\s+)dec(?:ade)?(?![a-z])"
    rf"(?:\s*{DASH}\s*1|\s*\(\s*{DASH}\s*1\s*\))?",
    # Densidade de corrente
    rf"\b{NUM}\s*mA(?:\s*[/.]\s*|\s+)cm"
    rf"(?:\s*{DASH}\s*2|\s*\(\s*{DASH}?\s*2\s*\)|\s*[²2])",
    # Sobrepotencial: "η = 150 mV", "η10 = 150 mV", "η_10 = 150 mV", "η₁₀ = 150 mV"
    rf"η\s*_?\s*(?:\d+|[₀-₉]+)?\s*=\s*{NUM}\s*mV",
    rf"\boverpotentials?\s+of\s+{NUM}\s*mV",
    r"\bmV\s+overpotential",
    # Área ativa
    rf"\bactive\s+area\s+of\s+{NUM}",
    NUM + r"\s*\S{1,8}\s+(?:of\s+)?active\s+area",
]
 
# Dopantes: um par de padrões por grupo de elementos, anexado à mesma lista
for _nomes, _simbolos in DOPANTS.values():
    PATTERNS.extend(dopant_patterns(_nomes, _simbolos))