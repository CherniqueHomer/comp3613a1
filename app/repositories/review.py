from sqlmodel import Session, select

from app.models.review import Review


class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_for_booking(self, booking_id: int) -> Review | None:
        statement = select(Review).where(Review.bookingID == booking_id)
        return self.db.exec(statement).first()

    def get_for_property(self, property_id: int) -> list[Review]:
        statement = (
            select(Review)
            .where(Review.propertyID == property_id)
            .order_by(Review.created_at.desc())
        )
        return list(self.db.exec(statement).all())

    def create(self, review_record: Review) -> Review:
        self.db.add(review_record)
        self.db.commit()
        self.db.refresh(review_record)
        return review_record