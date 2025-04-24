# Central config so magic numbers live in one place.
# Edit env vars (preferred) or change defaults here.
import os

# keep only the last N verbatim messages in the prompt
MAX_VISIBLE_TURNS = int(os.getenv("MAX_VISIBLE_TURNS", "25"))

# summarise history every M turns
SUMMARY_HORIZON   = int(os.getenv("SUMMARY_HORIZON", "50"))

# model used for summarisation (can be smaller/cheaper than main one)
SUMMARISE_MODEL   = os.getenv("SUMMARISE_MODEL", "gpt-4o-mini") 