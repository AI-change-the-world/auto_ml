from sqlalchemy.orm import Session

from db.tool_model.tool_model import ToolModel


def get_tool_model(db: Session, tool_model_id: int) -> ToolModel | None:
    return db.query(ToolModel).filter_by(id=tool_model_id, is_deleted=0).first()
