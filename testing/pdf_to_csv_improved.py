#!/usr/bin/env python3
"""
Version améliorée de pdf_to_csv.py qui gère différents types de documents :
- PV de contrôle technique (avec montants)
- Contre-visites (sans montants)
- Factures (format différent)
"""

import argparse
import logging
import csv
from pathlib import Path
import pdfplumber
import re
from config import EXCEL_HEADERS

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("pdf_to_csv_improved.log")],
)
logger = logging.getLogger(__name__)

DATASET_DIR = Path("dataset")
DATASET_CSV = DATASET_DIR / "dataset.csv"
DOUBLONS_CSV = DATASET_DIR / "doublons.csv"
FACTURES_CSV = DATASET_DIR / "factures.csv"


def ensure_csv_exists(csv_path, headers):
    if not csv_path.exists():
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()


def extract_pv_data(pdf_path):
    """
    Extrait les données d'un PV de contrôle technique.
    """
    data = {key: "" for key in EXCEL_HEADERS}
    data["COUPON"] = 0

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                raise ValueError("PDF vide")

            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            if "info@gta-Nomayos.cm" in text:
                text = text.split("info@gta-Nomayos.cm")[0]

            lines = text.split("\n")
            is_rejected = False

            # ACCEPTE/REFUS status
            if "ACCEPTE / ACCEPTED" in text:
                data["C/CV"] = "C"
            elif "CONTRE-VISITE" in text or "REFUSE / REJECTED" in text:
                data["C/CV"] = "CV"
                is_rejected = True

            # N° PV
            for line in lines:
                if "N° PV" in line and "SHEET" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        data["N° PV"] = parts[1].split("Type")[0].strip()
                        break

            # DATE
            for line in lines:
                if "Date du contrôle" in line and "Date of control" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        date_part = parts[1].split("Catégorie")[0].strip()
                        date_match = re.search(r"(\d{2}/\d{2}/\d{4})", date_part)
                        if date_match:
                            data["DATE"] = date_match.group(1)
                        break

            # DATE P.V
            if is_rejected:
                for line in lines:
                    if "JUSQU'AU" in line and "UNTIL" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            date_part = parts[1].strip()
                            date_match = re.search(r"(\d{2}/\d{2}/\d{4})", date_part)
                            if date_match:
                                data["DATE P.V"] = date_match.group(1)
                                break
            else:
                for line in lines:
                    if "PROCHAINE VISITE" in line and "NEXT VISIT" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            date_part = parts[1].split("Type")[0].strip()
                            date_match = re.search(r"(\d{2}/\d{2}/\d{4})", date_part)
                            if date_match:
                                data["DATE P.V"] = date_match.group(1)
                            break

            # IMMATRI
            for line in lines:
                if "Immatriculation" in line and "reg" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        data["IMMATRI"] = parts[1].split("Client")[0].strip()
                        break

            # DESCRIPTIONS
            for line in lines:
                if "Client" in line and "Customer" in line:
                    parts = line.split(":")
                    if len(parts) > 2:
                        data["DESCRIPTIONS"] = parts[2].strip()
                        break

            # CAT
            for line in lines:
                if "Catégorie" in line and "Category" in line:
                    parts = line.split(":")
                    if len(parts) > 3:
                        string_to_strip = parts[3].strip()
                        data["CAT"] = string_to_strip.split(" ")[0]
                        break

            # CONTACT
            for line in lines:
                if "Téléphone" in line and "Phone" in line:
                    parts = line.split(":")
                    if len(parts) > 2:
                        data["CONTACT"] = parts[2].strip()
                        break

            # pht (seulement si pas contre-visite)
            if not is_rejected:
                for line in lines:
                    if "Montant payé HT" in line:
                        parts = line.split(":")
                        if len(parts) > 2:
                            amount = (
                                parts[2].replace("FCFA", "").replace(" ", "").strip()
                            )
                            data["pht"] = amount
                            break

            # PTTC (seulement si pas contre-visite)
            if not is_rejected:
                for line in lines:
                    if "Montant payé TTC" in line:
                        parts = line.split(":")
                        if len(parts) > 2:
                            amount = (
                                parts[2].replace("FCFA", "").replace(" ", "").strip()
                            )
                            data["PTTC"] = amount
                            break

            # TVA
            try:
                if data["pht"] and data["PTTC"]:
                    data["TVA"] = str(int(data["PTTC"]) - int(data["pht"]))
            except (ValueError, TypeError):
                data["TVA"] = ""

                # Vérification finale (plus souple pour contre-visites)
            missing_fields = []
            for key in EXCEL_HEADERS:
                if key != "COUPON" and not data[key]:
                    if is_rejected and key in ["pht", "PTTC", "TVA"]:
                        # Contre-visites peuvent avoir des montants vides
                        continue
                    missing_fields.append(key)

            if missing_fields:
                raise ValueError(f"Champs manquants: {', '.join(missing_fields)}")

            # Pour les contre-visites, mettre des valeurs par défaut pour les montants
            if is_rejected:
                if not data["pht"]:
                    data["pht"] = "0"
                if not data["PTTC"]:
                    data["PTTC"] = "0"
                if not data["TVA"]:
                    data["TVA"] = "0"

            return data

    except Exception as e:
        logger.error(f"Erreur extraction PV {pdf_path}: {e}")
        return None


def extract_facture_data(pdf_path):
    """
    Extrait les données d'une facture.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                raise ValueError("PDF vide")

            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            lines = text.split("\n")

            data = {
                "file": str(pdf_path),
                "date": "",
                "reference": "",
                "description": "",
                "montant_ht": "",
                "montant_ttc": "",
                "tva": "",
            }

            # Date
            for line in lines:
                if "Date:" in line:
                    date_match = re.search(r"(\d{2}/\d{2}/\d{4})", line)
                    if date_match:
                        data["date"] = date_match.group(1)
                        break

            # Référence
            for line in lines:
                if "No/Réf.:" in line:
                    ref_match = re.search(r"No/Réf\.:\s*(\S+)", line)
                    if ref_match:
                        data["reference"] = ref_match.group(1)
                        break

            # Description
            for line in lines:
                if "Désignation" in line:
                    # Prendre la ligne suivante comme description
                    continue
                elif data["reference"] and not data["description"]:
                    data["description"] = line.strip()
                    break

            # Montant HT
            for line in lines:
                if "Montant Hors Taxe" in line:
                    amount_match = re.search(r"(\d+)\s*FCFA", line)
                    if amount_match:
                        data["montant_ht"] = amount_match.group(1)
                        break

            # Montant TTC
            for line in lines:
                if "Montant TTC" in line:
                    amount_match = re.search(r"(\d+)\s*FCFA", line)
                    if amount_match:
                        data["montant_ttc"] = amount_match.group(1)
                        break

            # TVA
            for line in lines:
                if "TVA" in line and "FCFA" in line:
                    tva_match = re.search(r"(\d+)\s*FCFA", line)
                    if tva_match:
                        data["tva"] = tva_match.group(1)
                        break

            return data

    except Exception as e:
        logger.error(f"Erreur extraction facture {pdf_path}: {e}")
        return None


def detect_document_type(pdf_path):
    """
    Détecte le type de document (PV, facture, contre-visite).
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)

            if "FACTURE" in str(pdf_path) or "Montant Hors Taxe" in text:
                return "FACTURE"
            elif "CONTRE-VISITE" in text or "CV" in str(pdf_path):
                return "CONTRE_VISITE"
            elif "N° PV" in text:
                return "PV"
            else:
                return "UNKNOWN"
    except:
        return "UNKNOWN"


def process_pdf(pdf_path):
    """
    Traite un PDF selon son type détecté.
    """
    doc_type = detect_document_type(pdf_path)

    if doc_type == "FACTURE":
        data = extract_facture_data(pdf_path)
        if data:
            # Sauvegarder dans un fichier séparé pour les factures
            ensure_csv_exists(
                FACTURES_CSV,
                [
                    "file",
                    "date",
                    "reference",
                    "description",
                    "montant_ht",
                    "montant_ttc",
                    "tva",
                ],
            )
            with open(FACTURES_CSV, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "file",
                        "date",
                        "reference",
                        "description",
                        "montant_ht",
                        "montant_ttc",
                        "tva",
                    ],
                )
                writer.writerow(data)
            logger.info(f"Facture traitée: {pdf_path}")
        return

    elif doc_type in ["PV", "CONTRE_VISITE"]:
        data = extract_pv_data(pdf_path)
        if data is None:
            return

        n_pv = data["N° PV"]
        if pv_exists(n_pv, DATASET_CSV):
            logger.warning(f"Doublon détecté: {n_pv} dans {pdf_path}")
            append_row_to_csv(data, DOUBLONS_CSV)
        else:
            append_row_to_csv(data, DATASET_CSV)
            logger.info(f"Ajouté: {n_pv} depuis {pdf_path}")

    else:
        logger.warning(f"Type de document non reconnu: {pdf_path}")


def pv_exists(n_pv, csv_path):
    if not csv_path.exists():
        return False
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("N° PV", "").strip() == n_pv.strip():
                return True
    return False


def append_row_to_csv(row, csv_path):
    with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXCEL_HEADERS)
        writer.writerow(row)


def process_folder(folder_path):
    pdf_files = list(Path(folder_path).rglob("*.pdf"))
    logger.info(f"{len(pdf_files)} PDF trouvés dans {folder_path}")

    stats = {"pv": 0, "factures": 0, "contre_visites": 0, "unknown": 0}

    for pdf_path in pdf_files:
        doc_type = detect_document_type(pdf_path)
        if doc_type == "PV":
            stats["pv"] += 1
        elif doc_type == "FACTURE":
            stats["factures"] += 1
        elif doc_type == "CONTRE_VISITE":
            stats["contre_visites"] += 1
        else:
            stats["unknown"] += 1

        process_pdf(pdf_path)

    logger.info(f"Statistiques: {stats}")


def main():
    parser = argparse.ArgumentParser(description="Extraction PDF vers CSV améliorée.")
    parser.add_argument("--pdf", type=str, help="Chemin d'un fichier PDF à traiter")
    parser.add_argument(
        "--folder", type=str, help="Chemin d'un dossier contenant des PDF"
    )
    args = parser.parse_args()

    DATASET_DIR.mkdir(exist_ok=True)
    ensure_csv_exists(DATASET_CSV, EXCEL_HEADERS)
    ensure_csv_exists(DOUBLONS_CSV, EXCEL_HEADERS)

    if args.pdf:
        process_pdf(args.pdf)
    elif args.folder:
        process_folder(args.folder)
    else:
        print("Utilisation: --pdf <fichier> ou --folder <dossier>")


if __name__ == "__main__":
    main()
