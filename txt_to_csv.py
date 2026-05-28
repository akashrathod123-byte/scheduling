"""
Convert a large whitespace/tab-delimited txt file to CSV.
Streams line-by-line so it handles 9M+ rows without loading into memory.
"""
import csv
import sys
import time

INPUT_PATH  = r"P:\Capacity Management\Management\Akash\B2B\contact.txt"
OUTPUT_PATH = r"P:\Capacity Management\Management\Akash\B2B\contact.csv"

# Pick ONE of these depending on what separates your columns:
#   "\t"     -> tab-delimited
#   None     -> any run of whitespace (spaces and/or tabs)
#   ","      -> already comma-separated
#   "|"      -> pipe-delimited
DELIMITER = None        # change to "\t" if your file is tab-delimited

# If your file has a header row, set to True. Otherwise leave False.
HAS_HEADER = False

# Optional column names if your file has no header (leave [] to skip).
COLUMN_NAMES = []       # e.g. ["name", "id1", "id2", "id3", ...]


def main():
    start = time.time()
    rows_written = 0

    # newline="" is required for csv on Windows to avoid blank lines.
    # encoding="latin-1" is forgiving of stray non-UTF8 bytes; switch to
    # "utf-8" if you know the file is clean UTF-8.
    with open(INPUT_PATH, "r", encoding="latin-1", errors="replace") as fin, \
         open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as fout:

        writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)

        if COLUMN_NAMES:
            writer.writerow(COLUMN_NAMES)

        for i, line in enumerate(fin, start=1):
            line = line.rstrip("\r\n")
            if not line:
                continue

            if i == 1 and HAS_HEADER and not COLUMN_NAMES:
                # Pass header through as-is
                fields = line.split(DELIMITER) if DELIMITER else line.split()
                writer.writerow(fields)
                continue

            if DELIMITER is None:
                fields = line.split()           # any whitespace
            else:
                fields = line.split(DELIMITER)  # specific delimiter

            writer.writerow(fields)
            rows_written += 1

            if rows_written % 500_000 == 0:
                print(f"  {rows_written:,} rows written...", flush=True)

    elapsed = time.time() - start
    print(f"\nDone. Wrote {rows_written:,} rows to {OUTPUT_PATH}")
    print(f"Elapsed: {elapsed:,.1f} seconds")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"ERROR: file not found -> {e.filename}", file=sys.stderr)
        sys.exit(1)
