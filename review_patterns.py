"""
review_patterns.py

Shared regex patterns for rule-based review flags, covering BOTH English
and Bahasa Melayu phrasing. Import this in BOTH FeatureExtraction.ipynb
(label construction) and app.py (live breakdown/explainability display)
so the two sides never drift apart.

USAGE:
    from review_patterns import (
        superlative_pattern,
        detail_pattern,
        genuine_phrase_pattern,
    )

    # then use exactly as before:
    superlative_flag = 1 if superlative_pattern.search(text) else 0
"""

import re

# =========================================================================
# SUPERLATIVE / HYPE PATTERN (EN + BM)
# =========================================================================
# Original English phrases kept as-is, with Malay equivalents added.
# NOTE: Malay does not capitalize the same way English does, and word
# order/particles differ ("memang", "betul-betul", "confirm" are common
# BM/Manglish intensifiers in review text) - patterns below reflect how
# these actually appear in Shopee/Lazada-style BM reviews, not formal BM.
superlative_pattern = re.compile(
    r"\b("
    # --- English (original) ---
    r"best ever|must buy|must have|highly recommend|100% recommend|"
    r"everyone (must|should) buy|perfect product|amazing product|"
    r"buy (it )?now|don'?t miss|definitely recommend|"
    # --- Malay additions ---
    r"wajib beli|mesti beli|sangat recommend|memang recommend|"
    r"confirm puas hati|memang terbaik|terbaik sangat|cantik sangat|"
    r"sangat berbaloi|power gila|cun gila|mantap betul|"
    r"semua orang patut beli|jangan ragu beli"
    r")\b",
    flags=re.IGNORECASE
)

# =========================================================================
# DETAILED REVIEW PATTERN (GENUINE COUNTER-SIGNAL) (EN + BM)
# =========================================================================
# Original: matches a number followed by a time/quantity unit in English
# (e.g. "3 days", "2 weeks", "50%"). Malay time/quantity units added.
detail_pattern = re.compile(
    r"(\d+\s*("
    # --- English (original) ---
    r"day|days|hour|hours|week|weeks|month|months|minute|minutes|"
    r"time|times|%|percent|"
    r"size|colour|color|material|fabric|quality|durable|fit|fits|"
    r"description|packaging|delivery|shipping|battery|weight|"
    r"comfortable|comfortable|received|usage|days|weeks|month|"
    r"price|texture|design"
    # --- Malay additions ---
    r"hari|jam|minggu|bulan|minit|kali|peratus"
    r")\b)",
    flags=re.IGNORECASE
)

# =========================================================================
# SHORT-BUT-GENUINE PATTERN (GENUINE COUNTER-SIGNAL #2) (EN + BM)
# =========================================================================
genuine_phrase_pattern = re.compile(
    r"\b("
    # --- English (original) ---
    r"fast delivery|quick delivery|secure packaging|"
    r"packaging was (secure|good|intact)|"
    r"no issues( so far)?|as described|works (fine|well|as expected)|"
    r"arrived (on time|early|earlier)|good condition|easy to use|"
    r"value for (the )?money|does the job|"
    # --- Malay additions ---
    r"penghantaran cepat|delivery cepat|packaging selamat|"
    r"bungkusan selamat|tak ada masalah|takde masalah|"
    r"macam dalam gambar|sama macam gambar|berfungsi dengan baik|"
    r"sampai awal|sampai cepat|keadaan baik|senang nak guna|"
    r"berbaloi dengan harga|memang berbaloi"
    r")\b",
    flags=re.IGNORECASE
)
