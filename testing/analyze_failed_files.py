#!/usr/bin/env python3
"""
Script de diagnostic pour analyser les fichiers PDF qui ont échoué lors de l'extraction.
"""

import pdfplumber
import re
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_pdf_structure(pdf_path):
    """
    Analyse la structure d'un PDF pour comprendre pourquoi l'extraction a échoué.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return {"error": "PDF vide"}

            text = "\n".join(page.extract_text() or "" for page in pdf.pages)

            # Analyse des champs clés
            analysis = {
                "file": str(pdf_path),
                "has_date_control": "Date du contrôle" in text,
                "has_date_facture": "Date:" in text and "FACTURE" in str(pdf_path),
                "has_pv_number": "N° PV" in text,
                "has_montant_ht": "Montant payé HT" in text,
                "has_montant_ht_facture": "Montant Hors Taxe" in text,
                "has_montant_ttc": "Montant payé TTC" in text,
                "has_montant_ttc_facture": "Montant TTC" in text,
                "is_contre_visite": "CONTRE-VISITE" in text or "CV" in str(pdf_path),
                "is_facture": "FACTURE" in str(pdf_path),
                "text_preview": text[:500] + "..." if len(text) > 500 else text,
            }

            return analysis

    except Exception as e:
        return {"error": str(e)}


def main():
    # Fichiers qui ont échoué (basé sur les logs)
    failed_files = [
        "training_data/SU 008 AQ N 47153 RED 900 B.pdf",
        "training_data/FACTURE 1.pdf",
        "training_data/FACTURE 2.pdf",
        "training_data/FACTURE 3.pdf",
        "training_data/FACTURE 4.pdf",
        "training_data/FACTURE 5.pdf",
        "training_data/FACTURE 6.pdf",
        "training_data/FACTURE 7.pdf",
        "training_data/FACTURE 8.pdf",
        "training_data/FACTURE 9.pdf",
        "training_data/FACTURE 10.pdf",
        "training_data/FACTURE 11.pdf",
        "training_data/FACTURE 12.pdf",
        "training_data/CE 654 NZ Q 32984 D.pdf",
        "training_data/CE 063 KY Q 32738 D CV.pdf",
        "training_data/CE 639 II H 26335 CV C.pdf",
    ]

    print("=== ANALYSE DES FICHIERS ÉCHOUÉS ===\n")

    for file_path in failed_files:
        if Path(file_path).exists():
            print(f"\n--- {file_path} ---")
            analysis = analyze_pdf_structure(file_path)

            if "error" in analysis:
                print(f"ERREUR: {analysis['error']}")
                continue

            print(f"Type de document: {'FACTURE' if analysis['is_facture'] else 'PV'}")
            print(f"Contre-visite: {analysis['is_contre_visite']}")
            print(f"Date contrôle: {analysis['has_date_control']}")
            print(f"Date facture: {analysis['has_date_facture']}")
            print(f"N° PV: {analysis['has_pv_number']}")
            print(f"Montant HT (PV): {analysis['has_montant_ht']}")
            print(f"Montant HT (Facture): {analysis['has_montant_ht_facture']}")
            print(f"Montant TTC (PV): {analysis['has_montant_ttc']}")
            print(f"Montant TTC (Facture): {analysis['has_montant_ttc_facture']}")

            # Diagnostic du problème
            if analysis["is_facture"]:
                print("PROBLÈME: Document FACTURE - format différent des PV")
            elif analysis["is_contre_visite"] and not analysis["has_montant_ht"]:
                print("PROBLÈME: Contre-visite sans montants (normal)")
            elif not analysis["has_date_control"]:
                print("PROBLÈME: Date de contrôle manquante")
            elif not analysis["has_montant_ht"]:
                print("PROBLÈME: Montant HT manquant")

        else:
            print(f"\n--- {file_path} ---")
            print("FICHIER NON TROUVÉ")


if __name__ == "__main__":
    main()
