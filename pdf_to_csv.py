import sys
import argparse
import logging
import csv
from pathlib import Path
import pdfplumber
from config import EXCEL_HEADERS

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("pdf_to_csv.log")],
)
logger = logging.getLogger(__name__)

DATASET_DIR = Path("dataset")
DATASET_CSV = DATASET_DIR / "dataset.csv"
DOUBLONS_CSV = DATASET_DIR / "doublons.csv"


def ensure_csv_exists(csv_path):
    if not csv_path.exists():
        with open(csv_path, mode="w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=EXCEL_HEADERS)
            writer.writeheader()


def extract_data_from_pdf(pdf_path):
    """
    Extrait les champs EXCEL_HEADERS d'un PDF selon la logique robuste de pv_autofill.py. Met COUPON à 0.
    Retourne un dict ou None si erreur.
    """
    import re
    data = {key: "" for key in EXCEL_HEADERS}
    data["COUPON"] = 0
    pdf = None
    try:
        pdf = pdfplumber.open(pdf_path)
        if not pdf.pages:
            raise ValueError("PDF vide")
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        # Tronquer si besoin
        if "info@gta-Nomayos.cm" in text:
            text = text.split("info@gta-Nomayos.cm")[0]
        lines = text.split("\n")
        is_rejected = False
        # ACCEPTE/REFUS status (pour C/CV)
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
        # pht
        for line in lines:
            if "Montant payé HT" in line:
                parts = line.split(":")
                if len(parts) > 2:
                    amount = parts[2].replace("FCFA", "").replace(" ", "").strip()
                    data["pht"] = amount
                    break
        # PTTC
        for line in lines:
            if "Montant payé TTC" in line:
                parts = line.split(":")
                if len(parts) > 2:
                    amount = parts[2].replace("FCFA", "").replace(" ", "").strip()
                    data["PTTC"] = amount
                    break
        # TVA
        try:
            if data["pht"] and data["PTTC"]:
                data["TVA"] = str(int(data["PTTC"]) - int(data["pht"]))
        except (ValueError, TypeError):
            data["TVA"] = ""
        # Vérification finale
        for key in EXCEL_HEADERS:
            if key != "COUPON" and not data[key]:
                raise ValueError(f"Champ manquant: {key}")
        return data
    except Exception as e:
        logger.error(f"Erreur extraction {pdf_path}: {e}")
        return None
    finally:
        if pdf:
            pdf.close()


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
    with open(csv_path, mode="a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXCEL_HEADERS)
        writer.writerow(row)


def process_pdf(pdf_path):
    data = extract_data_from_pdf(pdf_path)
    if data is None:
        return
    n_pv = data["N° PV"]
    if pv_exists(n_pv, DATASET_CSV):
        logger.warning(f"Doublon détecté: {n_pv} dans {pdf_path}")
        append_row_to_csv(data, DOUBLONS_CSV)
    else:
        append_row_to_csv(data, DATASET_CSV)
        logger.info(f"Ajouté: {n_pv} depuis {pdf_path}")


def process_folder(folder_path):
    pdf_files = list(Path(folder_path).rglob("*.pdf"))
    logger.info(f"{len(pdf_files)} PDF trouvés dans {folder_path}")
    for pdf_path in pdf_files:
        process_pdf(pdf_path)


def main():
    parser = argparse.ArgumentParser(description="Extraction PV PDF vers dataset CSV pour IA.")
    parser.add_argument("--pdf", type=str, help="Chemin d'un fichier PDF à traiter")
    parser.add_argument("--folder", type=str, help="Chemin d'un dossier contenant des PDF")
    args = parser.parse_args()

    DATASET_DIR.mkdir(exist_ok=True)
    ensure_csv_exists(DATASET_CSV)
    ensure_csv_exists(DOUBLONS_CSV)

    if args.pdf:
        process_pdf(args.pdf)
    elif args.folder:
        process_folder(args.folder)
    else:
        print("Spécifiez --pdf <fichier> ou --folder <dossier>")
        sys.exit(1)

if __name__ == "__main__":
    main() 