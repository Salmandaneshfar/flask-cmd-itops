import argparse
import sys
from typing import Dict, List, Optional

import pandas as pd

from app import create_app  # type: ignore
from models import db, Server  # type: ignore


REQUIRED_COLUMNS = [
	"name",
	"ip_address",
	"os_type",
	"status",
]


def normalize_columns(columns: List[str]) -> List[str]:
	"""Lowercase and strip spaces/underscores for matching."""
	return [
		c.strip().lower().replace(" ", "_") if isinstance(c, str) else c for c in columns
	]


def build_column_map(headers: List[str]) -> Dict[str, str]:
	"""Map required logical names to actual dataframe column names (case-insensitive)."""
	normalized = normalize_columns(headers)
	actual_by_norm = {n: orig for n, orig in zip(normalized, headers)}
	col_map: Dict[str, str] = {}
	for req in REQUIRED_COLUMNS:
		if req in actual_by_norm:
			col_map[req] = actual_by_norm[req]
	return col_map


def validate_required_columns(col_map: Dict[str, str]) -> Optional[str]:
	missing = [c for c in REQUIRED_COLUMNS if c not in col_map]
	if missing:
		return f"Missing required columns in Excel: {', '.join(missing)}"
	return None


def import_servers(
	file_path: str,
	sheet_name: Optional[str],
	update_on_conflict: bool,
	dry_run: bool,
) -> int:
	"""Import servers from Excel into DB. Returns number of processed rows."""
	# Read Excel
	try:
		if file_path.lower().endswith(".csv"):
			df = pd.read_csv(file_path)
		else:
			df = pd.read_excel(file_path, sheet_name=sheet_name)  # requires openpyxl
	except Exception as e:
		print(f"Failed to read file: {e}")
		return 1

	if df is None or df.empty:
		print("No rows found in the provided file/sheet.")
		return 0

	col_map = build_column_map(list(df.columns))
	err = validate_required_columns(col_map)
	if err:
		print(err)
		return 1

	processed = 0
	created = 0
	updated = 0
	skipped = 0
	errors = 0
	issues: List[str] = []

	for idx, row in df.iterrows():
		try:
			name = str(row[col_map["name"]]).strip() if pd.notna(row[col_map["name"]]) else ""
			ip_address = str(row[col_map["ip_address"]]).strip() if pd.notna(row[col_map["ip_address"]]) else ""
			os_type = str(row[col_map["os_type"]]).strip() if pd.notna(row[col_map["os_type"]]) else ""
			status = str(row[col_map["status"]]).strip() if pd.notna(row[col_map["status"]]) else ""
			description = None
			for cand in ("description", "desc", "شرح"):
				norm = normalize_columns([cand])[0]
				# try to find by normalized name in df
				df_norm = {n: c for n, c in zip(normalize_columns(list(df.columns)), list(df.columns))}
				if norm in df_norm:
					description_col = df_norm[norm]
					description = (
						str(row[description_col]).strip() if pd.notna(row[description_col]) else None
					)
					break

			if not name or not ip_address or not os_type or not status:
				issues.append(f"Row {idx+2}: missing required fields (name/ip/os/status)")
				skipped += 1
				continue

			# Conflict policy: try match by name first, fallback to ip_address
			existing = Server.query.filter_by(name=name).first()
			if not existing:
				existing = Server.query.filter_by(ip_address=ip_address).first()

			if existing:
				if update_on_conflict:
					if not dry_run:
						existing.ip_address = ip_address
						existing.os_type = os_type
						existing.status = status
						existing.description = description
					updated += 1
				else:
					skipped += 1
			else:
				if not dry_run:
					server = Server(
						name=name,
						ip_address=ip_address,
						os_type=os_type,
						status=status,
						description=description,
					)
					db.session.add(server)
				created += 1

			processed += 1
		except Exception as e:
			errors += 1
			issues.append(f"Row {idx+2}: error {e}")

	if not dry_run:
		try:
			db.session.commit()
		except Exception as e:
			print(f"Commit failed: {e}")
			db.session.rollback()
			return 1

	print(
		f"Processed: {processed}, Created: {created}, Updated: {updated}, Skipped: {skipped}, Errors: {errors}"
	)
	if issues:
		print("Notes:")
		for it in issues[:50]:
			print(f"- {it}")
		if len(issues) > 50:
			print(f"... and {len(issues)-50} more")

	return 0


def main() -> int:
	parser = argparse.ArgumentParser(
		description="Import Servers from Excel/CSV into the database"
	)
	parser.add_argument("file", help="Path to Excel (.xlsx) or CSV file")
	parser.add_argument(
		"--sheet",
		dest="sheet_name",
		help="Excel sheet name (if multiple). Ignored for CSV",
	)
	parser.add_argument(
		"--update",
		action="store_true",
		help="Update existing records on conflict (by name/ip)",
	)
	parser.add_argument(
		"--dry-run",
		action="store_true",
		help="Validate and show summary without writing to DB",
	)

	args = parser.parse_args()

	app = create_app()
	with app.app_context():
		return import_servers(
			file_path=args.file,
			sheet_name=args.sheet_name,
			update_on_conflict=args.update,
			dry_run=args.dry_run,
		)


if __name__ == "__main__":
	sys.exit(main())



