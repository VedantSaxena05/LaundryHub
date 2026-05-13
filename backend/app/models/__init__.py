# expose all models so alembic autogenerate picks them up
from app.models.user import Student, Staff
from app.models.delay import DelayReport
from app.models.hostel import BlockedDate
from app.models.laundry import LaundryBag, Slot, BagStatusLog
from app.models.rfid import RFIDTag, RFIDDevice, RFIDScanEvent
from app.models.notification import NotificationLog
from app.models.forum import ForumPost, ForumReply, ForumUpvote
from app.models.lost_found import LostFoundPost, LostFoundMatch

__all__ = [
    "Student", "Staff",
    "DelayReport",
    "BlockedDate",
    "LaundryBag", "Slot", "BagStatusLog",
    "RFIDTag", "RFIDDevice", "RFIDScanEvent",
    "NotificationLog",
    "ForumPost", "ForumReply", "ForumUpvote",
    "LostFoundPost", "LostFoundMatch",
]