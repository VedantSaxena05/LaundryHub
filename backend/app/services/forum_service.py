"""
Forum service.

Handles:
- Post create / list / get / update / delete
- Reply threads (nested via parent_reply_id)
- Upvotes with duplicate protection (DB unique constraint is the final guard)
- Pin toggling (admin only, enforced at router level)
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.forum import ForumPost, ForumReply, ForumUpvote
from app.utils.exceptions import NotFoundError, ConflictError, ForbiddenError


# ── Posts ─────────────────────────────────────────────────────────────────

def create_post(
    db: Session,
    author_id: UUID,
    category: str,
    title: str,
    body: str,
    is_anonymous: bool = False,
    swap_from_date=None,
    swap_to_date=None,
) -> ForumPost:
    post = ForumPost(
        author_id=author_id,
        category=category,
        title=title,
        body=body,
        is_anonymous=is_anonymous,
        swap_from_date=swap_from_date,
        swap_to_date=swap_to_date,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def list_posts(
    db: Session,
    category: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> List[ForumPost]:
    q = db.query(ForumPost)
    if category:
        q = q.filter(ForumPost.category == category)
    # Pinned posts float to the top, then by newest
    q = q.order_by(ForumPost.is_pinned.desc(), ForumPost.created_at.desc())
    offset = (page - 1) * page_size
    return q.offset(offset).limit(page_size).all()


def get_post(db: Session, post_id: UUID) -> ForumPost:
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise NotFoundError("Post not found")
    return post


def update_post(
    db: Session,
    post_id: UUID,
    author_id: UUID,
    title: Optional[str],
    body: Optional[str],
) -> ForumPost:
    post = get_post(db, post_id)
    if post.author_id != author_id:
        raise ForbiddenError("You can only edit your own posts")
    if title:
        post.title = title
    if body:
        post.body = body
    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post_id: UUID, requester_id: UUID, is_admin: bool = False) -> None:
    post = get_post(db, post_id)
    if not is_admin and post.author_id != requester_id:
        raise ForbiddenError("You can only delete your own posts")
    db.delete(post)
    db.commit()


def pin_post(db: Session, post_id: UUID) -> ForumPost:
    post = get_post(db, post_id)
    post.is_pinned = not post.is_pinned
    db.commit()
    db.refresh(post)
    return post


# ── Replies ───────────────────────────────────────────────────────────────

def create_reply(
    db: Session,
    post_id: UUID,
    author_id: UUID,
    body: str,
    is_anonymous: bool = False,
    parent_reply_id: Optional[UUID] = None,
) -> ForumReply:
    # Confirm post exists
    get_post(db, post_id)
    reply = ForumReply(
        post_id=post_id,
        author_id=author_id,
        body=body,
        is_anonymous=is_anonymous,
        parent_reply_id=parent_reply_id,
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply


def list_replies(db: Session, post_id: UUID) -> List[ForumReply]:
    return (
        db.query(ForumReply)
        .filter(ForumReply.post_id == post_id)
        .order_by(ForumReply.created_at.asc())
        .all()
    )


# ── Upvotes ───────────────────────────────────────────────────────────────

def upvote_post(db: Session, student_id: UUID, post_id: UUID) -> dict:
    existing = db.query(ForumUpvote).filter(
        ForumUpvote.student_id == student_id,
        ForumUpvote.post_id == post_id,
    ).first()

    post = get_post(db, post_id)

    if existing:
        # Toggle off (un-upvote)
        db.delete(existing)
        post.upvote_count = max(0, post.upvote_count - 1)
        db.commit()
        return {"action": "removed", "upvote_count": post.upvote_count}

    upvote = ForumUpvote(student_id=student_id, post_id=post_id)
    db.add(upvote)
    post.upvote_count += 1
    db.commit()
    return {"action": "added", "upvote_count": post.upvote_count}


def upvote_reply(db: Session, student_id: UUID, reply_id: UUID) -> dict:
    reply = db.query(ForumReply).filter(ForumReply.id == reply_id).first()
    if not reply:
        raise NotFoundError("Reply not found")

    existing = db.query(ForumUpvote).filter(
        ForumUpvote.student_id == student_id,
        ForumUpvote.reply_id == reply_id,
    ).first()

    if existing:
        db.delete(existing)
        reply.upvote_count = max(0, reply.upvote_count - 1)
        db.commit()
        return {"action": "removed", "upvote_count": reply.upvote_count}

    upvote = ForumUpvote(student_id=student_id, reply_id=reply_id)
    db.add(upvote)
    reply.upvote_count += 1
    db.commit()
    return {"action": "added", "upvote_count": reply.upvote_count}