from sqlalchemy.orm import Session

from db.annotation.annotation import Annotation


def get_annotation(db: Session, annotation_id: int) -> Annotation:
    return db.query(Annotation).filter_by(id=annotation_id, is_deleted=0).first()
