from sqlalchemy.orm import Session

from db.dataset.dataset import Dataset


def get_dataset(db: Session, dataset_id: int) -> Dataset:
    return db.query(Dataset).filter_by(id=dataset_id, is_deleted=0).first()
