from flask import Blueprint, jsonify

job_bp = Blueprint("job_bp", __name__)

@job_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Job routes is working perfectly ✅"})


