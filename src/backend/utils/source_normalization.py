from sqlalchemy import func

UNKNOWN_SOURCE_LABEL = "Unknown source"


def clean_source_value(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def normalized_source_label(
    source_name: str | None,
    source_id: str | None,
) -> str:
    return (
        clean_source_value(source_name)
        or clean_source_value(source_id)
        or UNKNOWN_SOURCE_LABEL
    )


def source_label_expression(model):
    return func.coalesce(
        func.nullif(func.trim(model.source_name), ""),
        func.nullif(func.trim(model.source_id), ""),
        UNKNOWN_SOURCE_LABEL,
    )


def source_id_expression(model):
    return func.nullif(func.trim(model.source_id), "")
