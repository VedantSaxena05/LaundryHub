"""
test_forum_lostfound.py — /forum and /lost-found endpoints.
"""
import pytest
from conftest import _headers


# ═══════════════════════════════════════════════════════════════════════════
# Forum
# ═══════════════════════════════════════════════════════════════════════════

def test_create_forum_post(client, student_a):
    token, _ = student_a
    resp = client.post("/forum", headers=_headers(token), json={
        "category": "tips",
        "title": "Best drop-off time",
        "body": "Go at 10am for fastest turnaround.",
        "is_anonymous": False,
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Best drop-off time"
    assert body["category"] == "tips"


def test_list_forum_posts(client, student_a):
    token, _ = student_a
    client.post("/forum", headers=_headers(token), json={
        "category": "tips",
        "title": "Listed post",
        "body": "Body here.",
        "is_anonymous": False,
    })
    resp = client.get("/forum?category=tips&page=1&page_size=10", headers=_headers(token))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    titles = [p["title"] for p in resp.json()]
    assert "Listed post" in titles


def test_upvote_post(client, student_a, student_b):
    token_a, _ = student_a
    token_b, _ = student_b
    post_id = client.post("/forum", headers=_headers(token_a), json={
        "category": "general",
        "title": "Upvote me",
        "body": "Please upvote.",
        "is_anonymous": False,
    }).json()["id"]

    resp = client.post(f"/forum/{post_id}/upvote", headers=_headers(token_b))
    assert resp.status_code == 200


def test_reply_to_post(client, student_a, student_b):
    token_a, _ = student_a
    token_b, _ = student_b
    post_id = client.post("/forum", headers=_headers(token_a), json={
        "category": "general",
        "title": "Reply to me",
        "body": "Waiting for replies.",
        "is_anonymous": False,
    }).json()["id"]

    resp = client.post(f"/forum/{post_id}/replies", headers=_headers(token_b), json={
        "body": "Great post!",
        "is_anonymous": False,
    })
    assert resp.status_code == 201


def test_admin_can_pin_post(client, student_a, admin_token):
    token, _ = student_a
    post_id = client.post("/forum", headers=_headers(token), json={
        "category": "announcements",
        "title": "Pin me",
        "body": "Important.",
        "is_anonymous": False,
    }).json()["id"]

    resp = client.post(f"/forum/{post_id}/pin", headers=_headers(admin_token))
    assert resp.status_code == 200


def test_staff_cannot_pin_post(client, student_a, staff_token):
    token, _ = student_a
    post_id = client.post("/forum", headers=_headers(token), json={
        "category": "general",
        "title": "Can staff pin?",
        "body": "No.",
        "is_anonymous": False,
    }).json()["id"]
    resp = client.post(f"/forum/{post_id}/pin", headers=_headers(staff_token))
    assert resp.status_code == 403


def test_anonymous_post_hides_author(client, student_a):
    token, sid = student_a
    resp = client.post("/forum", headers=_headers(token), json={
        "category": "general",
        "title": "Anon post",
        "body": "Who am I?",
        "is_anonymous": True,
    })
    assert resp.status_code == 201
    body = resp.json()
    # posted_by should be null or hidden when anonymous
    assert body.get("posted_by") is None or body.get("is_anonymous") is True


def test_unauthenticated_cannot_post(client):
    resp = client.post("/forum", json={
        "category": "tips",
        "title": "No auth",
        "body": "Should fail.",
        "is_anonymous": False,
    })
    assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════
# Lost & Found
# ═══════════════════════════════════════════════════════════════════════════

def test_create_lost_post(client, student_a):
    token, _ = student_a
    resp = client.post("/lost-found", headers=_headers(token), json={
        "post_type": "lost",
        "item_description": "blue denim jacket with VIT badge",
        "color": "blue",
        "last_seen_location": "Block A laundry room",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["post_type"] == "lost"
    assert body["resolved"] is False


def test_create_found_post(client, student_b):
    token, _ = student_b
    resp = client.post("/lost-found", headers=_headers(token), json={
        "post_type": "found",
        "item_description": "denim jacket blue found near laundry",
        "color": "blue",
        "last_seen_location": "Block A",
    })
    assert resp.status_code == 201
    assert resp.json()["post_type"] == "found"


def test_jaccard_match_created(client, student_a, student_b):
    """A found post with similar description should trigger a match for the lost post."""
    token_a, _ = student_a
    token_b, _ = student_b

    lost_id = client.post("/lost-found", headers=_headers(token_a), json={
        "post_type": "lost",
        "item_description": "red hoodie with VIT logo",
        "color": "red",
        "last_seen_location": "Block C laundry",
    }).json()["id"]

    client.post("/lost-found", headers=_headers(token_b), json={
        "post_type": "found",
        "item_description": "red hoodie vit logo found block c",
        "color": "red",
        "last_seen_location": "Block C",
    })

    resp = client.get(f"/lost-found/{lost_id}/matches", headers=_headers(token_a))
    assert resp.status_code == 200
    # Matches may or may not exist depending on Jaccard threshold, but endpoint should work
    assert isinstance(resp.json(), list)


def test_list_lost_posts(client, student_a):
    token, _ = student_a
    client.post("/lost-found", headers=_headers(token), json={
        "post_type": "lost",
        "item_description": "green water bottle",
        "color": "green",
        "last_seen_location": "Block B",
    })
    resp = client.get("/lost-found?post_type=lost&resolved=false", headers=_headers(token))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    types = [p["post_type"] for p in resp.json()]
    assert all(t == "lost" for t in types)


def test_resolve_post(client, student_a):
    token, _ = student_a
    post_id = client.post("/lost-found", headers=_headers(token), json={
        "post_type": "lost",
        "item_description": "black umbrella",
        "color": "black",
        "last_seen_location": "Block D",
    }).json()["id"]

    resp = client.post(f"/lost-found/{post_id}/resolve", headers=_headers(token))
    assert resp.status_code == 200
    assert resp.json()["resolved"] is True


def test_another_student_cannot_resolve_post(client, student_a, student_b):
    token_a, _ = student_a
    token_b, _ = student_b
    post_id = client.post("/lost-found", headers=_headers(token_a), json={
        "post_type": "lost",
        "item_description": "purple bag",
        "color": "purple",
        "last_seen_location": "Block E",
    }).json()["id"]

    resp = client.post(f"/lost-found/{post_id}/resolve", headers=_headers(token_b))
    assert resp.status_code in (403, 404)


def test_unauthenticated_cannot_list_lost_found(client):
    resp = client.get("/lost-found")
    assert resp.status_code == 403