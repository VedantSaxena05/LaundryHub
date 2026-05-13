"""
Lost & Found service.

Keyword match engine:
  - Tokenises item_description + color into lowercase word sets
  - Computes Jaccard similarity: |intersection| / |union|
  - Any pair scoring >= MATCH_THRESHOLD is stored as a LostFoundMatch
  - On creation of a new post, we scan all unresolved posts of the opposite type
"""
import re
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.lost_found import LostFoundPost, LostFoundMatch
from app.utils.exceptions import NotFoundError, ForbiddenError

MATCH_THRESHOLD = 0.25      # tune as needed


# ── Tokeniser ─────────────────────────────────────────────────────────────

def _tokenise(text: str) -> set[str]:
    """Lowercase alphanumeric tokens, min length 3, stopwords stripped."""
    STOPWORDS = {"the", "and", "was", "with", "for", "from", "have", "that", "this"}
    tokens = set(re.findall(r"[a-z0-9]{3,}", text.lower()))
    return tokens - STOPWORDS


def _score(post_a: LostFoundPost, post_b: LostFoundPost) -> float:
    text_a = f"{post_a.item_description} {post_a.color or ''}"
    text_b = f"{post_b.item_description} {post_b.color or ''}"
    t_a = _tokenise(text_a)
    t_b = _tokenise(text_b)
    if not t_a or not t_b:
        return 0.0
    return len(t_a & t_b) / len(t_a | t_b)


# ── CRUD ──────────────────────────────────────────────────────────────────

def create_post(
    db: Session,
    student_id: UUID,
    post_type: str,
    item_description: str,
    color: Optional[str],
    photo_url: Optional[str],
    last_seen_location: Optional[str],
) -> LostFoundPost:
    post = LostFoundPost(
        posted_by=student_id,
        post_type=post_type,
        item_description=item_description,
        color=color,
        photo_url=photo_url,
        last_seen_location=last_seen_location,
    )
    db.add(post)
    db.flush()   # get post.id before running match scan

    _run_match_scan(db, post)

    db.commit()
    db.refresh(post)
    return post


def list_posts(
    db: Session,
    post_type: Optional[str] = None,
    resolved: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> List[LostFoundPost]:
    q = db.query(LostFoundPost).filter(LostFoundPost.is_resolved == resolved)
    if post_type:
        q = q.filter(LostFoundPost.post_type == post_type)
    offset = (page - 1) * page_size
    return q.order_by(LostFoundPost.created_at.desc()).offset(offset).limit(page_size).all()


def get_post(db: Session, post_id: UUID) -> LostFoundPost:
    post = db.query(LostFoundPost).filter(LostFoundPost.id == post_id).first()
    if not post:
        raise NotFoundError("Post not found")
    return post


def resolve_post(db: Session, post_id: UUID, requester_id: UUID) -> LostFoundPost:
    post = get_post(db, post_id)
    if post.posted_by != requester_id:
        raise ForbiddenError("Only the original poster can mark as resolved")
    post.is_resolved = True
    db.commit()
    db.refresh(post)
    return post


def list_matches(db: Session, post_id: UUID) -> List[LostFoundMatch]:
    return (
        db.query(LostFoundMatch)
        .filter(
            (LostFoundMatch.lost_post_id == post_id) |
            (LostFoundMatch.found_post_id == post_id)
        )
        .order_by(LostFoundMatch.match_score.desc())
        .all()
    )


# ── Match engine ──────────────────────────────────────────────────────────

def _run_match_scan(db: Session, new_post: LostFoundPost) -> None:
    """
    Compare new_post against all unresolved posts of the opposite type.
    Write a LostFoundMatch row for every pair that clears the threshold.
    Duplicate pairs are silently skipped.
    """
    opposite = "found" if new_post.post_type == "lost" else "lost"
    candidates = (
        db.query(LostFoundPost)
        .filter(
            LostFoundPost.post_type == opposite,
            LostFoundPost.is_resolved == False,
        )
        .all()
    )

    for candidate in candidates:
        score = _score(new_post, candidate)
        if score < MATCH_THRESHOLD:
            continue

        # Determine which is lost, which is found
        if new_post.post_type == "lost":
            lost_id, found_id = new_post.id, candidate.id
        else:
            lost_id, found_id = candidate.id, new_post.id

        # Avoid duplicate match rows
        already = db.query(LostFoundMatch).filter(
            LostFoundMatch.lost_post_id == lost_id,
            LostFoundMatch.found_post_id == found_id,
        ).first()
        if already:
            continue

        match = LostFoundMatch(
            lost_post_id=lost_id,
            found_post_id=found_id,
            match_score=score,
        )
        db.add(match)


def run_full_match_scan(db: Session) -> int:
    """
    Admin utility: re-run match scan across all unresolved posts.
    Returns number of new matches written.
    """
    lost_posts = db.query(LostFoundPost).filter(
        LostFoundPost.post_type == "lost",
        LostFoundPost.is_resolved == False,
    ).all()

    new_matches = 0
    for post in lost_posts:
        before = db.query(LostFoundMatch).count()
        _run_match_scan(db, post)
        after = db.query(LostFoundMatch).count()
        new_matches += after - before

    db.commit()
    return new_matches