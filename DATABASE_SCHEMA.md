# Database Schema Documentation

## Overview
PD Triglav aplikacija uporablja SQLAlchemy ORM z PostgreSQL (produkcija) ali SQLite (razvoj) podatkovno bazo.

## Database Tables

### 1. Users (`users`)
Uporabniki sistema s štirimi različnimi vlogami.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Unikaten identifikator |
| email | String(120) | UNIQUE, NOT NULL | Email naslov |
| name | String(100) | NOT NULL | Polno ime |
| password_hash | String(255) | - | Zgoščena gesla (bcrypt) |
| google_id | String(100) | UNIQUE | Google OAuth identifikator |
| role | Enum(UserRole) | NOT NULL, DEFAULT='pending' | Vloga: pending, member, trip_leader, admin |
| is_approved | Boolean | DEFAULT=False | Ali je uporabnik odobren |
| phone | String(20) | - | Telefonska številka |
| emergency_contact | String(200) | - | Stik v sili |
| bio | Text | - | Opis uporabnika |
| created_at | DateTime | DEFAULT=utcnow | Datum registracije |
| last_login | DateTime | - | Zadnja prijava |

**Relationships:**
- `trips_led` → One-to-Many z Trip (kot vodnik)
- `trip_participations` → One-to-Many z TripParticipant
- `trip_reports` → One-to-Many z TripReport
- `comments` → One-to-Many z Comment

### 2. Trips (`trips`)
Planinski izleti z vsemi podrobnostmi.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Unikaten identifikator |
| title | String(200) | NOT NULL | Naslov izleta |
| description | Text | - | Opis izleta |
| destination | String(200) | NOT NULL | Cilj/destinacija |
| trip_date | Date | NOT NULL | Datum izleta |
| meeting_time | Time | - | Čas zbiranja |
| meeting_point | String(200) | - | Mesto zbiranja |
| return_time | Time | - | Pričakovan čas vrnitve |
| difficulty | Enum(TripDifficulty) | NOT NULL | Zahtevnost: easy, moderate, difficult, expert |
| max_participants | Integer | - | Največ udeležencev (NULL = neomejeno) |
| equipment_needed | Text | - | Potrebna oprema |
| cost_per_person | Float | - | Cena na osebo |
| status | Enum(TripStatus) | DEFAULT='announced' | Status: announced, completed, cancelled |
| leader_id | Integer | FOREIGN KEY | Referenca na User (vodnik) |
| created_at | DateTime | DEFAULT=utcnow | Datum objave |

**Relationships:**
- `leader` → Many-to-One z User
- `participants` → One-to-Many z TripParticipant
- `reports` → One-to-Many z TripReport

**Business Logic:**
- `can_signup` → Omogoča prijave, če je status='announced' in datum v prihodnosti
- `is_full` → True, če je doseženo max_participants
- `confirmed_participants_count` → Število potrjenih udeležencev
- `waitlist_count` → Število na čakalni listi

### 3. Trip Participants (`trip_participants`)
Many-to-Many povezava med uporabniki in izleti s statusom prijave.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| trip_id | Integer | PRIMARY KEY, FOREIGN KEY | Referenca na Trip |
| user_id | Integer | PRIMARY KEY, FOREIGN KEY | Referenca na User |
| status | Enum(ParticipantStatus) | DEFAULT='confirmed' | Status: confirmed, waitlisted, cancelled |
| signup_date | DateTime | DEFAULT=utcnow | Datum prijave |
| notes | Text | - | Opombe (posebne potrebe, stik v sili) |

**Relationships:**
- `user` → Many-to-One z User
- `trip` → Many-to-One z Trip (preko backref)

**Business Logic:**
- Avtomatska promocija s čakalne liste, ko se kdo odjavi
- Prijave preko kapacitete gredo na čakalno listo

### 4. Trip Reports (`trip_reports`)
Poročila o opravljenih izletih z fotografijami.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Unikaten identifikator |
| title | String(200) | NOT NULL | Naslov poročila |
| content | Text | - | Vsebina (rich text) |
| summary | String(500) | - | Kratek povzetek |
| weather_conditions | String(200) | - | Vremenske razmere |
| trail_conditions | String(200) | - | Stanje poti |
| is_published | Boolean | DEFAULT=True | Ali je objavljeno |
| featured | Boolean | DEFAULT=False | Označeno na začetni strani |
| trip_id | Integer | FOREIGN KEY | Referenca na Trip |
| author_id | Integer | FOREIGN KEY | Referenca na User |
| created_at | DateTime | DEFAULT=utcnow | Datum objave |
| updated_at | DateTime | DEFAULT=utcnow | Zadnja sprememba |

**Constraints:**
- `unique_trip_report_per_author` → En uporabnik lahko napiše samo eno poročilo na izlet

**Relationships:**
- `trip` → Many-to-One z Trip
- `author` → Many-to-One z User
- `photos` → One-to-Many z Photo
- `comments` → One-to-Many z Comment

### 5. Photos (`photos`)
Fotografije povezane s poročili, shranjene v AWS S3.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Unikaten identifikator |
| filename | String(255) | NOT NULL | Ime datoteke |
| original_filename | String(255) | - | Originalno ime |
| s3_bucket | String(100) | - | AWS S3 bucket |
| s3_key | String(500) | NOT NULL | AWS S3 ključ |
| file_size | Integer | - | Velikost datoteke v bajtih |
| content_type | String(100) | - | MIME tip (image/jpeg, image/png) |
| caption | String(500) | - | Opis fotografije |
| trip_report_id | Integer | FOREIGN KEY | Referenca na TripReport |
| uploaded_by | Integer | FOREIGN KEY | Referenca na User |
| created_at | DateTime | DEFAULT=utcnow | Datum nalaganja |

**Relationships:**
- `trip_report` → Many-to-One z TripReport
- `uploader` → Many-to-One z User
- `comments` → One-to-Many z Comment

**Business Logic:**
- `s3_url` → Generira AWS S3 URL za dostop do slike
- Podpora za thumbnail različice

### 6. Comments (`comments`)
Komentarji na poročila in fotografije (Facebook-style).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Unikaten identifikator |
| content | Text | NOT NULL | Vsebina komentarja |
| trip_report_id | Integer | FOREIGN KEY | Referenca na TripReport (NULL za komentarje slik) |
| photo_id | Integer | FOREIGN KEY | Referenca na Photo (NULL za komentarje poročil) |
| author_id | Integer | FOREIGN KEY | Referenca na User |
| created_at | DateTime | DEFAULT=utcnow | Datum objave |
| updated_at | DateTime | DEFAULT=utcnow | Zadnja sprememba |

**Constraints:**
- Vsaj eden od `trip_report_id` ali `photo_id` mora biti nastavljen

**Relationships:**
- `trip_report` → Many-to-One z TripReport
- `photo` → Many-to-One z Photo
- `author` → Many-to-One z User

## Enumerations

### UserRole
- `PENDING` = 'pending' → Čaka odobritev
- `MEMBER` = 'member' → Običajen član
- `TRIP_LEADER` = 'trip_leader' → Vodnik izletov
- `ADMIN` = 'admin' → Administrator

### TripDifficulty
- `EASY` = 'easy' → Lahka tura
- `MODERATE` = 'moderate' → Srednje zahtevna
- `DIFFICULT` = 'difficult' → Zahtevna
- `EXPERT` = 'expert' → Zelo zahtevna

### TripStatus
- `ANNOUNCED` = 'announced' → Objavljen
- `COMPLETED` = 'completed' → Opravljen
- `CANCELLED` = 'cancelled' → Odpovedan

### ParticipantStatus
- `CONFIRMED` = 'confirmed' → Potrjen
- `WAITLISTED` = 'waitlisted' → Na čakalni listi
- `CANCELLED` = 'cancelled' → Odpovedal

## Key Business Rules

1. **Uporabniki**:
   - Nova registracija → status PENDING
   - Admin mora odobriti nove uporabnike
   - Google OAuth uporabniki → avtomatski PENDING status

2. **Izleti**:
   - Samo TRIP_LEADER in ADMIN lahko ustvarjajo izlete
   - Prijave možne samo za objavljene izlete v prihodnosti
   - Avtomatska promocija s čakalne liste
   - Pretekli izleti se avtomatsko označijo kot COMPLETED

3. **Poročila**:
   - En uporabnik = eno poročilo na izlet
   - Fotografije shranjuje AWS S3
   - Komentarji možni na poročila in fotografije

4. **Varnost**:
   - Gesla shranjena kot bcrypt hash
   - Google OAuth integracija
   - Vloge kontrolirajo dostop do funkcij

## Database Migrations

```bash
# Ustvarjanje tabel (razvoj)
python3 app.py  # Avtomatsko ustvari tabele

# Nalaganje testnih podatkov
python3 scripts/seed_db.py
```

## Performance Considerations

- Indeksi na `email`, `google_id`, `trip_date`
- Kompozitni indeks na `(trip_id, user_id)` za TripParticipant
- AWS S3 za slike zmanjša obremenitev baze
- Eager loading za relacionske podatke z `joinedload()`