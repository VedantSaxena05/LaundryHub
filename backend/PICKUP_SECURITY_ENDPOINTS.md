# Pickup Security Feature — Endpoint Reference

## Overview

The pickup security feature adds a **two-step bag collection** flow and
a **one-time enrollment** step for both the bag RFID tag and the student's
college ID card.

```
ENROLLMENT (one-time per student)
  Staff → POST /rfid/link-bag-tag   (link bag RFID tag to student)
  Staff → POST /rfid/link-id-card   (link college ID card to student)

OPERATIONAL (every laundry cycle)
  ESP32 → POST /rfid/scan  scan_type=dropoff    (bag tag, drop-off counter)
  ESP32 → POST /rfid/scan  scan_type=ready      (bag tag, shelf reader)
  ESP32 → POST /rfid/scan  scan_type=pickup_bag (bag tag, pickup counter)  ← Step 1
  ESP32 → POST /rfid/scan  scan_type=pickup_id  (ID card, pickup counter)  ← Step 2
```

---

## State Machine

```
  [pending]
      │  dropoff scan (bag tag)
      ▼
  [dropped]
      │  ready scan (bag tag)
      ▼
  [ready]
      │  pickup_bag scan (bag tag)        ← NEW
      ▼
  [awaiting_id_scan]
      │  pickup_id scan (any ID card)     ← NEW
      ▼
  [collected]
```

---

## Enrollment Endpoints

### `POST /rfid/link-bag-tag`

Link the RFID sticker on a student's laundry bag to their account.
Done once when the bag is issued to the student.

**Auth:** Staff or Admin JWT

**Request body:**
```json
{
  "tag_uid": "A1B2C3D4",
  "student_id": "uuid-of-student"
}
```

**Response `201`:**
```json
{
  "id": "uuid",
  "tag_uid": "A1B2C3D4",
  "tag_type": "bag",
  "student_id": "uuid-of-student",
  "linked_by": "uuid-of-staff",
  "linked_at": "2026-04-04T10:00:00Z",
  "is_active": true,
  "created_at": "2026-04-04T10:00:00Z"
}
```

**Error cases:**
- `400` — tag already linked to a different student

---

### `POST /rfid/link-id-card`

Link the RFID chip in a student's college ID card to their account.
Done once at enrollment / registration time.

Only **one active ID card** is allowed per student. If the student already
has a different ID card linked, the old one is deactivated automatically.

**Auth:** Staff or Admin JWT

**Request body:**
```json
{
  "tag_uid": "E5F6A7B8",
  "student_id": "uuid-of-student"
}
```

**Response `201`:**
```json
{
  "id": "uuid",
  "tag_uid": "E5F6A7B8",
  "tag_type": "id_card",
  "student_id": "uuid-of-student",
  "linked_by": "uuid-of-staff",
  "linked_at": "2026-04-04T10:00:00Z",
  "is_active": true,
  "created_at": "2026-04-04T10:00:00Z"
}
```

**Error cases:**
- `400` — ID card already linked to a different student

---

## Scan Endpoint

### `POST /rfid/scan`

Called by the ESP32 on every card swipe. Always returns `HTTP 200`.
Inspect the `result` field in the response body to determine the outcome.

**Auth:** Staff JWT (the logged-in staff member operating the reader)

---

### Scan type: `dropoff`  *(unchanged)*

Student places their bag; staff scans the bag tag at the drop-off counter.

**Request:**
```json
{
  "tag_uid": "A1B2C3D4",
  "device_id": "uuid-of-dropoff-device",
  "scan_type": "dropoff"
}
```

**Success response:**
```json
{
  "result": "success",
  "message": "Bag status updated: pending → dropped",
  "bag_status": "dropped",
  "student_name": "Arjun Kumar",
  "bag_id": "uuid-of-bag",
  ...
}
```

**Possible result codes:**

| result | meaning |
|---|---|
| `success` | Bag moved to `dropped` |
| `unknown_tag` | Bag tag not enrolled |
| `no_slot_booked` | Student has no slot booked today |
| `student_not_found` | Tag linked to deleted account |

---

### Scan type: `ready`  *(unchanged)*

Staff scans the bag tag when the washed bag is placed on the collection shelf.

**Request:**
```json
{
  "tag_uid": "A1B2C3D4",
  "device_id": "uuid-of-shelf-device",
  "scan_type": "ready"
}
```

**Success response:**
```json
{
  "result": "success",
  "message": "Bag status updated: dropped → ready",
  "bag_status": "ready",
  ...
}
```

---

### Scan type: `pickup_bag`  *(NEW — Step 1 of 2)*

Student or staff scans the **bag tag** at the pickup counter.
The bag moves to `awaiting_id_scan`. The device must display
"Now tap your college ID card" and hold the returned `bag_id`
to send in the next scan.

**Request:**
```json
{
  "tag_uid": "A1B2C3D4",
  "device_id": "uuid-of-pickup-device",
  "scan_type": "pickup_bag"
}
```

**Success response:**
```json
{
  "result": "success",
  "message": "Bag status updated: ready → awaiting_id_scan — now tap college ID card to confirm pickup",
  "bag_status": "awaiting_id_scan",
  "bag_id": "uuid-of-bag",          ← device must store this
  "student_name": "Arjun Kumar",
  "student_id": "uuid-of-student",
  ...
}
```

**Possible result codes:**

| result | meaning |
|---|---|
| `success` | Bag moved to `awaiting_id_scan` |
| `unknown_tag` | Bag tag not enrolled |
| `wrong_state` | Bag not in `ready` state |
| `no_active_bag` | No active bag for this student |
| `student_not_found` | Tag linked to deleted account |

---

### Scan type: `pickup_id`  *(NEW — Step 2 of 2)*

Student taps their **college ID card** at the pickup counter.
Any student's enrolled ID card is accepted — it does not have to be
the bag owner. The tapper's identity is recorded in the audit log only.

The device **must** pass the `bag_id` received from the preceding
`pickup_bag` response. This ties the ID confirmation to the exact bag.

**Request:**
```json
{
  "tag_uid": "E5F6A7B8",
  "device_id": "uuid-of-pickup-device",
  "scan_type": "pickup_id",
  "bag_id": "uuid-of-bag"            ← required; from pickup_bag response
}
```

**Success response — bag owner collects:**
```json
{
  "result": "success",
  "message": "Bag status updated: awaiting_id_scan → collected. Collected by Arjun Kumar (bag owner)",
  "bag_status": "collected",
  "student_name": "Arjun Kumar",
  "pickup_tapped_by_student_id": "uuid-of-arjun",
  "pickup_tapped_by_student_name": "Arjun Kumar",
  ...
}
```

**Success response — someone else collects on behalf:**
```json
{
  "result": "success",
  "message": "Bag status updated: awaiting_id_scan → collected. Collected on behalf of Arjun Kumar — ID card tapped by Priya Sharma",
  "bag_status": "collected",
  "student_name": "Arjun Kumar",
  "pickup_tapped_by_student_id": "uuid-of-priya",
  "pickup_tapped_by_student_name": "Priya Sharma",
  ...
}
```

**Possible result codes:**

| result | meaning |
|---|---|
| `success` | Bag moved to `collected` |
| `missing_bag_id` | `bag_id` field not sent in request |
| `bag_not_found` | `bag_id` not found in DB |
| `wrong_state` | Bag not in `awaiting_id_scan` state |
| `unknown_id_card` | ID card UID not enrolled |
| `id_card_not_linked` | ID card exists but not linked to any student |

---

## Other Tag Management Endpoints

### `POST /rfid/unlink/{tag_uid}`

Deactivate a tag and remove its student association.
Works for both bag tags and ID card tags.

**Auth:** Staff

**Response:** Updated tag record with `is_active: false`, `student_id: null`

---

### `GET /rfid/tags`

List all registered RFID tags with their `tag_type` field.

**Auth:** Staff

---

### `GET /rfid/tags/{tag_uid}`

Look up a single tag by UID.

**Auth:** Staff

---

### `DELETE /rfid/tags/{tag_uid}`

Soft-delete (deactivate) a tag.

**Auth:** Admin only

---

### `GET /rfid/scan-log?limit=100`

Return recent scan audit log entries. Each entry includes
`pickup_scanned_by_student_id` (populated on `pickup_id` scans).

**Auth:** Staff

---

## ESP32 Device Flow at Pickup Counter

```
1. Student presents bag
   → ESP32 reads bag tag UID
   → POST /rfid/scan { tag_uid, device_id, scan_type: "pickup_bag" }
   → Response: { result: "success", bag_id: "...", bag_status: "awaiting_id_scan" }
   → Display: "Bag found for Arjun Kumar. Please tap your college ID card."

2. Student taps ID card
   → ESP32 reads ID card UID
   → POST /rfid/scan { tag_uid, device_id, scan_type: "pickup_id", bag_id: "<from step 1>" }
   → Response: { result: "success", bag_status: "collected", pickup_tapped_by_student_name: "..." }
   → Display: "Collected ✓ — have a good day!"
```

If `pickup_bag` returns anything other than `success`, the device should
display the `message` field and NOT proceed to the ID card scan step.

---

## Audit Trail

Every pickup is recorded in two places:

**`rfid_scan_events`**
```
pickup_bag row: tag_uid=<bag_tag>, bag_id=<bag_id>, pickup_scanned_by_student_id=NULL
pickup_id  row: tag_uid=<id_card>, bag_id=<bag_id>, pickup_scanned_by_student_id=<tapper_id>
```

**`bag_status_logs`**
```
awaiting_id_scan row: from=ready,            to=awaiting_id_scan, pickup_scanned_by_student=NULL
collected        row: from=awaiting_id_scan, to=collected,        pickup_scanned_by_student=<tapper_id>
```
