"""
malay_sentiment.py

Extends VADER's English-only sentiment lexicon with common Bahasa
Melayu (BM) sentiment words and negation terms, so that mixed-language
(BM + English) product reviews get sensible sentiment scores instead of
BM words being silently treated as neutral.

USAGE (both in FeatureExtraction.ipynb AND app.py - must be identical
on both sides, otherwise training and live prediction will disagree):

    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    from malay_sentiment import apply_malay_lexicon

    vader_analyzer = SentimentIntensityAnalyzer()
    apply_malay_lexicon(vader_analyzer)   # <-- call this ONCE after creating the analyzer

    # then use vader_analyzer.polarity_scores(text) as normal

IMPORTANT - SCOPE AND LIMITATIONS (be upfront about this in your report):
- This is a lexicon-based patch, not a trained BM sentiment model. It
  covers common review vocabulary (slang included) seen in Shopee/Lazada-
  style reviews, but it is NOT exhaustive. Rare/dialectal BM words will
  still be scored as neutral.
- VADER's own negation handling (flipping a nearby positive word negative,
  e.g. "not good") is pattern-based and tuned for English word order. We
  extend its negation word list with BM negators (tak, tidak, bukan,
  jangan, takde) but did NOT re-validate that VADER's negation-scope
  logic (how many words ahead/behind it looks) works identically well
  for BM sentence structure. Spot-check a sample of BM reviews manually
  before trusting this in production.
- This file does NOT translate text. It only adds vocabulary scores.
  Grammar, sarcasm, and context outside VADER's existing mechanism are
  unchanged.
"""

# =========================================================================
# BAHASA MELAYU SENTIMENT LEXICON
# =========================================================================
# Scores follow VADER's own convention: roughly -4 (extremely negative)
# to +4 (extremely positive), where +/-1.5 to 2.5 is a "normal" strong
# sentiment word and +/-3 to 4 is reserved for very intense words.
# These were hand-picked for e-commerce review context (Shopee/Lazada
# style) - NOT a general-purpose BM sentiment dictionary.
#
# NOTE: keys should be lowercase, matching how clean_review() normalizes
# text. Do not include words already removed by your stopword list
# (malay_stopwords) - if a sentiment word ends up in your stopword set,
# it will never reach VADER and adding it here has no effect. Cross-check
# against malay_stopwords in CleanAll.ipynb if you extend this list.
MALAY_SENTIMENT_LEXICON = {
    # ---------- strong positive ----------
    "bagus": 2.5,
    "cantik": 2.2,
    "power": 2.3,          # slang: "power gila" = excellent
    "terbaik": 2.8,
    "puas": 2.0,
    "cun": 2.0,            # slang, often describes product/appearance
    "mantap": 2.4,
    "memuaskan": 2.3,
    "berbaloi": 2.2,       # "worth it"
    "laju": 1.5,           # "fast" (delivery), mildly positive in review context
    "selesa": 1.8,         # "comfortable"
    "original": 1.2,       # reassurance word in this domain ("ini original")
    "tulen": 1.5,          # "genuine/authentic"
    "syok": 2.0,           # slang, positive

    # ---------- mild positive ----------
    "ok": 1.0,
    "okay": 1.0,
    "lawa": 1.8,           # "pretty/nice" (esp. for clothing/appearance)
    "sesuai": 1.3,
    "senang": 1.2,         # "easy" / "comfortable" depending on context
    "cepat": 1.0,          # "fast" - mildly positive, context-dependent (also neutral in some uses)

    # ---------- strong negative ----------
    "teruk": -2.5,
    "hampas": -2.7,        # slang: very bad/disappointing
    "rosak": -2.3,         # "broken/damaged"
    "menyesal": -2.4,      # "regret"
    "tipu": -3.0,          # "scam/cheat" - strong, common in fake/scam review context
    "scam": -3.0,
    "palsu": -2.6,         # "fake/counterfeit"
    "mengecewakan": -2.5,  # "disappointing"
    "lambat": -1.5,        # "slow" (delivery) - negative in review context
    "lembap": -1.3,        # "slow/sluggish" (slang variant)
    "bocor": -2.0,         # "leaking" (common defect complaint)
    "pecah": -2.2,         # "broken/cracked"
    "kecewa": -2.3,        # "disappointed"
    "x best": -1.8,        # common SMS-style negation slang ("not the best")

    # ---------- mild negative ----------
    "kecil": -0.5,         # "too small" - mild, often size-complaint context
    "susah": -1.2,         # "difficult"
    "biasa": -0.3,         # "just average/ordinary" - mildly negative in review tone
    "nipis": -0.8,         # "thin" (material complaint, e.g. fabric quality)
}

# =========================================================================
# BAHASA MELAYU NEGATION WORDS
# =========================================================================
# VADER flips/dampens sentiment for words that follow a negation term
# (e.g. "not good" weakens "good"). VADER's default negation list is
# English-only ("not", "never", "no", etc). These BM equivalents are
# added so phrases like "tak bagus" / "tidak puas hati" are recognized
# as negated rather than scoring "bagus"/"puas" at full positive
# strength.
MALAY_NEGATION_WORDS = {
    "tak",
    "tidak",
    "bukan",
    "jangan",
    "takde",     # colloquial "tak ada"
    "tak ada",
    "x",         # common SMS-style shorthand for "tak" (e.g. "x best", "x bagus")
}


def apply_malay_lexicon(analyzer):
    """
    Mutates a VADER SentimentIntensityAnalyzer in-place: merges the BM
    sentiment lexicon into its existing (English) lexicon, and extends
    its negation word set with BM negators.

    Call this exactly once right after creating the analyzer, and make
    sure both FeatureExtraction.ipynb (training) and app.py (live
    prediction) call it the same way - otherwise training and live
    scoring will diverge.
    """
    # Merge BM words into VADER's existing lexicon dict. VADER's lexicon
    # is a plain dict of {word: mean_sentiment_score}, so this is a
    # straightforward dict update - no special API needed.
    analyzer.lexicon.update(MALAY_SENTIMENT_LEXICON)

    # VADER's negation check lives in vaderSentiment.vaderSentiment as a
    # module-level constant NEGATE (a Python set/list of negation words).
    # We extend it directly so the negation-scope logic (which already
    # exists in VADER's code) also recognizes BM negators.
    try:
        from vaderSentiment import vaderSentiment as _vs_module
        if hasattr(_vs_module, "NEGATE"):
            _vs_module.NEGATE = set(_vs_module.NEGATE) | MALAY_NEGATION_WORDS
        else:
            print("WARNING: vaderSentiment.NEGATE constant not found in this "
                  "version of the library - BM negation words were NOT added. "
                  "Sentiment scoring will still work, but phrases like 'tak "
                  "bagus' may score as positive instead of negative. Check "
                  "your installed vaderSentiment version.")
    except ImportError:
        print("WARNING: could not import vaderSentiment.vaderSentiment to "
              "extend negation list. BM lexicon words were still added, but "
              "BM negation ('tak', 'tidak', etc) will not be recognized.")

    return analyzer
