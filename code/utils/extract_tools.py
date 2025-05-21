import json
import os
from tqdm import tqdm

def extract_patient_condition(data):
    patient_info = data["Patient Information"]
    disease_info = data["Disease Information"]
    exam_results = data["Examination Results"]
    treatment_plan = data["Treatment Plan"]
    patient_condition = (
        "Patient Information:\n"
        f"Name: {patient_info['Name']}\n"
        f"Age: {patient_info['Age']}\n"
        f"Gender: {patient_info['Gender']}\n"
        f"Medical History: {patient_info['Medical History']}\n"
        "\nDisease Information:\n"
        f"Disease: {disease_info['Disease']}\n"
        f"Severity Level: {disease_info['Severity Level']}\n"
        f"Symptoms: {disease_info['Symptoms']}\n"
        f"Duration: {disease_info['Duration']}\n"
        f"Curability: {disease_info['Curability']}\n"
        "\nExamination Results:\n"
    )

    for test_category, test_results in exam_results.items():
        if isinstance(test_results, dict): 
            patient_condition += f"{test_category}:\n"
            for test_name, result in test_results.items():
                patient_condition += f"{test_name}: {result}\n"
        else: 
            patient_condition += f"{test_category}:\n{test_results}\n"

    patient_condition += (
        "\nTreatment Plan:\n"
        f"{treatment_plan}"
    )
    
    return patient_condition


def extract_preknow_condition(data):
    patient_info = data["Patient Information"]
    disease_info = data["Disease Information"]
    preknow_condition = (
        "Patient Information:\n"
        f"Name: {patient_info['Name']}\n"
        f"Age: {patient_info['Age']}\n"
        f"Gender: {patient_info['Gender']}\n"
        "\nDisease Information:\n"
        f"Symptoms: {disease_info['Symptoms']}\n"
        f"Duration: {disease_info['Duration']}"
    )
    return preknow_condition


def extract_bigfive_traits(data):
    bigfive = data.get("BigFive", {})
    bigfive_strings = []

    for trait, details in bigfive.items():
        description = details.get("Description", "").strip()
        trait_str = f"{trait}: {description}"
        bigfive_strings.append(trait_str)

    return " ".join(bigfive_strings)

def extract_bigfive_scores(data):
    bigfive = data.get("BigFive", {})
    scores = {}

    for trait, details in bigfive.items():
        score = details.get("Score", "").strip()
        scores[trait] = score

    return scores


def extract_education_category(data):
    edu_profile = data.get("EducationProfile", {})
    return edu_profile.get("Education Category", "").strip()

def extract_simulated_behaviors(data):
    edu_profile = data.get("EducationProfile", {})
    return edu_profile.get("Simulated Behaviors", "").strip()



