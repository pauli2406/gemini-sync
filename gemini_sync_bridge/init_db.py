from gemini_sync_bridge.db import engine
from gemini_sync_bridge.models import Base


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
