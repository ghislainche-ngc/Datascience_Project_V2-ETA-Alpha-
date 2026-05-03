"""
Mobile Money Transaction Data Pipeline
=======================================
STEP 1: Extraction (both datasets)
STEP 2: Cleaning (separate)
STEP 3: Data source labeling
STEP 4: Validation
STEP 5: Merging
STEP 6: Feature engineering
STEP 7: Output
"""

import re
import hashlib
import os
import sys
import warnings
import pandas as pd
import numpy as np
from pathlib import Path

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

# ─────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
ORIGINAL_RAW_DIR = BASE_DIR / "Data" / "Original_Raw"
ANONYMIZED_RAW_DIR = BASE_DIR / "Data" / "Anonymized_raw"
EXTRACTED_ORIGINAL_DIR = BASE_DIR / "Data" / "extracted" / "original"
EXTRACTED_ANON_DIR = BASE_DIR / "Data" / "extracted" / "anonymized"
CLEANED_DIR = BASE_DIR / "Data" / "cleaned"
OUTPUT_DIR = BASE_DIR / "Data" / "output"

for d in [EXTRACTED_ORIGINAL_DIR, EXTRACTED_ANON_DIR, CLEANED_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ═════════════════════════════════════════════════════════════
# EXTRACTOR LOGIC (copied verbatim from Mobile_Money_Data_Extractor V2-1)
# ═════════════════════════════════════════════════════════════

# ── Column name aliases (FR / EN) ─────────────────────────────
COL_ALIASES = {
    'date':      ['date'],
    'heure':     ['heure', 'time'],
    'direction': ['direction'],
    'contact':   ['contact'],
    'telephone': ['téléphone', 'telephone', 'phone'],
    'contenu':   ['contenu', 'content'],
    'type':      ['type'],
}

def normalize_columns(df):
    rename = {}
    for canonical, aliases in COL_ALIASES.items():
        for col in df.columns:
            if str(col).strip().lower() in aliases:
                rename[col] = canonical
                break
    return df.rename(columns=rename)

def load_file(path):
    path = str(path)
    if path.endswith('.xlsx'):
        for skip in range(5):
            df = pd.read_excel(path, skiprows=skip)
            cols_lower = [str(c).strip().lower() for c in df.columns]
            if any(c in cols_lower for c in ['date', 'contenu', 'content']):
                df = normalize_columns(df)
                if 'contenu' in df.columns:
                    df = df.dropna(subset=['contenu'], how='all')
                    df['contenu'] = df['contenu'].astype(str).str.replace('_x000d_', ' ', regex=False).str.strip()
                return df
    elif path.endswith('.csv'):
        for skip in range(5):
            try:
                df = pd.read_csv(path, skiprows=skip)
                cols_lower = [str(c).strip().lower() for c in df.columns]
                if any(c in cols_lower for c in ['date', 'contenu', 'content']):
                    df = normalize_columns(df)
                    if 'contenu' in df.columns:
                        df = df.dropna(subset=['contenu'], how='all')
                        df['contenu'] = df['contenu'].astype(str).str.replace('_x000d_', ' ', regex=False).str.strip()
                    return df
            except Exception:
                continue
    raise ValueError(f'Could not detect column headers in: {path}')


def load_anonymized_csv(path):
    """Parse the pre-anonymized CSV files (user011-user018) with non-standard quoting."""
    import csv
    rows = []

    # Try standard CSV parsing first (handles multiline quoted fields)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            # Normalize header
            header_lower = [h.strip().lower() for h in header]

            for row in reader:
                if len(row) >= 4:
                    rows.append({
                        'date': row[0].strip(),
                        'heure': row[1].strip(),
                        'contact': row[2].strip(),
                        'contenu': row[3].strip().strip('"'),
                    })
                elif len(row) == 1 and ',' in row[0]:
                    # Format A: entire row is one string with internal commas
                    inner = row[0].strip().strip('"').replace('""', '"')
                    parts = inner.split(',', 3)
                    if len(parts) >= 4:
                        rows.append({
                            'date': parts[0].strip(),
                            'heure': parts[1].strip(),
                            'contact': parts[2].strip(),
                            'contenu': parts[3].strip().strip('"'),
                        })
    except Exception:
        pass

    if not rows:
        # Fallback: manual line-by-line parsing for outer-quoted format
        with open(path, 'r', encoding='utf-8') as f:
            raw = f.read()
        lines = raw.strip().split('\n')
        current_row = None
        for line in lines[1:]:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            if line_stripped.startswith('"') and current_row is None:
                current_row = line_stripped
            elif current_row is not None:
                current_row += ' ' + line_stripped

            if current_row and current_row.endswith('"'):
                inner = current_row[1:-1].replace('""', '"')
                parts = inner.split(',', 3)
                if len(parts) >= 4:
                    rows.append({
                        'date': parts[0].strip(),
                        'heure': parts[1].strip(),
                        'contact': parts[2].strip(),
                        'contenu': parts[3].strip().strip('"'),
                    })
                current_row = None

    if not rows:
        return pd.DataFrame(columns=['date', 'heure', 'contact', 'contenu'])
    return pd.DataFrame(rows)


# ── Operator detection ────────────────────────────────────────
def detect_operator(df):
    for col in ['contact', 'telephone']:
        if col in df.columns:
            sample = df[col].dropna().astype(str).str.lower()
            if sample.str.contains('orangemoney').any():
                return 'OrangeMoney'
            if sample.str.contains('mobilemoney').any():
                return 'MobileMoney'
    return 'Unknown'

def detect_operator_from_content(df):
    if 'contenu' in df.columns:
        sample = df['contenu'].dropna().astype(str).str.lower()
        if sample.str.contains('orange').any():
            return 'OrangeMoney'
        if sample.str.contains('momo|mtn|mobile money').any():
            return 'MobileMoney'
    return 'Unknown'


# ── Balance filter ────────────────────────────────────────────
BALANCE_KEYWORDS = [
    'nouveau solde', 'nouveau solde est',
    'new balance', 'your new balance',
]
BALANCE_RE = re.compile(
    r'(?:' + '|'.join(re.escape(k) for k in BALANCE_KEYWORDS) + r')',
    re.IGNORECASE
)

def filter_balance_messages(df):
    if 'contenu' not in df.columns:
        return df
    mask = df['contenu'].apply(lambda x: bool(BALANCE_RE.search(str(x))))
    return df[mask].copy().reset_index(drop=True)


# ── Amount & balance extractors ───────────────────────────────
AMOUNT_RE = re.compile(
    r'(?:montant[^:]*:\s*|(?<!solde\sest\s)de\s+|amount\s+|of\s+)'
    r'(\d[\d\s,\.]*?)\s*(FCFA|XAF)',
    re.IGNORECASE
)
AMOUNT_FALLBACK_RE = re.compile(
    r'(\d[\d\s]*?)\s*(FCFA|XAF)',
    re.IGNORECASE
)
BALANCE_VAL_RE = re.compile(
    r'(?:'
        r'votre\s+nouveau\s+solde\s+est\s+de\s+|your\s+new\s+balance\s+is\s+|'
        r'nouveau\s+solde\s+est\s+de\s*:?|new\s+balance\s+is\s*:?|'
        r'nouveau\s+solde\s+est\s*:?|new\s+balance\s+is\s*:?|'
        r'nouveau\s+solde\s*:?|new\s+balance\s*:?|'
        r'solde\s*:?|balance\s*:?'
    r')\s*'
    r'(\d[\d\s,\.]*?)\s*(FCFA|XAF)',
    re.IGNORECASE
)

def clean_amount(raw):
    if raw is None:
        return None
    cleaned = re.sub(r'[\s,]', '', str(raw))
    try:
        return float(cleaned)
    except ValueError:
        return None

def extract_amount(text):
    m = AMOUNT_RE.search(text)
    if m:
        return clean_amount(m.group(1)), m.group(2).upper()
    m = AMOUNT_FALLBACK_RE.search(text)
    if m:
        return clean_amount(m.group(1)), m.group(2).upper()
    return None, None

def extract_new_balance(text):
    m = BALANCE_VAL_RE.search(text)
    if m:
        return clean_amount(m.group(1)), m.group(2).upper()
    return None, None


# ── Transaction classification ────────────────────────────────
TX_RULES = [
    ('retrait', 'OUT', [
        r"retrait\s+d'argent",
        r'retrait\s+de\s+\d',
        r'vous\s+avez\s+effectue\s+avec\s+succes\s+le\s+retrait',
        r'withdrawal\s+successful',
        r'cash\s+out',
    ]),
    ('depot', 'IN', [
        r'depot\s+effectue\s+par',
        r'deposit\s+made\s+by',
        r'deposit\s+to\s+your',
    ]),
    ('transfert', 'IN', [
        r'(transfert|transfer).*?(frais|fees?)\s*(:|(de)|was|is)?\s*0\s*(xaf|fcfa)',
        r'vous\s+avez\s+re[cç]u\s+\d',
        r'you\s+have\s+received\s+\d',
        r'has\s+been\s+added\s+to\s+your',
        r'adjustment\s+has\s+been\s+made',
    ]),
    ('transfert', 'OUT', [
        r'transfert\s+de\s+\d+\s*(fcfa|xaf)',
        r'transfert\s+de\s+\d+fcfa',
        r'transfer\s+of\s+\d',
        r'transfert.*effectue.*succes.*\d',
        r'transfert.*vers\s+\d',
    ]),
    ('paiement', 'OUT', [
        r'paiement\s+de\s+votre\s+facture',
        r'votre\s+paiement\s+de\s+\d',
        r'your\s+payment\s+of\s+\d',
        r'paiement.*réussi',
        r'payment.*successful',
        r'paiement\s+total',
        r'vous\s+venez\s+d.effectuer\s+un\s+paiement',
    ]),
    ('rechargement', 'OUT', [
        r'rechargement\s+reussi',
        r'top.?up\s+successful',
        r'recharge\s+successful',
    ]),
    ('airtime', 'OUT', [
        r'achete\s+avec\s+succes.*airtime',
        r'airtime.*transaction',
        r'paiement.*airtime',
        r'paiement.*de',
        r'payment.*airtime',
        r'you\s+have\s+received.*airtime\s+from',
        r'vous\s+avez\s+re[cç]u.*airtime\s+de',
        r'recu.*xaf\s+airtime',
        r'received.*xaf\s+airtime',
    ]),
    ('transaction', 'OUT', [
        r'une\s+transaction\s+de\s+\d',
        r'a\s+transaction\s+of\s+\d',
        r'transaction.*effectuee\s+par',
        r'transaction.*made\s+by',
    ]),
]

TX_RULES_COMPILED = [
    (tx_type, direction, [re.compile(p, re.IGNORECASE) for p in patterns])
    for tx_type, direction, patterns in TX_RULES
]

def classify_transaction(text):
    for tx_type, direction, compiled_patterns in TX_RULES_COMPILED:
        for pattern in compiled_patterns:
            if pattern.search(text):
                return tx_type, direction
    return 'autre', 'unknown'


# ── Anonymization ─────────────────────────────────────────────
def short_hash(value, length=4):
    return hashlib.md5(str(value).encode()).hexdigest()[:length].upper()

PHONE_RE = re.compile(r'\b\d{9,12}\b')
NAME_AFTER_PHONE_RE = re.compile(
    r'\b(\d{9,12})\s*[-–:]?\s*([A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}(?:\s+[A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}){0,3})\b'
)
NAME_BEFORE_PHONE_RE = re.compile(
    r'\b([A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}(?:\s+[A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}){0,3})\s*\((\d{9,12})\)'
)
WITHDRAWAL_NAME_RE = re.compile(
    r'\b(?:withdrawn|withdraw|retrait)\b.*?\b(?:chez|at)\s*[:\-–]?\s*([A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}(?:\s+[A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}){0,4})\b',
    re.IGNORECASE
)

def _phone_variants(phone):
    if not phone:
        return []
    phone = str(phone).strip()
    variants = {phone}
    if re.match(r'^6\d{8}$', phone):
        variants.add('237' + phone)
    if re.match(r'^237\d{9}$', phone):
        variants.add(phone[3:])
    return list(variants)

def anonymize_message(text, user_name=None, user_phone=None, user_id="USER"):
    result = text
    if user_name and user_name.strip():
        result = re.sub(re.escape(user_name.strip()), f'[{user_id}]', result, flags=re.IGNORECASE)

    def replace_withdrawal_name(m):
        name = m.group(1).strip()
        token = short_hash(name)
        return m.group(0).replace(name, f'[CONTACT_{token}]')

    result = WITHDRAWAL_NAME_RE.sub(replace_withdrawal_name, result)

    def replace_name_after(m):
        phone = m.group(1)
        name = m.group(2).strip()
        token = short_hash(name)
        return f'{phone} [CONTACT_{token}]'
    result = NAME_AFTER_PHONE_RE.sub(replace_name_after, result)

    def replace_name_before(m):
        name = m.group(1).strip()
        phone = m.group(2)
        token = short_hash(name)
        return f'[CONTACT_{token}] ({phone})'
    result = NAME_BEFORE_PHONE_RE.sub(replace_name_before, result)

    for variant in _phone_variants(user_phone):
        result = result.replace(variant, f'[{user_id}_phone]')

    def replace_phone(m):
        phone = m.group(0)
        return f'[PHONE_{phone[-4:]}]'
    result = PHONE_RE.sub(replace_phone, result)

    skip_tokens = {'FCFA', 'XAF', 'SMS', 'ID', 'MTN', 'ORANGE',
                   'MOBILEMONEY', 'OM', 'MOMO', 'OTP', 'PIN'}

    def replace_caps_name(m):
        name = m.group(0).strip()
        words = name.split()
        if len(words) < 2:
            return name
        if any(w in skip_tokens for w in words):
            return name
        token = short_hash(name)
        return name
    result = re.sub(
        r'\b([A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}(?:\s+[A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ]{2,}){1,3})\b',
        replace_caps_name, result)
    return result


# ═════════════════════════════════════════════════════════════
# STEP 1: EXTRACTION
# ═════════════════════════════════════════════════════════════

def extract_transactions_from_df(df, user_id, operator=None):
    """Run the extractor pipeline on a loaded dataframe."""
    if operator is None:
        operator = detect_operator(df)
        if operator == 'Unknown':
            operator = detect_operator_from_content(df)

    df_filtered = filter_balance_messages(df)

    if len(df_filtered) == 0:
        return pd.DataFrame(columns=[
            'UserId', 'Date', 'Heure', 'Operator', 'Transaction_type',
            'Direction', 'Amount', 'Currency', 'New_balance', 'Anonymized_Content'
        ])

    records = []
    for _, row in df_filtered.iterrows():
        text = str(row.get('contenu', ''))
        tx_type, direction = classify_transaction(text)
        amount, currency = extract_amount(text)
        new_balance, bal_currency = extract_new_balance(text)
        if currency is None and bal_currency:
            currency = bal_currency

        anon_content = anonymize_message(text, user_name=None, user_phone=None, user_id=user_id)

        records.append({
            'UserId': user_id,
            'Date': row.get('date', ''),
            'Heure': row.get('heure', ''),
            'Operator': operator,
            'Transaction_type': tx_type,
            'Direction': direction,
            'Amount': amount,
            'Currency': currency,
            'New_balance': new_balance,
            'Anonymized_Content': anon_content,
        })

    return pd.DataFrame(records)


def run_extraction_original():
    """Extract from all original raw files."""
    print("=" * 60)
    print("STEP 1: EXTRACTING FROM ORIGINAL RAW DATA")
    print("=" * 60)

    all_records = []
    file_list = sorted(os.listdir(ORIGINAL_RAW_DIR))
    user_counter = 0

    for fname in file_list:
        fpath = ORIGINAL_RAW_DIR / fname
        if not (fname.endswith('.xlsx') or fname.endswith('.csv')):
            continue

        user_counter += 1
        user_id = f"orig_user_{user_counter:03d}"

        try:
            df_raw = load_file(fpath)
            df_extracted = extract_transactions_from_df(df_raw, user_id)

            if len(df_extracted) > 0:
                all_records.append(df_extracted)
                print(f"  ✓ {fname}: {len(df_raw)} raw → {len(df_extracted)} transactions ({user_id})")
            else:
                print(f"  ⚠ {fname}: {len(df_raw)} raw → 0 balance-related messages ({user_id})")
        except Exception as e:
            print(f"  ✗ {fname}: ERROR - {str(e)[:80]}")

    if all_records:
        df_original = pd.concat(all_records, ignore_index=True)
    else:
        df_original = pd.DataFrame()

    out_path = EXTRACTED_ORIGINAL_DIR / "extracted_original.csv"
    df_original.to_csv(out_path, index=False)
    print(f"\n✅ Original extraction complete: {len(df_original)} total transactions from {len(all_records)} files")
    print(f"   Saved to: {out_path}")
    return df_original


def run_extraction_anonymized():
    """Extract from all anonymized files."""
    print("\n" + "=" * 60)
    print("STEP 1b: EXTRACTING FROM ANONYMIZED DATA")
    print("=" * 60)

    all_records = []
    file_list = sorted(os.listdir(ANONYMIZED_RAW_DIR))

    for fname in file_list:
        fpath = ANONYMIZED_RAW_DIR / fname

        # Derive user_id from filename
        user_id = fname.replace('.xlsx', '').replace('.csv', '')
        # Normalize: user0001 -> user0001, user011 -> user011
        user_id = f"anon_{user_id}"

        try:
            if fname.endswith('.xlsx'):
                df_raw = load_file(fpath)
                df_extracted = extract_transactions_from_df(df_raw, user_id)
            elif fname.endswith('.csv'):
                # Pre-anonymized CSV format
                df_raw = load_anonymized_csv(fpath)
                operator = detect_operator(df_raw)
                if operator == 'Unknown':
                    operator = detect_operator_from_content(df_raw)

                df_filtered = filter_balance_messages(df_raw)
                if len(df_filtered) == 0:
                    print(f"  ⚠ {fname}: {len(df_raw)} raw → 0 balance-related messages ({user_id})")
                    continue

                records = []
                for _, row in df_filtered.iterrows():
                    text = str(row.get('contenu', ''))
                    tx_type, direction = classify_transaction(text)
                    amount, currency = extract_amount(text)
                    new_balance, bal_currency = extract_new_balance(text)
                    if currency is None and bal_currency:
                        currency = bal_currency

                    records.append({
                        'UserId': user_id,
                        'Date': row.get('date', ''),
                        'Heure': row.get('heure', ''),
                        'Operator': operator,
                        'Transaction_type': tx_type,
                        'Direction': direction,
                        'Amount': amount,
                        'Currency': currency,
                        'New_balance': new_balance,
                        'Anonymized_Content': text,  # already anonymized
                    })
                df_extracted = pd.DataFrame(records)
            else:
                continue

            if len(df_extracted) > 0:
                all_records.append(df_extracted)
                raw_count = len(df_raw) if 'df_raw' in dir() else '?'
                print(f"  ✓ {fname}: {raw_count} raw → {len(df_extracted)} transactions ({user_id})")
            else:
                print(f"  ⚠ {fname}: 0 balance-related messages ({user_id})")

        except Exception as e:
            print(f"  ✗ {fname}: ERROR - {str(e)[:80]}")

    if all_records:
        df_anon = pd.concat(all_records, ignore_index=True)
    else:
        df_anon = pd.DataFrame()

    out_path = EXTRACTED_ANON_DIR / "extracted_anonymized.csv"
    df_anon.to_csv(out_path, index=False)
    print(f"\n✅ Anonymized extraction complete: {len(df_anon)} total transactions from {len(all_records)} files")
    print(f"   Saved to: {out_path}")
    return df_anon


# ═════════════════════════════════════════════════════════════
# STEP 2: CLEANING (applied identically to both)
# ═════════════════════════════════════════════════════════════

def clean_dataset(df, label="dataset"):
    """Apply identical cleaning pipeline to a dataset."""
    print(f"\n{'─' * 40}")
    print(f"Cleaning: {label}")
    print(f"{'─' * 40}")
    print(f"  Input rows: {len(df)}")

    df = df.copy()
    stats = {}

    # ── Standardize column names ──
    df.columns = [c.strip() for c in df.columns]

    # ── Convert Date to datetime ──
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    stats['date_parse_failures'] = df['Date'].isna().sum()
    print(f"  Date parse failures: {stats['date_parse_failures']}")

    # ── Convert Heure to string time ──
    df['Heure'] = df['Heure'].astype(str).str.strip()

    # ── Combine Date + Heure into a single datetime column ──
    def combine_datetime(row):
        if pd.isna(row['Date']):
            return pd.NaT
        date_str = row['Date'].strftime('%Y-%m-%d')
        time_str = str(row['Heure']).strip()
        try:
            return pd.to_datetime(f"{date_str} {time_str}")
        except Exception:
            return row['Date']

    df['Datetime'] = df.apply(combine_datetime, axis=1)

    # ── Amount to numeric ──
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    stats['amount_missing'] = df['Amount'].isna().sum()

    # ── New_balance to numeric ──
    df['New_balance'] = pd.to_numeric(df['New_balance'], errors='coerce')
    stats['balance_missing'] = df['New_balance'].isna().sum()

    # ── Normalize categorical values ──
    df['Transaction_type'] = df['Transaction_type'].astype(str).str.lower().str.strip()
    df['Direction'] = df['Direction'].astype(str).str.upper().str.strip()
    df['Operator'] = df['Operator'].astype(str).str.strip()
    df['Currency'] = df['Currency'].astype(str).str.upper().str.strip()
    df['Currency'] = df['Currency'].replace({'FCFA': 'XAF', 'NAN': 'XAF', 'NONE': 'XAF'})

    # ── Handle missing values ──
    stats['missing_before'] = df.isnull().sum().to_dict()
    # Keep rows with valid dates and amounts where possible
    # Don't drop - just flag
    df['has_valid_amount'] = df['Amount'].notna()
    df['has_valid_date'] = df['Date'].notna()

    # ── Remove duplicates ──
    n_before = len(df)
    df = df.drop_duplicates(
        subset=['UserId', 'Date', 'Heure', 'Amount', 'Transaction_type', 'Direction'],
        keep='first'
    )
    stats['duplicates_removed'] = n_before - len(df)
    print(f"  Duplicates removed: {stats['duplicates_removed']}")

    # ── Detect outliers using IQR (DO NOT REMOVE) ──
    if df['Amount'].notna().sum() > 0:
        Q1 = df['Amount'].quantile(0.25)
        Q3 = df['Amount'].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        df['is_outlier'] = (df['Amount'] < lower) | (df['Amount'] > upper)
        stats['outlier_count'] = df['is_outlier'].sum()
        stats['iqr_lower'] = lower
        stats['iqr_upper'] = upper
        print(f"  Outliers detected (IQR): {stats['outlier_count']} (bounds: {lower:.0f} - {upper:.0f})")
    else:
        df['is_outlier'] = False
        stats['outlier_count'] = 0

    # ── Sort by user and datetime ──
    df = df.sort_values(['UserId', 'Datetime']).reset_index(drop=True)

    stats['output_rows'] = len(df)
    stats['unique_users'] = df['UserId'].nunique()
    stats['missing_after'] = df.isnull().sum().to_dict()
    print(f"  Output rows: {len(df)}")
    print(f"  Unique users: {stats['unique_users']}")

    return df, stats


# ═════════════════════════════════════════════════════════════
# STEP 4: VALIDATION
# ═════════════════════════════════════════════════════════════

def validate_datasets(df_orig, df_anon):
    """Compare two datasets for compatibility."""
    print("\n" + "=" * 60)
    print("STEP 4: DATASET VALIDATION")
    print("=" * 60)

    report = {}

    # Column consistency
    orig_cols = set(df_orig.columns)
    anon_cols = set(df_anon.columns)
    report['cols_only_original'] = orig_cols - anon_cols
    report['cols_only_anon'] = anon_cols - orig_cols
    report['cols_common'] = orig_cols & anon_cols
    print(f"\n  Columns only in original: {report['cols_only_original'] or 'None'}")
    print(f"  Columns only in anonymized: {report['cols_only_anon'] or 'None'}")

    # Amount distributions
    print("\n  Amount distributions:")
    for name, df in [("Original", df_orig), ("Anonymized", df_anon)]:
        amt = df['Amount'].dropna()
        if len(amt) > 0:
            print(f"    {name}: mean={amt.mean():.0f}, median={amt.median():.0f}, "
                  f"std={amt.std():.0f}, min={amt.min():.0f}, max={amt.max():.0f}")
            report[f'{name.lower()}_amount_stats'] = amt.describe().to_dict()
        else:
            print(f"    {name}: no valid amounts")

    # Transaction frequency
    print("\n  Transaction counts:")
    print(f"    Original: {len(df_orig)} transactions, {df_orig['UserId'].nunique()} users")
    print(f"    Anonymized: {len(df_anon)} transactions, {df_anon['UserId'].nunique()} users")

    # Transaction types comparison
    print("\n  Transaction types:")
    orig_types = df_orig['Transaction_type'].value_counts()
    anon_types = df_anon['Transaction_type'].value_counts()
    all_types = set(orig_types.index) | set(anon_types.index)
    for t in sorted(all_types):
        o = orig_types.get(t, 0)
        a = anon_types.get(t, 0)
        print(f"    {t:20s} | Original: {o:5d} | Anonymized: {a:5d}")

    # Direction comparison
    print("\n  Direction breakdown:")
    for name, df in [("Original", df_orig), ("Anonymized", df_anon)]:
        dc = df['Direction'].value_counts()
        print(f"    {name}: {dict(dc)}")

    # Operator comparison
    print("\n  Operator breakdown:")
    for name, df in [("Original", df_orig), ("Anonymized", df_anon)]:
        oc = df['Operator'].value_counts()
        print(f"    {name}: {dict(oc)}")

    report['validation_passed'] = True
    # Check for critical mismatches
    if report['cols_only_original'] or report['cols_only_anon']:
        print("\n  ⚠ Column mismatch detected — will harmonize before merging")
        report['validation_passed'] = False

    return report


# ═════════════════════════════════════════════════════════════
# STEP 6: FEATURE ENGINEERING
# ═════════════════════════════════════════════════════════════

def engineer_features(df):
    """Apply feature engineering on the merged dataset."""
    print("\n" + "=" * 60)
    print("STEP 6: FEATURE ENGINEERING")
    print("=" * 60)

    df = df.copy()

    # ── Time features ──
    df['year'] = df['Datetime'].dt.year
    df['month'] = df['Datetime'].dt.month
    df['day'] = df['Datetime'].dt.day
    df['weekday'] = df['Datetime'].dt.dayofweek  # 0=Mon, 6=Sun
    df['hour'] = df['Datetime'].dt.hour
    df['is_weekend'] = df['weekday'].isin([5, 6]).astype(int)
    print("  ✓ Time features: year, month, day, weekday, hour, is_weekend")

    # ── Behavioral features (per user, chronological) ──
    df = df.sort_values(['UserId', 'Datetime']).reset_index(drop=True)

    # net_amount: positive for IN, negative for OUT
    df['net_amount'] = df.apply(
        lambda r: r['Amount'] if r['Direction'] == 'IN'
                  else -r['Amount'] if r['Direction'] == 'OUT'
                  else 0, axis=1
    )

    # days_since_last_txn (per user)
    df['days_since_last_txn'] = df.groupby('UserId')['Datetime'].diff().dt.total_seconds() / 86400

    # monthly_txn_frequency (per user per month)
    df['year_month'] = df['Datetime'].dt.to_period('M')
    monthly_counts = df.groupby(['UserId', 'year_month']).size().reset_index(name='monthly_txn_count')
    user_monthly_avg = monthly_counts.groupby('UserId')['monthly_txn_count'].mean().reset_index(name='monthly_txn_frequency')
    df = df.merge(user_monthly_avg, on='UserId', how='left')
    print("  ✓ monthly_txn_frequency")

    # send_receive_ratio (per user, cumulative up to current point)
    def compute_send_receive_ratio(group):
        group = group.copy()
        cum_out = (group['Direction'] == 'OUT').cumsum()
        cum_in = (group['Direction'] == 'IN').cumsum()
        group['send_receive_ratio'] = cum_out / cum_in.replace(0, np.nan)
        group['send_receive_ratio'] = group['send_receive_ratio'].fillna(0)
        return group

    df = df.groupby('UserId', group_keys=False).apply(compute_send_receive_ratio)
    print("  ✓ send_receive_ratio")

    # txn_velocity_7d (number of transactions in past 7 days, per user)
    def compute_velocity_7d(group):
        group = group.copy()
        group = group.sort_values('Datetime')
        velocities = []
        datetimes = group['Datetime'].values
        for i in range(len(group)):
            current = datetimes[i]
            if pd.isna(current):
                velocities.append(np.nan)
                continue
            window_start = current - pd.Timedelta(days=7)
            count = ((datetimes[:i+1] >= window_start) & (datetimes[:i+1] <= current)).sum()
            velocities.append(count)
        group['txn_velocity_7d'] = velocities
        return group

    df = df.groupby('UserId', group_keys=False).apply(compute_velocity_7d)
    print("  ✓ txn_velocity_7d")

    # Clean up temp column
    df = df.drop(columns=['year_month'], errors='ignore')

    print(f"\n  Total features: {len(df.columns)}")
    print(f"  Feature list: {df.columns.tolist()}")

    return df


# ═════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═════════════════════════════════════════════════════════════

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  MOBILE MONEY TRANSACTION DATA PIPELINE                   ║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    # ── STEP 1: Extraction ──
    df_original_extracted = run_extraction_original()
    df_anon_extracted = run_extraction_anonymized()

    # Verify extracted outputs
    print("\n── Post-extraction verification ──")
    print(f"  Original columns: {df_original_extracted.columns.tolist()}")
    print(f"  Anonymized columns: {df_anon_extracted.columns.tolist()}")

    # ── STEP 2: Clean datasets SEPARATELY ──
    print("\n" + "=" * 60)
    print("STEP 2: CLEANING DATASETS (SEPARATELY)")
    print("=" * 60)

    df_orig_clean, orig_stats = clean_dataset(df_original_extracted, "Original")
    df_anon_clean, anon_stats = clean_dataset(df_anon_extracted, "Anonymized")

    # ── STEP 3: Add data_source label ──
    print("\n" + "=" * 60)
    print("STEP 3: ADDING DATA SOURCE LABELS")
    print("=" * 60)
    df_orig_clean['data_source'] = 'original'
    df_anon_clean['data_source'] = 'anonymized'
    print(f"  Original: {len(df_orig_clean)} rows labeled 'original'")
    print(f"  Anonymized: {len(df_anon_clean)} rows labeled 'anonymized'")

    # Save cleaned (pre-merge)
    df_orig_clean.to_csv(CLEANED_DIR / "cleaned_original.csv", index=False)
    df_anon_clean.to_csv(CLEANED_DIR / "cleaned_anonymized.csv", index=False)
    print("  ✓ Saved cleaned datasets (pre-merge)")

    # ── STEP 4: Validation ──
    validation_report = validate_datasets(df_orig_clean, df_anon_clean)

    # Harmonize columns if needed
    common_cols = list(set(df_orig_clean.columns) & set(df_anon_clean.columns))
    # Ensure both have exactly the same columns
    for col in df_orig_clean.columns:
        if col not in df_anon_clean.columns:
            df_anon_clean[col] = np.nan
    for col in df_anon_clean.columns:
        if col not in df_orig_clean.columns:
            df_orig_clean[col] = np.nan

    # ── STEP 5: Merge ──
    print("\n" + "=" * 60)
    print("STEP 5: MERGING DATASETS")
    print("=" * 60)

    df_all = pd.concat([df_orig_clean, df_anon_clean], ignore_index=True)
    print(f"  Merged dataset: {len(df_all)} rows, {df_all['UserId'].nunique()} users")
    print(f"  data_source distribution: {dict(df_all['data_source'].value_counts())}")
    print(f"  Columns: {df_all.columns.tolist()}")

    # Save cleaned merged
    cleaned_path = OUTPUT_DIR / "cleaned_transactions.csv"
    df_all.to_csv(cleaned_path, index=False)
    print(f"  ✓ Saved: {cleaned_path}")

    # ── STEP 6: Feature Engineering ──
    df_model = engineer_features(df_all)

    # ── STEP 7: Output ──
    print("\n" + "=" * 60)
    print("STEP 7: FINAL OUTPUT")
    print("=" * 60)

    model_path = OUTPUT_DIR / "model_ready_dataset.csv"
    df_model.to_csv(model_path, index=False)
    print(f"  ✓ Saved: {model_path}")

    # Summary
    print("\n" + "═" * 60)
    print("PIPELINE SUMMARY")
    print("═" * 60)
    print(f"  Total transactions: {len(df_model)}")
    print(f"  Total users: {df_model['UserId'].nunique()}")
    print(f"  Date range: {df_model['Datetime'].min()} to {df_model['Datetime'].max()}")
    print(f"  Transaction types: {dict(df_model['Transaction_type'].value_counts())}")
    print(f"  Features: {len(df_model.columns)} columns")
    print(f"\n  Output files:")
    print(f"    - {cleaned_path}")
    print(f"    - {model_path}")

    return df_model, df_orig_clean, df_anon_clean, orig_stats, anon_stats, validation_report


if __name__ == '__main__':
    df_model, df_orig, df_anon, orig_stats, anon_stats, val_report = main()
