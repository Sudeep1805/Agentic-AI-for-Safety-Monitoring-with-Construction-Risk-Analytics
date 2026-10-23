"""Create missing initial tables; never drops or replaces existing tables."""
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.database import Base, make_engine
from app.models.detection import Detection  # noqa: F401 -- registers model metadata
from app.models.project import Project  # noqa: F401 -- registers model metadata
from app.models.upload import SiteUpload  # noqa: F401 -- registers model metadata
from app.models.session import UserSession  # noqa: F401
from app.models.user import User  # noqa: F401


def main():
    engine = make_engine(get_settings())
    try:
        Base.metadata.create_all(engine)
        print("Initial upload schema is ready. Existing tables were preserved.")
    except SQLAlchemyError:
        raise SystemExit("Cannot initialize schema. Check MySQL, backend/.env and CREATE privileges.") from None
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
