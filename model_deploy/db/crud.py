from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from db.models import AvailableModel, Deployment


def get_available_model(db: Session, model_id: int) -> Optional[AvailableModel]:
    return (
        db.query(AvailableModel)
        .filter_by(available_model_id=model_id, is_deleted=0)
        .first()
    )


def get_deployment(db: Session, deployment_id: int) -> Optional[Deployment]:
    return db.query(Deployment).filter_by(deployment_id=deployment_id).first()


def get_deployment_by_model(db: Session, model_id: int) -> Optional[Deployment]:
    return db.query(Deployment).filter_by(model_id=model_id, status=1).first()


def get_all_deployments(db: Session) -> List[Deployment]:
    return db.query(Deployment).order_by(Deployment.created_at.desc()).all()


def create_deployment(db: Session, deployment_data: Dict[str, Any]) -> Deployment:
    deployment = Deployment(**deployment_data)
    db.add(deployment)
    db.commit()
    db.refresh(deployment)
    return deployment


def update_deployment(
    db: Session, deployment_id: int, updates: Dict[str, Any]
) -> Optional[Deployment]:
    deployment = db.query(Deployment).filter_by(
        deployment_id=deployment_id).first()
    if not deployment:
        return None
    for key, value in updates.items():
        if hasattr(deployment, key):
            setattr(deployment, key, value)
    db.commit()
    db.refresh(deployment)
    return deployment


def delete_deployment(db: Session, deployment_id: int) -> bool:
    deployment = db.query(Deployment).filter_by(
        deployment_id=deployment_id).first()
    if not deployment:
        return False
    db.delete(deployment)
    db.commit()
    return True
