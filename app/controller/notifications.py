from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"],
)


@router.get("/")
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch all notifications scoped to the authenticated user.
    """
    items = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )

    unread_count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.read == False
        )
        .count()
    )

    return {
        "success": True,
        "unread_count": unread_count,
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "read": n.read,
                "project_id": n.project_id,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in items
        ],
    }


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark a specific notification as read.
    """
    notif = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
        .first()
    )

    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")

    notif.read = True
    db.commit()

    return {"success": True, "message": "Notification marked as read."}


@router.post("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark all unread notifications as read for current user.
    """
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read == False
    ).update({"read": True})
    db.commit()

    return {"success": True, "message": "All notifications marked as read."}
