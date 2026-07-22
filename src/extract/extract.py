from pathlib import Path

import pandas as pd


def inspect_raw_csv_files() -> None:
	base_dir = Path(__file__).resolve().parents[2]
	raw_dir = base_dir / "data" / "raw"

	csv_files = sorted(raw_dir.glob("*.csv"))
	if not csv_files:
		print(f"Aucun fichier CSV trouvé dans {raw_dir}")
		return

	for csv_file in csv_files:
		df = pd.read_csv(csv_file)

		print(f"\nFichier: {csv_file.name}")
		print(f"Nombre de lignes: {df.shape[0]}")
		print(f"Nombre de colonnes: {df.shape[1]}")
		print("Types des colonnes:")
		print(df.dtypes.to_string())
		print("Valeurs manquantes:")
		print(df.isna().sum().to_string())


if __name__ == "__main__":
	inspect_raw_csv_files()
