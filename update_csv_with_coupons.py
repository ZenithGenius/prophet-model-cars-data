#!/usr/bin/env python3
"""
Script pour mettre à jour le CSV avec les coupons extraits des fichiers Excel.
Prend en compte les fichiers avec plusieurs sheets.
"""

import pandas as pd
import re
from pathlib import Path


def extract_coupon_from_description(description):
    """Extrait le montant du coupon depuis la description contenant 'RED'"""
    if pd.isna(description):
        return 0

    description_str = str(description)
    # Chercher le pattern "RED" suivi d'un nombre
    red_match = re.search(r"RED\s+(\d+)", description_str, re.IGNORECASE)
    if red_match:
        return int(red_match.group(1))
    return 0


def process_excel_file(file_path):
    """Traite un fichier Excel et extrait les données de coupons"""
    coupons_data = []

    try:
        # Lire toutes les sheets du fichier Excel
        excel_file = pd.ExcelFile(file_path)
        sheets = excel_file.sheet_names

        print(f"📁 Traitement de {file_path.name} ({len(sheets)} sheets)")

        for sheet_name in sheets:
            print(f"  📄 Sheet: {sheet_name}")

            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # Vérifier si c'est un fichier de 2025 (avec colonne COUPON)
                if "COUPON" in df.columns:
                    print("    ✅ Format 2025 détecté (colonne COUPON)")

                    # Extraire les données avec colonne COUPON
                    for idx, row in df.iterrows():
                        if pd.notna(row.get("DATE")) and pd.notna(row.get("N° PV")):
                            date = pd.to_datetime(row["DATE"]).strftime("%Y-%m-%d")
                            pv_number = str(row["N° PV"]).strip()
                            coupon = (
                                float(row["COUPON"]) if pd.notna(row["COUPON"]) else 0
                            )
                            pttc_original = (
                                float(row["PTTC"]) if pd.notna(row["PTTC"]) else 0
                            )

                            coupons_data.append(
                                {
                                    "date": date,
                                    "pv_number": pv_number,
                                    "coupon": coupon,
                                    "pttc_original": pttc_original,
                                    "pttc_final": pttc_original - coupon,
                                    "source": f"{file_path.name} - {sheet_name}",
                                }
                            )

                # Vérifier si c'est un fichier de 2023-2024 (avec "RED" dans DESCRIPTIONS)
                elif "DESCRIPTIONS" in df.columns:
                    print("    ✅ Format 2023-2024 détecté (RED dans DESCRIPTIONS)")

                    # Chercher les colonnes DATE et N° PV
                    date_col = None
                    pv_col = None
                    pttc_col = None

                    for col in df.columns:
                        col_str = str(col).lower()
                        if "date" in col_str and "pv" not in col_str:
                            date_col = col
                        elif "pv" in col_str or "n°" in col_str:
                            pv_col = col
                        elif "pttc" in col_str:
                            pttc_col = col

                    if date_col and pv_col:
                        for idx, row in df.iterrows():
                            if pd.notna(row.get(date_col)) and pd.notna(
                                row.get(pv_col)
                            ):
                                try:
                                    date = pd.to_datetime(row[date_col]).strftime(
                                        "%Y-%m-%d"
                                    )
                                    pv_number = str(row[pv_col]).strip()
                                    description = row.get("DESCRIPTIONS", "")
                                    coupon = extract_coupon_from_description(
                                        description
                                    )
                                    pttc_original = (
                                        float(row[pttc_col])
                                        if pd.notna(row.get(pttc_col))
                                        else 0
                                    )

                                    if coupon > 0:  # Seulement si un coupon est trouvé
                                        coupons_data.append(
                                            {
                                                "date": date,
                                                "pv_number": pv_number,
                                                "coupon": coupon,
                                                "pttc_original": pttc_original,
                                                "pttc_final": pttc_original - coupon,
                                                "source": f"{file_path.name} - {sheet_name}",
                                            }
                                        )
                                except Exception as e:
                                    print(f"    ⚠️ Erreur ligne {idx}: {e}")
                                    continue
                    else:
                        print("    ⚠️ Colonnes DATE ou N° PV non trouvées")

                else:
                    print("    ⚠️ Format non reconnu")

            except Exception as e:
                print(f"    ❌ Erreur sheet {sheet_name}: {e}")
                continue

    except Exception as e:
        print(f"❌ Erreur fichier {file_path.name}: {e}")

    return coupons_data


def update_csv_with_coupons():
    """Met à jour le CSV avec les coupons extraits des fichiers Excel"""

    # Charger le CSV existant
    csv_path = Path("dataset/dataset.csv")
    if not csv_path.exists():
        print("❌ Fichier CSV non trouvé: dataset/dataset.csv")
        return

    print("📊 Chargement du CSV existant...")
    df_csv = pd.read_csv(csv_path)
    print(f"📊 CSV chargé: {len(df_csv)} lignes")

    # Traiter tous les fichiers Excel
    excel_dir = Path("excel_files")
    if not excel_dir.exists():
        print("❌ Dossier excel_files non trouvé")
        return

    excel_files = list(excel_dir.glob("*.xlsx")) + list(excel_dir.glob("*.xls"))

    if not excel_files:
        print("❌ Aucun fichier Excel trouvé")
        return

    print(f"📁 Traitement de {len(excel_files)} fichiers Excel...")

    all_coupons_data = []

    for file_path in sorted(excel_files):
        coupons_data = process_excel_file(file_path)
        all_coupons_data.extend(coupons_data)

    if not all_coupons_data:
        print("❌ Aucune donnée de coupon trouvée")
        return

    # Créer un DataFrame des coupons
    df_coupons = pd.DataFrame(all_coupons_data)
    print(f"💰 {len(df_coupons)} entrées de coupons trouvées")

    # Afficher un résumé des coupons
    print("\n📊 Résumé des coupons trouvés:")
    coupon_summary = df_coupons.groupby("coupon").size().sort_index()
    for coupon, count in coupon_summary.items():
        print(f"  💰 Coupon {coupon}: {count} entrées")

    # Mettre à jour le CSV
    print("\n🔄 Mise à jour du CSV...")

    # Créer une colonne de correspondance dans le CSV
    df_csv['pv_key'] = df_csv['N° PV'].astype(str).str.strip()
    df_coupons['pv_key'] = df_coupons['pv_number'].astype(str).str.strip()

    # Initialiser la colonne COUPON si elle n'existe pas
    if 'COUPON' not in df_csv.columns:
        df_csv['COUPON'] = 0

    # Compter les correspondances
    matched_count = 0
    updated_count = 0
    exemples = []

    for idx, row in df_csv.iterrows():
        key = row['pv_key']
        matching_coupons = df_coupons[df_coupons['pv_key'] == key]

        if len(matching_coupons) > 0:
            matched_count += 1
            coupon_value = matching_coupons.iloc[0]['coupon']

            if coupon_value > 0:
                df_csv.at[idx, 'COUPON'] = coupon_value
                updated_count += 1
                if len(exemples) < 5:
                    exemples.append((row['N° PV'], coupon_value))
                print(f"  ✅ Ligne {idx}: Coupon {coupon_value} ajouté (PV: {row['N° PV']})")

    # Supprimer la colonne temporaire
    df_csv = df_csv.drop('pv_key', axis=1)

    # Recalcul automatique de la colonne PTTC
    print("\n🔢 Recalcul de la colonne PTTC...")
    if 'PTTC' in df_csv.columns:
        for idx, row in df_csv.iterrows():
            try:
                pttc = float(row['PTTC']) if pd.notna(row['PTTC']) else 0
                coupon = float(row['COUPON']) if pd.notna(row['COUPON']) else 0
                new_pttc = max(pttc - coupon, 0) if coupon > 0 else pttc
                df_csv.at[idx, 'PTTC'] = new_pttc
            except Exception as e:
                print(f"  ⚠️ Erreur recalcul PTTC ligne {idx}: {e}")
    else:
        print("  ⚠️ Colonne PTTC absente du CSV")

    # Correction des coupons non extraits (analyse DESCRIPTIONS du CSV)
    print("\n🔍 Correction des coupons non extraits (analyse DESCRIPTIONS du CSV)...")
    corrections = 0
    for idx, row in df_csv[df_csv['COUPON'] == 0].iterrows():
        description = row.get('DESCRIPTIONS', '')
        coupon = extract_coupon_from_description(description)
        if coupon > 0:
            df_csv.at[idx, 'COUPON'] = coupon
            # Recalcul PTTC
            try:
                pttc = float(row['PTTC']) if pd.notna(row['PTTC']) else 0
                new_pttc = max(pttc - coupon, 0)
                df_csv.at[idx, 'PTTC'] = new_pttc
            except Exception as e:
                print(f"  ⚠️ Erreur recalcul PTTC (correction) ligne {idx}: {e}")
            corrections += 1
            if corrections <= 5:
                print(f"  🛠️ Correction ligne {idx}: Coupon {coupon} extrait de DESCRIPTIONS")

    print(f"\n✅ Corrections appliquées: {corrections}")

    # Sauvegarder le CSV mis à jour
    output_path = csv_path
    df_csv.to_csv(output_path, index=False)
    print(f"💾 Fichier sauvegardé: {output_path}")

    # Afficher quelques exemples de corrections
    if corrections > 0:
        print(f"\n📝 Exemples de corrections:")
        for idx, row in df_csv[df_csv['COUPON'] > 0].head(5).iterrows():
            print(f"  📄 PV {row['N° PV']} ({row['DATE']}): Coupon {row['COUPON']} | PTTC: {row['PTTC']}")


if __name__ == "__main__":
    update_csv_with_coupons()
 