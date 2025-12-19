from sqlmodel import Session, select
from database import engine
from domain.interim import Interim, InterimReview

def check_dates():
    with Session(engine) as session:
        interims = session.exec(select(Interim)).all()
        print(f"Found {len(interims)} interims.")
        
        for interim in interims:
            print(f"Interim ID: {interim.id}")
            print(f"  Start: {interim.start_date}")
            print(f"  End:   {interim.end_date}")
            reviews_count = len(session.exec(select(InterimReview).where(InterimReview.interim_id == interim.id)).all())
            print(f"  Reviews: {reviews_count}")

if __name__ == "__main__":
    check_dates()
