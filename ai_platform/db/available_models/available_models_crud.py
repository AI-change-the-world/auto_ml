from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from db.available_models.available_models import AvailableModel


def get_available_model(db: Session, model_id: int) -> Optional[AvailableModel]:
    return (
        db.query(AvailableModel)
        .filter_by(available_model_id=model_id, is_deleted=0)
        .first()
    )


def get_available_models_in_id_list(
    db: Session, model_ids: List[int]
) -> List[AvailableModel]:
    return (
        db.query(AvailableModel)
        .filter(
            AvailableModel.available_model_id.in_(model_ids),
            AvailableModel.is_deleted == 0,
        )
        .all()
    )


def update_available_model(
    db: Session, model_id: int, updates: Dict[str, Any]
) -> Optional[AvailableModel]:
    model = (
        db.query(AvailableModel)
        .filter_by(available_model_id=model_id, is_deleted=0)
        .first()
    )
    if not model:
        return None

    for key, value in updates.items():
        if hasattr(model, key):
            setattr(model, key, value)

    db.commit()
    db.refresh(model)
    return model


def create_available_model(db: Session, model_data: Dict[str, Any]) -> AvailableModel:
    model = AvailableModel(**model_data)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def delete_available_model(db: Session, model_id: int) -> bool:
    model = (
        db.query(AvailableModel)
        .filter_by(available_model_id=model_id, is_deleted=0)
        .first()
    )
    if not model:
        return False
    model.is_deleted = 1
    db.commit()
    return True
