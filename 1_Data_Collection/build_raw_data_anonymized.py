"""Build raw_data_anonymized.csv from the original and anonymized raw SMS exports.

The script preserves the raw SMS export schema from the anonymized raw files:
- UserId is added for grouping and traceability
- original raw files are assigned orig_user_001, orig_user_002, ... in sorted order
- anonymized files keep anon_ prefixed ids based on their filenames
- original message content is anonymized with the same token logic used in the project pipeline
- all raw rows are kept, not only balance-related transactions

Output:
    1_Data_Collection/raw_data_anonymized.csv
"""

from __future__ import annotations

import csv
import hashlib
import os
import re
import sys
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
ORIGINAL_RAW_DIR = BASE_DIR / "Data" / "Original_Raw"
ANONYMIZED_RAW_DIR = BASE_DIR / "Data" / "Anonymized_raw"
OUTPUT_PATH = BASE_DIR / "1_Data_Collection" / "raw_data_anonymized.csv"

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

COL_ALIASES = {
    "date": ["date"],
    "heure": ["heure", "time"],
    "direction": ["direction"],
    "contact": ["contact"],
    "telephone": ["téléphone", "telephone", "phone"],
    "contenu": ["contenu", "content"],
    "type": ["type"],
}

BALANCE_KEYWORDS = [
    "nouveau solde",
    "nouveau solde est",
    "new balance",
    "your new balance",
]
BALANCE_RE = re.compile(r"(?:" + "|".join(re.escape(k) for k in BALANCE_KEYWORDS) + r")", re.IGNORECASE)

AMOUNT_RE = re.compile(
    r"(?:montant[^:]*:\s*|(?<!solde\sest\s)de\s+|amount\s+|of\s+)"
    r"(\d[\d\s,\.]*?)\s*(FCFA|XAF)",
    re.IGNORECASE,
)
AMOUNT_FALLBACK_RE = re.compile(r"(\d[\d\s]*?)\s*(FCFA|XAF)", re.IGNORECASE)
BALANCE_VAL_RE = re.compile(
    r"(?:"
    r"votre\s+nouveau\s+solde\s+est\s+de\s+|your\s+new\s+balance\s+is\s+|"
    r"nouveau\s+solde\s+est\s+de\s*:?|new\s+balance\s+is\s*:?|"
    r"nouveau\s+solde\s+est\s*:?|new\s+balance\s+is\s*:?|"
    r"nouveau\s+solde\s*:?|new\s+balance\s*:?|"
    r"solde\s*:?|balance\s*:?"
    r")\s*"
    r"(\d[\d\s,\.]*?)\s*(FCFA|XAF)",
    re.IGNORECASE,
)

TX_RULES = [
    ("retrait", "OUT", [
        r"retrait\s+d'argent",
        r"retrait\s+de\s+\d",
        r"vous\s+avez\s+effectue\s+avec\s+succes\s+le\s+retrait",
        r"withdrawal\s+successful",
        r"cash\s+out",
    ]),
    ("depot", "IN", [
        r"depot\s+effectue\s+par",
        r"deposit\s+made\s+by",
        r"deposit\s+to\s+your",
    ]),
    ("transfert", "IN", [
        r"(transfert|transfer).*?(frais|fees?)\s*(:|(de)|was|is)?\s*0\s*(xaf|fcfa)",
        r"vous\s+avez\s+re[cç]u\s+\d",
        r"you\s+have\s+received\s+\d",
        r"has\s+been\s+added\s+to\s+your",
        r"adjustment\s+has\s+been\s+made",
    ]),
    ("transfert", "OUT", [
        r"transfert\s+de\s+\d+\s*(fcfa|xaf)",
        r"transfert\s+de\s+\d+fcfa",
        r"transfer\s+of\s+\d",
        r"transfert.*effectue.*succes.*\d",
        r"transfert.*vers\s+\d",
    ]),
    ("paiement", "OUT", [
        r"paiement\s+de\s+votre\s+facture",
        r"votre\s+paiement\s+de\s+\d",
        r"your\s+payment\s+of\s+\d",
        r"paiement.*réussi",
        r"payment.*successful",
        r"paiement\s+total",
        r"vous\s+venez\s+d.effectuer\s+un\s+paiement",
    ]),
    ("rechargement", "OUT", [
        r"rechargement\s+reussi",
        r"top.?up\s+successful",
        r"recharge\s+successful",
    ]),
    ("airtime", "OUT", [
        r"achete\s+avec\s+succes.*airtime",
        r"airtime.*transaction",
        r"paiement.*airtime",
        r"paiement.*de",
        r"payment.*airtime",
        r"you\s+have\s+received.*airtime\s+from",
        r"vous\s+avez\s+re[cç]u.*airtime\s+de",
        r"recu.*xaf\s+airtime",
        r"received.*xaf\s+airtime",
    ]),
    ("transaction", "OUT", [
        r"une\s+transaction\s+de\s+\d",
        r"a\s+transaction\s+of\s+\d",
        r"transaction.*effectuee\s+par",
        r"transaction.*made\s+by",
    ]),
]
TX_RULES_COMPILED = [
    (tx_type, direction, [re.compile(pattern, re.IGNORECASE) for pattern in patterns])
    for tx_type, direction, patterns in TX_RULES
]

PHONE_RE = re.compile(r"\b\d{9,12}\b")
NAME_AFTER_PHONE_RE = re.compile(
    r"\b(\d{9,12})\s*[-–:]?\s*([A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}(?:\s+[A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}){0,3})\b"
)
NAME_BEFORE_PHONE_RE = re.compile(
    r"\b([A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}(?:\s+[A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}){0,3})\s*\((\d{9,12})\)"
)
WITHDRAWAL_NAME_RE = re.compile(
    r"\b(?:withdrawn|withdraw|retrait)\b.*?\b(?:chez|at)\s*[:\-–]?\s*([A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}(?:\s+[A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}){0,4})\b",
    re.IGNORECASE,
)


def short_hash(value: str, length: int = 4) -> str:
    return hashlib.md5(str(value).encode()).hexdigest()[:length].upper()


def _phone_variants(phone):
    if not phone:
        return []
    phone = str(phone).strip()
    variants = {phone}
    if re.match(r"^6\d{8}$", phone):
        variants.add("237" + phone)
    if re.match(r"^237\d{9}$", phone):
        variants.add(phone[3:])
    return list(variants)


def anonymize_message(text, user_name=None, user_phone=None, user_id="USER"):
    result = str(text)
    if user_name and str(user_name).strip():
        result = re.sub(re.escape(str(user_name).strip()), f"[{user_id}]", result, flags=re.IGNORECASE)

    def replace_withdrawal_name(match):
        name = match.group(1).strip()
        token = short_hash(name)
        return match.group(0).replace(name, f"[CONTACT_{token}]")

    result = WITHDRAWAL_NAME_RE.sub(replace_withdrawal_name, result)

    def replace_name_after(match):
        phone = match.group(1)
        name = match.group(2).strip()
        token = short_hash(name)
        return f"{phone} [CONTACT_{token}]"

    result = NAME_AFTER_PHONE_RE.sub(replace_name_after, result)

    def replace_name_before(match):
        name = match.group(1).strip()
        phone = match.group(2)
        token = short_hash(name)
        return f"[CONTACT_{token}] ({phone})"

    result = NAME_BEFORE_PHONE_RE.sub(replace_name_before, result)

    for variant in _phone_variants(user_phone):
        result = result.replace(variant, f"[{user_id}_phone]")

    def replace_phone(match):
        phone = match.group(0)
        return f"[PHONE_{phone[-4:]}]"

    result = PHONE_RE.sub(replace_phone, result)

    skip_tokens = {"FCFA", "XAF", "SMS", "ID", "MTN", "ORANGE", "MOBILEMONEY", "OM", "MOMO", "OTP", "PIN"}

    def replace_caps_name(match):
        name = match.group(0).strip()
        words = name.split()
        if len(words) < 2:
            return name
        if any(word in skip_tokens for word in words):
            return name
        return name

    result = re.sub(
        r"\b([A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}(?:\s+[A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}){1,3})\b",
        replace_caps_name,
        result,
    )
    return result


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for canonical, aliases in COL_ALIASES.items():
        for col in df.columns:
            if str(col).strip().lower() in aliases:
                rename[col] = canonical
                break
    return df.rename(columns=rename)


def load_file(path: Path) -> pd.DataFrame:
    path_str = str(path)
    if path_str.endswith(".xlsx"):
        for skip in range(5):
            df = pd.read_excel(path_str, skiprows=skip)
            cols_lower = [str(c).strip().lower() for c in df.columns]
            if any(c in cols_lower for c in ["date", "contenu", "content"]):
                df = normalize_columns(df)
                if "contenu" in df.columns:
                    df = df.dropna(subset=["contenu"], how="all")
                    df["contenu"] = df["contenu"].astype(str).str.replace("_x000d_", " ", regex=False).str.strip()
                return df
    elif path_str.endswith(".csv"):
        for skip in range(5):
            try:
                df = pd.read_csv(path_str, skiprows=skip)
                cols_lower = [str(c).strip().lower() for c in df.columns]
                if any(c in cols_lower for c in ["date", "contenu", "content"]):
                    df = normalize_columns(df)
                    if "contenu" in df.columns:
                        df = df.dropna(subset=["contenu"], how="all")
                        df["contenu"] = df["contenu"].astype(str).str.replace("_x000d_", " ", regex=False).str.strip()
                    return df
            except Exception:
                continue
    raise ValueError(f"Could not detect column headers in: {path}")


def load_anonymized_csv(path: Path) -> pd.DataFrame:
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            header = next(reader)
            _ = [h.strip().lower() for h in header]
            for row in reader:
                if len(row) >= 4:
                    rows.append({
                        "date": row[0].strip(),
                        "heure": row[1].strip(),
                        "contact": row[2].strip(),
                        "contenu": row[3].strip().strip('"'),
                    })
                elif len(row) == 1 and "," in row[0]:
                    inner = row[0].strip().strip('"').replace('""', '"')
                    parts = inner.split(",", 3)
                    if len(parts) >= 4:
                        rows.append({
                            "date": parts[0].strip(),
                            "heure": parts[1].strip(),
                            "contact": parts[2].strip(),
                            "contenu": parts[3].strip().strip('"'),
                        })
    except Exception:
        pass

    if not rows:
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
        lines = raw.strip().split("\n")
        current_row = None
        for line in lines[1:]:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            if line_stripped.startswith('"') and current_row is None:
                current_row = line_stripped
            elif current_row is not None:
                current_row += " " + line_stripped

            if current_row and current_row.endswith('"'):
                inner = current_row[1:-1].replace('""', '"')
                parts = inner.split(",", 3)
                if len(parts) >= 4:
                    rows.append({
                        "date": parts[0].strip(),
                        "heure": parts[1].strip(),
                        "contact": parts[2].strip(),
                        "contenu": parts[3].strip().strip('"'),
                    })
                current_row = None

    if not rows:
        return pd.DataFrame(columns=["date", "heure", "contact", "contenu"])
    return pd.DataFrame(rows)


def detect_operator(df: pd.DataFrame) -> str:
    for col in ["contact", "telephone"]:
        if col in df.columns:
            sample = df[col].dropna().astype(str).str.lower()
            if sample.str.contains("orangemoney").any():
                return "OrangeMoney"
            if sample.str.contains("mobilemoney").any():
                return "MobileMoney"
    return "Unknown"


def detect_operator_from_content(df: pd.DataFrame) -> str:
    if "contenu" in df.columns:
        sample = df["contenu"].dropna().astype(str).str.lower()
        if sample.str.contains("orange").any():
            return "OrangeMoney"
        if sample.str.contains("momo|mtn|mobile money").any():
            return "MobileMoney"
    return "Unknown"


def filter_balance_messages(df: pd.DataFrame) -> pd.DataFrame:
    if "contenu" not in df.columns:
        return df
    mask = df["contenu"].apply(lambda value: bool(BALANCE_RE.search(str(value))))
    return df[mask].copy().reset_index(drop=True)


def clean_amount(raw):
    if raw is None:
        return None
    cleaned = re.sub(r"[\s,]", "", str(raw))
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_amount(text):
    match = AMOUNT_RE.search(text)
    if match:
        return clean_amount(match.group(1)), match.group(2).upper()
    match = AMOUNT_FALLBACK_RE.search(text)
    if match:
        return clean_amount(match.group(1)), match.group(2).upper()
    return None, None


def extract_new_balance(text):
    match = BALANCE_VAL_RE.search(text)
    if match:
        return clean_amount(match.group(1)), match.group(2).upper()
    return None, None


TX_RULES_COMPILED = [
    (tx_type, direction, [re.compile(pattern, re.IGNORECASE) for pattern in patterns])
    for tx_type, direction, patterns in TX_RULES
]


def classify_transaction(text):
    for tx_type, direction, compiled_patterns in TX_RULES_COMPILED:
        for pattern in compiled_patterns:
            if pattern.search(text):
                return tx_type, direction
    return "autre", "unknown"


RAW_OUTPUT_COLUMNS = ["UserId", "Date", "Time", "Direction", "Contact", "Phone", "Content", "Type"]


def infer_raw_direction(text: str) -> str:
    """Best-effort direction label for rows that do not already contain one."""
    _, flow = classify_transaction(str(text))
    if flow == "IN":
        return "Received"
    if flow == "OUT":
        return "Sent"
    return ""


def normalize_raw_records(df: pd.DataFrame, user_id: str, *, anonymize_content: bool = False, infer_direction: bool = False) -> pd.DataFrame:
    """Normalize a loaded SMS export into the raw dataset schema."""
    records = []

    for _, row in df.iterrows():
        content = str(row.get("contenu", row.get("content", "")))
        if anonymize_content:
            content = anonymize_message(content, user_name=None, user_phone=None, user_id=user_id)

        direction = row.get("direction", "")
        if (not isinstance(direction, str) or not direction.strip()) and infer_direction:
            direction = infer_raw_direction(content)

        records.append({
            "UserId": user_id,
            "Date": row.get("date", ""),
            "Time": row.get("heure", row.get("time", "")),
            "Direction": direction,
            "Contact": row.get("contact", ""),
            "Phone": row.get("telephone", row.get("phone", "")),
            "Content": content,
            "Type": row.get("type", "SMS") if str(row.get("type", "")).strip() else "SMS",
        })

    result = pd.DataFrame(records)
    if result.empty:
        return pd.DataFrame(columns=RAW_OUTPUT_COLUMNS)
    return result.reindex(columns=RAW_OUTPUT_COLUMNS)


def build_original_dataset() -> pd.DataFrame:
    all_records = []
    file_list = sorted(os.listdir(ORIGINAL_RAW_DIR))
    user_counter = 0

    for fname in file_list:
        if not (fname.endswith(".xlsx") or fname.endswith(".csv")):
            continue
        user_counter += 1
        user_id = f"orig_user_{user_counter:03d}"
        fpath = ORIGINAL_RAW_DIR / fname
        df_raw = load_file(fpath)
        df_normalized = normalize_raw_records(df_raw, user_id, anonymize_content=True, infer_direction=False)
        if len(df_normalized) > 0:
            all_records.append(df_normalized)
            print(f"  ✓ {fname}: {len(df_raw)} raw -> {len(df_normalized)} rows ({user_id})")
        else:
            print(f"  ⚠ {fname}: {len(df_raw)} raw -> 0 rows ({user_id})")

    return pd.concat(all_records, ignore_index=True) if all_records else pd.DataFrame()


def build_anonymized_dataset() -> pd.DataFrame:
    all_records = []
    file_list = sorted(os.listdir(ANONYMIZED_RAW_DIR))

    for fname in file_list:
        if not (fname.endswith(".xlsx") or fname.endswith(".csv")):
            continue

        stem = fname.replace(".xlsx", "").replace(".csv", "")
        user_id = f"anon_{stem}"
        fpath = ANONYMIZED_RAW_DIR / fname

        if fname.endswith(".xlsx"):
            df_raw = load_file(fpath)
            df_normalized = normalize_raw_records(df_raw, user_id, anonymize_content=True, infer_direction=False)
        else:
            df_raw = load_anonymized_csv(fpath)
            df_normalized = normalize_raw_records(df_raw, user_id, anonymize_content=False, infer_direction=True)

        if len(df_normalized) > 0:
            all_records.append(df_normalized)
            print(f"  ✓ {fname}: {len(df_raw)} raw -> {len(df_normalized)} rows ({user_id})")
        else:
            print(f"  ⚠ {fname}: {len(df_raw)} raw -> 0 rows ({user_id})")

    return pd.concat(all_records, ignore_index=True) if all_records else pd.DataFrame()


def main() -> None:
    print("=" * 72)
    print("BUILDING raw_data_anonymized.csv")
    print("=" * 72)

    print("\n[1] Extracting original raw files...")
    df_original = build_original_dataset()

    print("\n[2] Extracting anonymized raw files...")
    df_anonymized = build_anonymized_dataset()

    if df_original.empty and df_anonymized.empty:
        raise RuntimeError("No rows were extracted from either raw dataset.")

    df_all = pd.concat([df_original, df_anonymized], ignore_index=True)
    df_all = df_all.sort_values(["UserId", "Date", "Time"]).reset_index(drop=True)
    df_all.to_csv(OUTPUT_PATH, index=False)

    print("\n" + "=" * 72)
    print("DONE")
    print("=" * 72)
    print(f"Original rows : {len(df_original):,}")
    print(f"Anonymized rows: {len(df_anonymized):,}")
    print(f"Merged rows             : {len(df_all):,}")
    print(f"Unique users            : {df_all['UserId'].nunique():,}")
    print(f"Saved to                : {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
