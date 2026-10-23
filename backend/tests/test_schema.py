from sqlalchemy import create_engine, inspect

from app.core.database import Base
from app.init_db import Detection


def test_initialization_registers_and_creates_detection_table():
    assert "detections" in Base.metadata.tables
    assert Detection.__tablename__ == "detections"

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    assert "detections" in inspect(engine).get_table_names()
    engine.dispose()
