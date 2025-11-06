from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SystemPreparerConfig:
    download_is_required: bool
    trgm_required: bool
    accept_setup_automatically: bool
