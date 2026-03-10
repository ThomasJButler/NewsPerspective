from sqlalchemy import func

UNKNOWN_SOURCE_LABEL = "Unknown source"


def clean_source_value(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def source_label_expression(model):
    return func.coalesce(
        func.nullif(func.trim(model.source_name), ""),
        func.nullif(func.trim(model.source_id), ""),
        UNKNOWN_SOURCE_LABEL,
    )


def source_id_expression(model):
    return func.nullif(func.trim(model.source_id), "")
