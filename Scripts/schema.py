from typing import Optional, List
from pydantic import BaseModel
from enum import Enum

class SynthesisMethod(str, Enum):

    autoclave_method = "autoclave_method"
    hydrothermal = "hydrothermal"
    solvothermal = "solvothermal"
    mechanical_exfoliation = "mechanical_exfoliation"
    sticky_tape = "sticky_tape" 
    ball_milling = "ball_milling"
    chemical_exfoliation = "chemical_exfoliation"
    intercalation_exfoliation = "intercalation_exfoliation"
    electrochemical_exfoliation = "electrochemical_exfoliation"
    chemical_vapor_deposition = "chemical_vapor_deposition"
    microwave_driven_exfoliation = "microwave_driven_exfoliation"
    liquid_phase_exfoliation = "liquid_phase_exfoliation"
    thermal_synthesis = "thermal_synthesis"

class SynthesisDirection(str, Enum):

    bottom_up = "bottom_up"
    top_down = "top_down"

class PostSynthesisModification(str, Enum):

    heteroatom_doping = "heteroatom_doping"
    heterojunction = "heterojunction"
    support = "support"
    phase_adjustment = "phase_adjustment"
    sulfur_vacancy = "sulfur_vacancy"
    molybdenum_vacancy = "molybdenum_vacancy"
    metal_clusters = "metal_clusters"

class SynthesisEngineering(str, Enum):

    defect_engineering = "defect_engineering"
    strain_engineering = "strain_engineering"

class NumSheets(str, Enum):

    few_layer = "few_layer"
    monolayer = "monolayer"
    double_layer = "double_layer"

class StructureFormat(str, Enum):

    ribbon = "ribbon"
    nanoflower = "nanoflower"
    nanoflake = "nanoflake"
    nanoparticle = "nanoparticle"
    nanotube = "nanotube"
    quantum_dot = "quantum_dot"

class SpecificApplication(str, Enum):

    her = "HER"
    oer = "OER"
    nrr = "NRR"
    co2rr = "CO2RR"
    pollutants = "pollutants"

class GeneralApplication(str, Enum):

    electrocatalysis = "electrocatalysis"
    photocatalysis = "photocatalysis"

class AbstractExtraction(BaseModel):

    synthesis_methods: Optional[List[SynthesisMethod]] = None
    synthesis_direction: Optional[List[SynthesisDirection]] = None
    post_synthesis_modifications: Optional[List[PostSynthesisModification]] = None
    synthesis_engineering: Optional[List[SynthesisEngineering]] = None
    num_sheets: Optional[List[NumSheets]] = None
    structure_format: Optional[List[StructureFormat]] = None
    specific_applications: Optional[List[SpecificApplication]] = None
    general_applications: Optional[List[GeneralApplication]] = None

class ExperimentSchema(BaseModel):
    experiments: List[AbstractExtraction]
