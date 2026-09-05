from dataclasses import dataclass, field


@dataclass(frozen=True)
class AppConfig:
    APP_NAME: str = "SmartCSV Analyst"
    APP_TAGLINE: str = "Interactive CSV Analysis & Data Exploration"
    VERSION: str = "1.0.0"
    MAX_UPLOAD_SIZE_MB: int = 200
    MAX_SCATTER_POINTS: int = 50_000
    LARGE_DATASET_THRESHOLD: int = 100_000
    SAMPLE_SIZE_FOR_VIZ: int = 50_000
    OUTLIER_IQR_MULTIPLIER: float = 1.5
    OUTLIER_ZSCORE_THRESHOLD: float = 3.0
    HIGH_MISSING_THRESHOLD: float = 0.5
    HIGH_CARDINALITY_THRESHOLD: int = 100
    CONSTANT_COLUMN_NUNIQUE: int = 1
    CORRELATION_STRONG_THRESHOLD: float = 0.7
    TREND_MIN_POINTS: int = 10
    SUPPORTED_ENCODINGS: tuple = ("utf-8", "latin-1", "cp1252", "iso-8859-1", "utf-16", "ascii")
    COLOR_PALETTE: list = field(
        default_factory=lambda: [
            "#2563EB",
            "#10B981",
            "#F59E0B",
            "#EF4444",
            "#8B5CF6",
            "#EC4899",
            "#06B6D4",
            "#84CC16",
        ]
    )
    COLORBLIND_PALETTE: list = field(
        default_factory=lambda: [
            "#0072B2",
            "#E69F00",
            "#009E73",
            "#CC79A7",
            "#56B4E9",
            "#D55E00",
            "#F0E442",
            "#000000",
        ]
    )


config = AppConfig()
