#!/usr/bin/env python3
"""
Script pour analyser la structure des fichiers Excel dans le dossier excel_files
et comprendre la gestion des coupons.
"""

import pandas as pd
from pathlib import Path


def analyze_excel_files():
    """Analyse tous les fichiers Excel dans le dossier excel_files"""
    excel_dir = Path("excel_files")

    if not excel_dir.exists():
        print("❌ Dossier excel_files non trouvé")
        return

    excel_files = list(excel_dir.glob("*.xlsx")) + list(excel_dir.glob("*.xls"))

    if not excel_files:
        print("❌ Aucun fichier Excel trouvé dans excel_files/")
        return

    print(f"📊 Analyse de {len(excel_files)} fichiers Excel...\n")

    for file_path in sorted(excel_files):
        print(f"📁 {file_path.name}")
        print("=" * 50)

        try:
            # Lire toutes les sheets du fichier Excel
            excel_file = pd.ExcelFile(file_path)
            sheets = excel_file.sheet_names

            print(f"📋 Nombre de sheets: {len(sheets)}")
            print(f"📋 Noms des sheets: {', '.join(sheets)}")
            print()

            for sheet_name in sheets:
                print(f"  📄 Sheet: '{sheet_name}'")
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                print(
                    f"    📊 Dimensions: {df.shape[0]} lignes x {df.shape[1]} colonnes"
                )
                print(f"    📋 Colonnes: {list(df.columns)}")

                # Vérifier la présence de colonnes importantes
                has_date = any("date" in col.lower() for col in df.columns)
                has_pv = any(
                    "pv" in col.lower() or "n°" in col.lower() for col in df.columns
                )
                has_coupon = "COUPON" in df.columns
                has_descriptions = "DESCRIPTIONS" in df.columns
                has_pttc = "PTTC" in df.columns

                print(f"    ✅ Colonne DATE: {'Oui' if has_date else 'Non'}")
                print(f"    ✅ Colonne N° PV: {'Oui' if has_pv else 'Non'}")
                print(f"    ✅ Colonne COUPON: {'Oui' if has_coupon else 'Non'}")
                print(
                    f"    ✅ Colonne DESCRIPTIONS: {'Oui' if has_descriptions else 'Non'}"
                )
                print(f"    ✅ Colonne PTTC: {'Oui' if has_pttc else 'Non'}")

                # Analyser les coupons si la colonne existe
                if has_coupon:
                    coupon_values = df["COUPON"].dropna()
                    print(
                        f"    💰 Valeurs COUPON uniques: {sorted(coupon_values.unique())}"
                    )
                    print(f"    💰 Nombre de lignes avec coupon: {len(coupon_values)}")

                # Analyser les descriptions pour "RED"
                if has_descriptions:
                    red_count = (
                        df["DESCRIPTIONS"]
                        .str.contains("RED", case=False, na=False)
                        .sum()
                    )
                    print(f"    🔴 Lignes avec 'RED' dans DESCRIPTIONS: {red_count}")

                    if red_count > 0:
                        red_rows = df[
                            df["DESCRIPTIONS"].str.contains("RED", case=False, na=False)
                        ]
                        print(f"    🔴 Exemples de descriptions avec 'RED':")
                        for idx, row in red_rows.head(3).iterrows():
                            print(f"      - {row['DESCRIPTIONS']}")

                # Afficher quelques exemples de données
                print(f"    📝 Exemples de données (3 premières lignes):")
                for idx, row in df.head(3).iterrows():
                    row_data = {}
                    for col in df.columns:
                        if pd.notna(row[col]):
                            row_data[col] = str(row[col])[:50]  # Limiter la longueur
                    print(f"      Ligne {idx}: {row_data}")

                print()

        except Exception as e:
            print(f"❌ Erreur lors de l'analyse de {file_path.name}: {e}")
            print()

    print("✅ Analyse terminée")


if __name__ == "__main__":
    analyze_excel_files()
