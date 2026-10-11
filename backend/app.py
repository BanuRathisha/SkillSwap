from flask import Flask, send_from_directory
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_db_connection

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
CORS(app)


# =========================================================
# HELPERS
# =========================================================

def close_db(cursor, connection):
    if cursor:
        cursor.close()
    if connection:
        connection.close()


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/dashboard.html", methods=["GET"])
def dashboard_page():
    return send_from_directory(FRONTEND_DIR, "dashboard.html")


@app.route("/style.css", methods=["GET"])
def frontend_css():
    return send_from_directory(FRONTEND_DIR, "style.css")


@app.route("/frontend/<path:filename>", methods=["GET"])
def frontend_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)

# =========================================================
# REGISTER - 100 STARTER CREDITS
# =========================================================

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({
            "success": False,
            "message": "Name, email and password are required"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM students WHERE email = %s",
            (email,)
        )

        if cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "Email already registered"
            }), 409

        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO students
                (name, email, password, skill_credits)
            VALUES (%s, %s, %s, %s)
        """, (name, email, hashed_password, 100))

        student_id = cursor.lastrowid
        connection.commit()

        return jsonify({
            "success": True,
            "message": "Registration successful",
            "student_id": student_id,
            "skill_credits": 100
        }), 201

    except Exception:
        if connection:
            connection.rollback()
        app.logger.exception("Registration failed")
        return jsonify({
            "success": False,
            "message": "Registration failed"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM students WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()

        if not user or not check_password_hash(
            user["password"], password
        ):
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "bio": user.get("bio"),
                "department": user.get("department"),
                "year": user.get("year"),
                "skills_to_teach": user.get("skills_to_teach"),
                "skills_to_learn": user.get("skills_to_learn"),
                "profile_image": user.get("profile_image"),
                "skill_credits": user.get("skill_credits") or 0
            }
        })

    except Exception:
        app.logger.exception("Login failed")
        return jsonify({
            "success": False,
            "message": "Login failed"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# GET PROFILE
# =========================================================

@app.route("/api/profile/<int:student_id>", methods=["GET"])
def get_profile(student_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, email, bio, department, year,
                   skills_to_teach, skills_to_learn,
                   profile_image, skill_credits
            FROM students WHERE id = %s
        """, (student_id,))

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "success": False,
                "message": "Student not found"
            }), 404

        return jsonify({"success": True, "user": user})

    except Exception:
        app.logger.exception("Get profile failed")
        return jsonify({
            "success": False,
            "message": "Unable to load profile"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# UPDATE PROFILE
# =========================================================

@app.route("/api/profile/<int:student_id>", methods=["PUT"])
def update_profile(student_id):
    data = request.get_json(silent=True) or {}

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE students
            SET name=%s, bio=%s, department=%s, year=%s,
                skills_to_teach=%s, skills_to_learn=%s,
                profile_image=%s
            WHERE id=%s
        """, (
            data.get("name"),
            data.get("bio"),
            data.get("department"),
            data.get("year"),
            data.get("skills_to_teach"),
            data.get("skills_to_learn"),
            data.get("profile_image"),
            student_id
        ))

        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "success": True,
                "message": "Profile unchanged or student not found"
            })

        return jsonify({
            "success": True,
            "message": "Profile updated successfully"
        })

    except Exception:
        if connection:
            connection.rollback()
        app.logger.exception("Profile update failed")
        return jsonify({
            "success": False,
            "message": "Unable to update profile"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# ADD SKILL
# =========================================================

@app.route("/api/skills", methods=["POST"])
def add_skill():
    data = request.get_json(silent=True) or {}

    student_id = data.get("student_id")
    skill_name = data.get("skill_name")
    skill_type = data.get("skill_type", "teach")
    level = data.get("level")

    if not student_id or not skill_name:
        return jsonify({
            "success": False,
            "message": "Student ID and skill name are required"
        }), 400

    if skill_type not in ("teach", "learn"):
        return jsonify({
            "success": False,
            "message": "Skill type must be teach or learn"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO skills (student_id, skill_name, skill_type, level)
            VALUES (%s, %s, %s, %s)
        """, (student_id, skill_name, skill_type, level))

        skill_id = cursor.lastrowid
        connection.commit()

        return jsonify({
            "success": True,
            "message": "Skill added successfully",
            "skill_id": skill_id
        }), 201

    except Exception:
        if connection:
            connection.rollback()
        app.logger.exception("Add skill failed")
        return jsonify({
            "success": False,
            "message": "Unable to add skill"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# GET STUDENT SKILLS
# =========================================================

@app.route("/api/skills/<int:student_id>", methods=["GET"])
def get_skills(student_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM skills
            WHERE student_id = %s
            ORDER BY created_at DESC
        """, (student_id,))

        return jsonify({
            "success": True,
            "skills": cursor.fetchall()
        })

    except Exception:
        app.logger.exception("Get skills failed")
        return jsonify({
            "success": False,
            "message": "Unable to load skills"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# DELETE SKILL
# =========================================================

@app.route("/api/skills/<int:skill_id>", methods=["DELETE"])
def delete_skill(skill_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM skills WHERE id = %s",
            (skill_id,)
        )
        deleted = cursor.rowcount
        connection.commit()

        if not deleted:
            return jsonify({
                "success": False,
                "message": "Skill not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Skill deleted successfully"
        })

    except Exception:
        if connection:
            connection.rollback()
        app.logger.exception("Delete skill failed")
        return jsonify({
            "success": False,
            "message": "Unable to delete skill"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# FIND MATCHES
# =========================================================

@app.route("/api/matches/<int:student_id>", methods=["GET"])
def get_matches(student_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT s.id, s.name, s.email, s.bio, s.department,
                   s.year, s.profile_image, s.skill_credits,
                   sk.id AS skill_id, sk.skill_name, sk.level
            FROM students s
            JOIN skills sk ON s.id = sk.student_id
            WHERE s.id != %s AND sk.skill_type = 'teach'
            ORDER BY s.name
        """, (student_id,))

        return jsonify({
            "success": True,
            "matches": cursor.fetchall()
        })

    except Exception:
        app.logger.exception("Find matches failed")
        return jsonify({
            "success": False,
            "message": "Unable to load matches"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# CREATE LEARNING REQUEST
# =========================================================

@app.route("/api/requests", methods=["POST"])
def create_request():
    data = request.get_json(silent=True) or {}

    learner_id = data.get("learner_id")
    teacher_id = data.get("teacher_id")
    skill_id = data.get("skill_id")
    message = data.get("message", "")

    if not learner_id or not teacher_id or not skill_id:
        return jsonify({
            "success": False,
            "message": "Required fields are missing"
        }), 400

    if learner_id == teacher_id:
        return jsonify({
            "success": False,
            "message": "Learner and teacher must be different"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO learning_requests
                (learner_id, teacher_id, skill_id, message, status)
            VALUES (%s, %s, %s, %s, 'pending')
        """, (learner_id, teacher_id, skill_id, message))

        request_id = cursor.lastrowid
        connection.commit()

        return jsonify({
            "success": True,
            "message": "Learning request sent successfully",
            "request_id": request_id
        }), 201

    except Exception:
        if connection:
            connection.rollback()
        app.logger.exception("Create request failed")
        return jsonify({
            "success": False,
            "message": "Unable to create request"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# GET REQUESTS
# =========================================================

@app.route("/api/requests/<int:student_id>", methods=["GET"])
def get_requests(student_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT lr.*, learner.name AS learner_name,
                   teacher.name AS teacher_name, sk.skill_name
            FROM learning_requests lr
            JOIN students learner ON lr.learner_id = learner.id
            JOIN students teacher ON lr.teacher_id = teacher.id
            JOIN skills sk ON lr.skill_id = sk.id
            WHERE lr.learner_id = %s OR lr.teacher_id = %s
            ORDER BY lr.created_at DESC
        """, (student_id, student_id))

        return jsonify({
            "success": True,
            "requests": cursor.fetchall()
        })

    except Exception:
        app.logger.exception("Get requests failed")
        return jsonify({
            "success": False,
            "message": "Unable to load requests"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# UPDATE REQUEST STATUS
# =========================================================

@app.route("/api/requests/<int:request_id>", methods=["PUT"])
def update_request(request_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")

    if status not in ["pending", "accepted", "rejected", "completed"]:
        return jsonify({
            "success": False,
            "message": "Invalid status"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE learning_requests
            SET status = %s
            WHERE id = %s
        """, (status, request_id))

        if cursor.rowcount == 0:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Request not found or unchanged"
            }), 404

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Request updated successfully"
        })

    except Exception:
        if connection:
            connection.rollback()
        app.logger.exception("Update request failed")
        return jsonify({
            "success": False,
            "message": "Unable to update request"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# CREATE SESSION
# =========================================================

@app.route("/api/sessions", methods=["POST"])
def create_session():
    data = request.get_json(silent=True) or {}

    request_id = data.get("request_id")
    learner_id = data.get("learner_id")
    teacher_id = data.get("teacher_id")
    skill_id = data.get("skill_id")
    duration = data.get("duration", 1)

    if not learner_id or not teacher_id or not skill_id:
        return jsonify({
            "success": False,
            "message": "Learner, teacher and skill are required"
        }), 400

    if learner_id == teacher_id:
        return jsonify({
            "success": False,
            "message": "Learner and teacher must be different"
        }), 400

    try:
        duration = int(duration)
        if duration < 1:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Duration must be a positive integer"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Validate participants and skill.
        cursor.execute("""
            SELECT id FROM students
            WHERE id IN (%s, %s)
        """, (learner_id, teacher_id))

        if len(cursor.fetchall()) != 2:
            return jsonify({
                "success": False,
                "message": "Learner or teacher not found"
            }), 404

        cursor.execute("""
            SELECT id FROM skills
            WHERE id = %s AND student_id = %s
              AND skill_type = 'teach'
        """, (skill_id, teacher_id))

        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "Skill does not belong to this teacher"
            }), 400

        if request_id:
            cursor.execute("""
                SELECT id, learner_id, teacher_id, skill_id, status
                FROM learning_requests
                WHERE id = %s
            """, (request_id,))
            req = cursor.fetchone()

            if (
                not req
                or req["learner_id"] != learner_id
                or req["teacher_id"] != teacher_id
                or req["skill_id"] != skill_id
                or req["status"] != "accepted"
            ):
                return jsonify({
                    "success": False,
                    "message": "A matching accepted request is required"
                }), 400

        cursor.execute("""
            INSERT INTO sessions
                (request_id, learner_id, teacher_id, skill_id,
                 duration, status)
            VALUES (%s, %s, %s, %s, %s, 'scheduled')
        """, (request_id, learner_id, teacher_id, skill_id, duration))

        session_id = cursor.lastrowid
        connection.commit()

        return jsonify({
            "success": True,
            "message": "Session created successfully",
            "session_id": session_id
        }), 201

    except Exception:
        if connection:
            connection.rollback()
        app.logger.exception("Create session failed")
        return jsonify({
            "success": False,
            "message": "Unable to create session"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# GET SESSIONS
# =========================================================

@app.route("/api/sessions/<int:student_id>", methods=["GET"])
def get_sessions(student_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT ss.*, learner.name AS learner_name,
                   teacher.name AS teacher_name, sk.skill_name
            FROM sessions ss
            JOIN students learner ON ss.learner_id = learner.id
            JOIN students teacher ON ss.teacher_id = teacher.id
            JOIN skills sk ON ss.skill_id = sk.id
            WHERE ss.learner_id = %s OR ss.teacher_id = %s
            ORDER BY ss.created_at DESC
        """, (student_id, student_id))

        sessions = cursor.fetchall()

        for session in sessions:
            if session.get("created_at"):
                session["created_at"] = session["created_at"].isoformat()

        return jsonify({
            "success": True,
            "sessions": sessions
        })

    except Exception:
        app.logger.exception("Get sessions failed")
        return jsonify({
            "success": False,
            "message": "Unable to load sessions"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# COMPLETE SESSION AND TRANSFER CREDITS
# Learner spends 10; teacher earns 10.
# All changes commit together or roll back together.
# =========================================================

@app.route(
    "/api/sessions/<int:session_id>/complete",
    methods=["POST"]
)
def complete_skill_session(session_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, learner_id, teacher_id, status
            FROM sessions
            WHERE id = %s
            FOR UPDATE
        """, (session_id,))

        session = cursor.fetchone()

        if not session:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Session not found"
            }), 404

        if session["status"] == "completed":
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Session already completed"
            }), 409

        if session["status"] != "scheduled":
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Only scheduled sessions can be completed"
            }), 400

        learner_id = session["learner_id"]
        teacher_id = session["teacher_id"]

        if learner_id == teacher_id:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Learner and teacher must be different"
            }), 400

        # Lock both student rows in consistent order.
        cursor.execute("""
            SELECT id, skill_credits
            FROM students
            WHERE id IN (%s, %s)
            ORDER BY id
            FOR UPDATE
        """, (learner_id, teacher_id))

        students = {row["id"]: row for row in cursor.fetchall()}
        learner = students.get(learner_id)
        teacher = students.get(teacher_id)

        if not learner or not teacher:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Learner or teacher not found"
            }), 404

        learner_balance = learner["skill_credits"] or 0
        teacher_balance = teacher["skill_credits"] or 0

        if learner_balance < 10:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Learner needs at least 10 credits"
            }), 400

        # Deduct 10 credits from learner.
        cursor.execute("""
            UPDATE students
            SET skill_credits = skill_credits - 10
            WHERE id = %s AND skill_credits >= 10
        """, (learner_id,))

        if cursor.rowcount != 1:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Credit deduction failed"
            }), 400

        # Add 10 credits to teacher.
        cursor.execute("""
            UPDATE students
            SET skill_credits = COALESCE(skill_credits, 0) + 10
            WHERE id = %s
        """, (teacher_id,))

        # Record learner spending.
        cursor.execute("""
            INSERT INTO credit_transactions
                (student_id, transaction_type, credits,
                 description, session_id)
            VALUES (%s, 'SPEND', 10, %s, %s)
        """, (
            learner_id,
            "Completed learning session",
            session_id
        ))

        # Record teacher earning.
        cursor.execute("""
            INSERT INTO credit_transactions
                (student_id, transaction_type, credits,
                 description, session_id)
            VALUES (%s, 'EARN', 10, %s, %s)
        """, (
            teacher_id,
            "Completed teaching session",
            session_id
        ))

        cursor.execute("""
            UPDATE sessions
            SET status = 'completed'
            WHERE id = %s AND status = 'scheduled'
        """, (session_id,))

        if cursor.rowcount != 1:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Session status update failed"
            }), 409

        # Mark associated request completed, if present.
        if session.get("request_id"):
            cursor.execute("""
                UPDATE learning_requests
                SET status = 'completed'
                WHERE id = %s AND status = 'accepted'
            """, (session["request_id"],))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Session completed and credits transferred",
            "learner_balance": learner_balance - 10,
            "teacher_balance": teacher_balance + 10
        })

    except Exception:
        if connection:
            connection.rollback()
        app.logger.exception("Session completion failed")
        return jsonify({
            "success": False,
            "message": "Unable to complete session"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# CREDIT BALANCE AND TRANSACTION HISTORY
# =========================================================

@app.route("/api/credits/<int:student_id>", methods=["GET"])
def get_credits(student_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT skill_credits
            FROM students
            WHERE id = %s
        """, (student_id,))

        student = cursor.fetchone()

        if not student:
            return jsonify({
                "success": False,
                "message": "Student not found"
            }), 404

        cursor.execute("""
            SELECT
                COALESCE(SUM(
                    CASE WHEN transaction_type = 'EARN'
                    THEN credits ELSE 0 END
                ), 0) AS earned,
                COALESCE(SUM(
                    CASE WHEN transaction_type = 'SPEND'
                    THEN credits ELSE 0 END
                ), 0) AS spent
            FROM credit_transactions
            WHERE student_id = %s
        """, (student_id,))

        totals = cursor.fetchone()

        cursor.execute("""
            SELECT transaction_type, credits, description,
                   session_id, created_at
            FROM credit_transactions
            WHERE student_id = %s
            ORDER BY id DESC
            LIMIT 10
        """, (student_id,))

        history = cursor.fetchall()

        for item in history:
            if item.get("created_at"):
                item["created_at"] = item["created_at"].isoformat()

        return jsonify({
            "success": True,
            "balance": student["skill_credits"] or 0,
            "earned": totals["earned"],
            "spent": totals["spent"],
            "history": history
        })

    except Exception:
        app.logger.exception("Credit summary failed")
        return jsonify({
            "success": False,
            "message": "Unable to load credits"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# ADD REVIEW
# =========================================================

@app.route("/api/reviews", methods=["POST"])
def add_review():
    data = request.get_json(silent=True) or {}

    reviewer_id = data.get("reviewer_id")
    reviewed_id = data.get("reviewed_id")
    session_id = data.get("session_id")
    rating = data.get("rating")
    comment = data.get("comment", "")

    if not reviewer_id or not reviewed_id or rating is None:
        return jsonify({
            "success": False,
            "message": "Required fields are missing"
        }), 400

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Rating must be an integer from 1 to 5"
        }), 400

    if not 1 <= rating <= 5:
        return jsonify({
            "success": False,
            "message": "Rating must be between 1 and 5"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            
INSERT INTO reviews
    (reviewer_id, reviewee_id, session_id, rating, comment)
VALUES (%s, %s, %s, %s, %s)

        """, (reviewer_id, reviewed_id, session_id, rating, comment))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Review added successfully"
        }), 201

    except Exception:
        if connection:
            connection.rollback()
        app.logger.exception("Add review failed")
        return jsonify({
            "success": False,
            "message": "Unable to add review"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# GET REVIEWS
# =========================================================

@app.route("/api/reviews/<int:student_id>", methods=["GET"])
def get_reviews(student_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT r.*, reviewer.name AS reviewer_name
            FROM reviews r
            JOIN students reviewer ON r.reviewer_id = reviewer.id
            WHERE r.reviewee_id = %s
            ORDER BY r.created_at DESC
        """, (student_id,))

        reviews = cursor.fetchall()

        for review in reviews:
            if review.get("created_at"):
                review["created_at"] = review["created_at"].isoformat()

        return jsonify({
            "success": True,
            "reviews": reviews
        })

    except Exception:
        app.logger.exception("Get reviews failed")
        return jsonify({
            "success": False,
            "message": "Unable to load reviews"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# DASHBOARD DATA
# =========================================================

@app.route("/api/dashboard/<int:student_id>", methods=["GET"])
def dashboard_data(student_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, email, bio, department, year,
                   profile_image, skill_credits
            FROM students
            WHERE id = %s
        """, (student_id,))

        student = cursor.fetchone()

        if not student:
            return jsonify({
                "success": False,
                "message": "Student not found"
            }), 404

        cursor.execute("""
            SELECT COUNT(*) AS total_skills
            FROM skills WHERE student_id = %s
        """, (student_id,))
        skill_data = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*) AS total_requests
            FROM learning_requests
            WHERE learner_id = %s OR teacher_id = %s
        """, (student_id, student_id))
        request_data = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*) AS total_sessions
            FROM sessions
            WHERE learner_id = %s OR teacher_id = %s
        """, (student_id, student_id))
        session_data = cursor.fetchone()

        cursor.execute("""
            SELECT COALESCE(AVG(rating), 0) AS average_rating
            FROM reviews WHERE reviewee_id = %s
        """, (student_id,))
        rating_data = cursor.fetchone()

        return jsonify({
            "success": True,
            "student": student,
            "stats": {
                "total_skills": skill_data["total_skills"],
                "total_requests": request_data["total_requests"],
                "total_sessions": session_data["total_sessions"],
                "average_rating": round(
                    float(rating_data["average_rating"]), 1
                )
            }
        })

    except Exception:
        app.logger.exception("Dashboard failed")
        return jsonify({
            "success": False,
            "message": "Unable to load dashboard"
        }), 500

    finally:
        close_db(cursor, connection)


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
