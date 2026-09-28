import pandas as pd
from keyword_quality import add_keyword_quality


def _normalize_raw_columns(df):
    """Support both legacy project schema and Ubersuggest-style raw CSVs."""
    rename_map = {
        "Keywords": "Keyword",
        "Keyword": "Keyword",
        "Est. Visits": "Estimated Visits",
        "Estimated Visits": "Estimated Visits",
        "Seo Difficulty": "SEO Difficulty",
        "SEO Difficulty": "SEO Difficulty",
        "Ranking Url": "Ranking URL",
        "Ranking URL": "Ranking URL",
    }

    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if "Keyword" not in df.columns:
        df["Keyword"] = ""

    for column in ["Volume", "Position", "Estimated Visits", "CPC", "Paid Difficulty", "SEO Difficulty"]:
        if column not in df.columns:
            df[column] = 0

    return df


def prepare_features(df):

    df = _normalize_raw_columns(df)

    # ==========================================
    # 1. CPC Cleaning
    # ==========================================

    df["CPC"] = (
        df["CPC"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )

    df["CPC"] = pd.to_numeric(
        df["CPC"],
        errors="coerce"
    )

    df["CPC"] = df["CPC"].fillna(0)


    # ==========================================
    # 2. Missing Estimated Visits
    # ==========================================

    df["Estimated Visits"] = pd.to_numeric(
        df["Estimated Visits"],
        errors="coerce"
    )

    df["Estimated Visits"] = (
        df["Estimated Visits"]
        .fillna(0)
    )


    # ==========================================
    # 3. Volume Score
    # ==========================================

    df["Volume_Score"] = (
        df["Volume"]
        .rank(pct=True)
        * 100
    )


    # ==========================================
    # 4. Estimated Visits Score
    # ==========================================

    df["Visits_Score"] = (
        df["Estimated Visits"]
        .rank(pct=True)
        * 100
    )


    # ==========================================
    # 5. Position Score
    # ==========================================
    # Lower position = better

    df["Position_Score"] = (
        1 - df["Position"].rank(pct=True)
    ) * 100


    # ==========================================
    # 6. CPC Score
    # ==========================================

    df["CPC_Score"] = (
        df["CPC"]
        .rank(pct=True)
        * 100
    )


    # ==========================================
    # 7. SEO Opportunity
    # ==========================================
    # Lower difficulty = better opportunity

    df["SEO_Opportunity"] = (
        1 - df["SEO Difficulty"].rank(pct=True)
    ) * 100


    # ==========================================
    # 8. Paid Opportunity
    # ==========================================
    # Lower difficulty = better opportunity

    df["Paid_Opportunity"] = (
        1 - df["Paid Difficulty"].rank(pct=True)
    ) * 100


    # ==========================================
    # 9. Keyword Quality
    # ==========================================

    df = add_keyword_quality(df)


    # ==========================================
    # 10. Final Safety Check
    # ==========================================

    numeric_columns = [
        "Volume_Score",
        "Visits_Score",
        "Position_Score",
        "CPC_Score",
        "SEO_Opportunity",
        "Paid_Opportunity",
        "Keyword_Quality_Score"
    ]

    for column in numeric_columns:

        df[column] = (
            pd.to_numeric(
                df[column],
                errors="coerce"
            )
            .replace(
                [float("inf"), float("-inf")],
                0
            )
            .fillna(0)
        )


    return df
