# VIT Laundry Backend — PowerShell Test Commands (Windows)

> **Start the server first (in a separate terminal):**
> ```powershell
> uvicorn app.main:app --reload
> ```
> Base URL: `http://localhost:8000`
> Interactive docs: `http://localhost:8000/docs`

---

## 0. Health Check

```powershell
Invoke-RestMethod http://localhost:8000/health
```

---

## 1. Auth

### Register a student
```powershell
Invoke-RestMethod -Method Post http://localhost:8000/auth/register/student `
  -ContentType "application/json" `
  -Body '{
    "registration_number": "22BCE1234",
    "name": "Arjun Kumar",
    "email": "arjun@vit.ac.in",
    "phone_number": "9876543210",
    "password": "secret123",
    "block": "A",
    "floor": 3,
    "room_number": "A303",
    "language_preference": "en"
  }'
```

### Register staff
```powershell
Invoke-RestMethod -Method Post http://localhost:8000/auth/register/staff `
  -ContentType "application/json" `
  -Body '{
    "name": "Ravi Staff",
    "employee_id": "EMP001",
    "phone_number": "9000000001",
    "password": "staffpass",
    "role": "staff"
  }'
```

### Register admin
```powershell
Invoke-RestMethod -Method Post http://localhost:8000/auth/register/staff `
  -ContentType "application/json" `
  -Body '{
    "name": "Admin User",
    "employee_id": "ADMIN001",
    "phone_number": "9000000002",
    "password": "adminpass",
    "role": "admin"
  }'
```

### Login as student → save token
```powershell
$r = Invoke-RestMethod -Method Post http://localhost:8000/auth/login `
  -ContentType "application/json" `
  -Body '{"identifier":"arjun@vit.ac.in","password":"secret123","role":"student"}'
$ST = $r.access_token
Write-Host "Student token: $ST"
```

### Login as staff → save token
```powershell
$r = Invoke-RestMethod -Method Post http://localhost:8000/auth/login `
  -ContentType "application/json" `
  -Body '{"identifier":"EMP001","password":"staffpass","role":"staff"}'
$SF = $r.access_token
Write-Host "Staff token: $SF"
```

### Login as admin → save token
```powershell
$r = Invoke-RestMethod -Method Post http://localhost:8000/auth/login `
  -ContentType "application/json" `
  -Body '{"identifier":"ADMIN001","password":"adminpass","role":"admin"}'
$ADM = $r.access_token
Write-Host "Admin token: $ADM"
```

---

## 2. Students

### Get own profile
```powershell
Invoke-RestMethod http://localhost:8000/students/me `
  -Headers @{ Authorization = "Bearer $ST" }
```

### Update profile
```powershell
Invoke-RestMethod -Method Patch http://localhost:8000/students/me `
  -Headers @{ Authorization = "Bearer $ST" } `
  -ContentType "application/json" `
  -Body '{"language_preference":"ta","room_number":"A304","fcm_token":"fake-fcm-token-123"}'
```

### Get student ID (saved for later)
```powershell
$SID = (Invoke-RestMethod http://localhost:8000/students/me `
  -Headers @{ Authorization = "Bearer $ST" }).id
Write-Host "Student ID: $SID"
```

---

## 3. Slot Booking

### Check availability for today
```powershell
$today = (Get-Date -Format "yyyy-MM-dd")
Invoke-RestMethod "http://localhost:8000/slots/availability/$today" `
  -Headers @{ Authorization = "Bearer $ST" }
```

### Book a slot for today
```powershell
$today = (Get-Date -Format "yyyy-MM-dd")
$r = Invoke-RestMethod -Method Post http://localhost:8000/slots/book `
  -Headers @{ Authorization = "Bearer $ST" } `
  -ContentType "application/json" `
  -Body "{`"date`":`"$today`"}"
$SLOT_ID = $r.id
Write-Host "Slot ID: $SLOT_ID"
```

### View my slots
```powershell
Invoke-RestMethod http://localhost:8000/slots/my `
  -Headers @{ Authorization = "Bearer $ST" }
```

### Cancel a slot
```powershell
Invoke-RestMethod -Method Post http://localhost:8000/slots/cancel `
  -Headers @{ Authorization = "Bearer $ST" } `
  -ContentType "application/json" `
  -Body "{`"slot_id`":`"$SLOT_ID`"}"
```

### Admin: update daily slot limit
```powershell
Invoke-RestMethod -Method Patch "http://localhost:8000/slots/limit?new_limit=200" `
  -Headers @{ Authorization = "Bearer $ADM" }
```

---

## 4. RFID Devices & Tags

### Register a device (admin)
```powershell
$r = Invoke-RestMethod -Method Post http://localhost:8000/devices `
  -Headers @{ Authorization = "Bearer $ADM" } `
  -ContentType "application/json" `
  -Body '{"device_name":"Dropoff Scanner 1","location_tag":"dropoff"}'
$DEVICE_ID = $r.id
Write-Host "Device ID: $DEVICE_ID"
```

### List devices
```powershell
Invoke-RestMethod http://localhost:8000/devices `
  -Headers @{ Authorization = "Bearer $SF" }
```

### Link RFID tag to student
```powershell
Invoke-RestMethod -Method Post http://localhost:8000/rfid/link `
  -Headers @{ Authorization = "Bearer $SF" } `
  -ContentType "application/json" `
  -Body "{`"tag_uid`":`"AABBCCDD`",`"student_id`":`"$SID`"}"
```

### Simulate dropoff scan
```powershell
Invoke-RestMethod -Method Post http://localhost:8000/rfid/scan `
  -Headers @{ Authorization = "Bearer $SF" } `
  -ContentType "application/json" `
  -Body "{`"tag_uid`":`"AABBCCDD`",`"device_id`":`"$DEVICE_ID`",`"scan_type`":`"dropoff`"}"
```

### Simulate ready scan
```powershell
Invoke-RestMethod -Method Post http://localhost:8000/rfid/scan `
  -Headers @{ Authorization = "Bearer $SF" } `
  -ContentType "application/json" `
  -Body "{`"tag_uid`":`"AABBCCDD`",`"device_id`":`"$DEVICE_ID`",`"scan_type`":`"ready`"}"
```

### Simulate collected scan
```powershell
Invoke-RestMethod -Method Post http://localhost:8000/rfid/scan `
  -Headers @{ Authorization = "Bearer $SF" } `
  -ContentType "application/json" `
  -Body "{`"tag_uid`":`"AABBCCDD`",`"device_id`":`"$DEVICE_ID`",`"scan_type`":`"collected`"}"
```

### View scan audit log
```powershell
Invoke-RestMethod "http://localhost:8000/rfid/scan-log?limit=20" `
  -Headers @{ Authorization = "Bearer $SF" }
```

---

## 5. Bags

### My active bag
```powershell
Invoke-RestMethod http://localhost:8000/bags/my `
  -Headers @{ Authorization = "Bearer $ST" }
```

### My bag history
```powershell
$bags = Invoke-RestMethod http://localhost:8000/bags/my/history `
  -Headers @{ Authorization = "Bearer $ST" }
$BAG_ID = $bags[0].id
Write-Host "Bag ID: $BAG_ID"
```

### Bag status log
```powershell
Invoke-RestMethod "http://localhost:8000/bags/$BAG_ID/logs" `
  -Headers @{ Authorization = "Bearer $ST" }
```

---

## 6. Staff Operations

### Report a delay
```powershell
$today = (Get-Date -Format "yyyy-MM-dd")
Invoke-RestMethod -Method Post http://localhost:8000/staff/delays `
  -Headers @{ Authorization = "Bearer $SF" } `
  -ContentType "application/json" `
  -Body "{`"reason`":`"machine_repair`",`"affected_date`":`"$today`",`"note`":`"Drum 2 motor failure`"}"
```

### List delay reports
```powershell
Invoke-RestMethod http://localhost:8000/staff/delays `
  -Headers @{ Authorization = "Bearer $SF" }
```

### Set floor schedule (Block A, Floor 3, Monday)
```powershell
Invoke-RestMethod -Method Put http://localhost:8000/staff/schedules `
  -Headers @{ Authorization = "Bearer $SF" } `
  -ContentType "application/json" `
  -Body '{"block":"A","floor":3,"day_of_week":0,"is_active":true}'
```

### Add a blocked date
```powershell
Invoke-RestMethod -Method Post http://localhost:8000/staff/blocked-dates `
  -Headers @{ Authorization = "Bearer $SF" } `
  -ContentType "application/json" `
  -Body '{"date":"2026-04-14","reason":"Pongal holiday"}'
```

### Today's ops snapshot
```powershell
Invoke-RestMethod http://localhost:8000/staff/today `
  -Headers @{ Authorization = "Bearer $SF" }
```

---

## 7. Forum

### Create a post
```powershell
$r = Invoke-RestMethod -Method Post http://localhost:8000/forum `
  -Headers @{ Authorization = "Bearer $ST" } `
  -ContentType "application/json" `
  -Body '{"category":"tips","title":"Best time to drop off","body":"Drop off before 8am for fastest turnaround.","is_anonymous":false}'
$POST_ID = $r.id
Write-Host "Post ID: $POST_ID"
```

### List posts
```powershell
Invoke-RestMethod "http://localhost:8000/forum?category=tips&page=1&page_size=10" `
  -Headers @{ Authorization = "Bearer $ST" }
```

### Upvote a post
```powershell
Invoke-RestMethod -Method Post "http://localhost:8000/forum/$POST_ID/upvote" `
  -Headers @{ Authorization = "Bearer $ST" }
```

### Reply to a post
```powershell
Invoke-RestMethod -Method Post "http://localhost:8000/forum/$POST_ID/replies" `
  -Headers @{ Authorization = "Bearer $ST" } `
  -ContentType "application/json" `
  -Body '{"body":"Totally agree, 7am works great!","is_anonymous":false}'
```

### Admin: pin a post
```powershell
Invoke-RestMethod -Method Post "http://localhost:8000/forum/$POST_ID/pin" `
  -Headers @{ Authorization = "Bearer $ADM" }
```

---

## 8. Lost & Found

### Post a lost item
```powershell
$r = Invoke-RestMethod -Method Post http://localhost:8000/lost-found `
  -Headers @{ Authorization = "Bearer $ST" } `
  -ContentType "application/json" `
  -Body '{"post_type":"lost","item_description":"blue denim jacket with VIT badge","color":"blue","last_seen_location":"Block A laundry room"}'
$LF_ID = $r.id
Write-Host "Lost post ID: $LF_ID"
```

### Post a found item (triggers Jaccard match scan)
```powershell
Invoke-RestMethod -Method Post http://localhost:8000/lost-found `
  -Headers @{ Authorization = "Bearer $ST" } `
  -ContentType "application/json" `
  -Body '{"post_type":"found","item_description":"denim jacket blue found near laundry","color":"blue","last_seen_location":"Block A"}'
```

### List unresolved lost posts
```powershell
Invoke-RestMethod "http://localhost:8000/lost-found?post_type=lost&resolved=false" `
  -Headers @{ Authorization = "Bearer $ST" }
```

### View matches for a post
```powershell
Invoke-RestMethod "http://localhost:8000/lost-found/$LF_ID/matches" `
  -Headers @{ Authorization = "Bearer $ST" }
```

### Mark as resolved
```powershell
Invoke-RestMethod -Method Post "http://localhost:8000/lost-found/$LF_ID/resolve" `
  -Headers @{ Authorization = "Bearer $ST" }
```

---

## 9. Admin Analytics

### System overview
```powershell
Invoke-RestMethod http://localhost:8000/admin/analytics/overview `
  -Headers @{ Authorization = "Bearer $ADM" }
```

### Slot analytics
```powershell
Invoke-RestMethod "http://localhost:8000/admin/analytics/slots?from_date=2026-04-01&to_date=2026-04-30" `
  -Headers @{ Authorization = "Bearer $ADM" }
```

### Bag state counts
```powershell
Invoke-RestMethod http://localhost:8000/admin/analytics/bags `
  -Headers @{ Authorization = "Bearer $ADM" }
```

### Notification delivery stats
```powershell
Invoke-RestMethod "http://localhost:8000/admin/analytics/notifications?from_date=2026-04-01&to_date=2026-04-30" `
  -Headers @{ Authorization = "Bearer $ADM" }
```

### List all students
```powershell
Invoke-RestMethod "http://localhost:8000/admin/students?active_only=true&page=1&page_size=20" `
  -Headers @{ Authorization = "Bearer $ADM" }
```

---

## 10. Run Pytest Suite

```powershell
pip install pytest httpx pytest-asyncio
pytest tests/ -v
```

---

## Quick End-to-End Flow (run top to bottom in one session)

```powershell
$BASE = "http://localhost:8000"

# Register
Invoke-RestMethod -Method Post "$BASE/auth/register/student" -ContentType "application/json" `
  -Body '{"registration_number":"22BCE9999","name":"Test Student","email":"test@vit.ac.in","phone_number":"9999999999","password":"pass123","block":"B","floor":2,"room_number":"B202","language_preference":"en"}'

Invoke-RestMethod -Method Post "$BASE/auth/register/staff" -ContentType "application/json" `
  -Body '{"name":"Test Staff","employee_id":"EMP999","phone_number":"8888888888","password":"staffpass","role":"staff"}'

Invoke-RestMethod -Method Post "$BASE/auth/register/staff" -ContentType "application/json" `
  -Body '{"name":"Test Admin","employee_id":"ADM999","phone_number":"7777777777","password":"adminpass","role":"admin"}'

# Get tokens
$ST  = (Invoke-RestMethod -Method Post "$BASE/auth/login" -ContentType "application/json" `
  -Body '{"identifier":"test@vit.ac.in","password":"pass123","role":"student"}').access_token

$SF  = (Invoke-RestMethod -Method Post "$BASE/auth/login" -ContentType "application/json" `
  -Body '{"identifier":"EMP999","password":"staffpass","role":"staff"}').access_token

$ADM = (Invoke-RestMethod -Method Post "$BASE/auth/login" -ContentType "application/json" `
  -Body '{"identifier":"ADM999","password":"adminpass","role":"admin"}').access_token

# Get student ID
$SID = (Invoke-RestMethod "$BASE/students/me" -Headers @{ Authorization = "Bearer $ST" }).id

# Register device
$DEVICE_ID = (Invoke-RestMethod -Method Post "$BASE/devices" `
  -Headers @{ Authorization = "Bearer $ADM" } -ContentType "application/json" `
  -Body '{"device_name":"Scanner-1","location_tag":"dropoff"}').id

# Link tag to student
Invoke-RestMethod -Method Post "$BASE/rfid/link" `
  -Headers @{ Authorization = "Bearer $SF" } -ContentType "application/json" `
  -Body "{`"tag_uid`":`"TESTUID01`",`"student_id`":`"$SID`"}"

# Book slot for today
$today = (Get-Date -Format "yyyy-MM-dd")
Invoke-RestMethod -Method Post "$BASE/slots/book" `
  -Headers @{ Authorization = "Bearer $ST" } -ContentType "application/json" `
  -Body "{`"date`":`"$today`"}"

# Full bag lifecycle: dropoff → ready → collected
Invoke-RestMethod -Method Post "$BASE/rfid/scan" `
  -Headers @{ Authorization = "Bearer $SF" } -ContentType "application/json" `
  -Body "{`"tag_uid`":`"TESTUID01`",`"device_id`":`"$DEVICE_ID`",`"scan_type`":`"dropoff`"}"

Invoke-RestMethod -Method Post "$BASE/rfid/scan" `
  -Headers @{ Authorization = "Bearer $SF" } -ContentType "application/json" `
  -Body "{`"tag_uid`":`"TESTUID01`",`"device_id`":`"$DEVICE_ID`",`"scan_type`":`"ready`"}"

Invoke-RestMethod -Method Post "$BASE/rfid/scan" `
  -Headers @{ Authorization = "Bearer $SF" } -ContentType "application/json" `
  -Body "{`"tag_uid`":`"TESTUID01`",`"device_id`":`"$DEVICE_ID`",`"scan_type`":`"collected`"}"

# Confirm final bag status — should be "collected"
(Invoke-RestMethod "$BASE/bags/my/history" -Headers @{ Authorization = "Bearer $ST" })[0].status
```