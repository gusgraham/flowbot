from database import engine
from sqlmodel import Session, select
from domain.monitor import Monitor

with Session(engine) as session:
    monitors = session.exec(select(Monitor)).all()
    print(f'Found {len(monitors)} monitors')
    for m in monitors:
        session.delete(m)
    session.commit()
    print('All monitors deleted')
