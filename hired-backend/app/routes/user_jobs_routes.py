from flask import Blueprint, request, jsonify
from app.supabase_client import supabase

user_jobs_bp = Blueprint("user_jobs_bp", __name__)

@user_jobs_bp.route("/health", methods=["GET"])
def auth_health():
    return jsonify({"status": "User Job routes are working ✅"})

@user_jobs_bp.route("/saved-jobs", methods=["POST"])
@token_required
def save_job(user):
   if user.get("role") != "candidate":
       return jsonify({"error": "Only candidate can save jobs"}), 403


   data = request.get_json() or {}
   job_id = data.get("job_id")
   if not job_id:
       return jsonify({"error": "job_id is required"}), 400


   try:
       existing = supabase.table("saved_jobs").select("*").eq("job_id", job_id).eq("user_id", user["auth_uid"]).execute()
       if existing.data:
           return jsonify({"message": "Job already saved", "saved_job": existing.data[0]}), 200

       saved_job = {"user_id": user["auth_uid"], "job_id": job_id}
       resp = supabase.table("saved_jobs").insert(saved_job).execute()
       if resp.data:
           return jsonify({"message": "Job saved successfully", "saved_job": resp.data[0]}), 201


       return jsonify({"error": "Failed to save job"}), 500


   except Exception as e:
       return jsonify({"error": f"Failed to save job: {str(e)}"}), 500




# ---------------------------------------------
# 2. GET ALL SAVED JOBS FOR USER (expanded + pagination)
# GET /saved-jobs?page=1&page_size=10
# ---------------------------------------------
@user_jobs_bp.route("/saved-jobs", methods=["GET"])
@token_required
def get_saved_jobs(user):
   if user.get("role") != "candidate":
       return jsonify({"error": "Only candidate can view saved jobs"}), 403


   page, page_size = _get_pagination_params()
   offset = (page - 1) * page_size
   to_index = offset + page_size - 1


   try:
       # select joined job fields (only few fields) to avoid FK issues
       saved_resp = (
           supabase.table("saved_jobs")
           .select("id, job_id, saved_at, jobs(recruiter_id, company_name, title)")
           .eq("user_id", user["auth_uid"])
           .order("saved_at", desc=True)
           .range(offset, to_index)
           .execute()
       )


       total_resp = supabase.table("saved_jobs").select("id", count="exact").eq("user_id", user["auth_uid"]).execute()
       total = getattr(total_resp, "count", None) or 0


       return jsonify({
           "page": page,
           "page_size": page_size,
           "total": total,
           "saved_jobs": saved_resp.data or []
       }), 200


   except Exception as e:
       return jsonify({"error": f"Failed to fetch saved jobs: {str(e)}"}), 500




# ---------------------------------------------
# 3. REMOVE A SAVED JOB
# DELETE /saved-jobs/<saved_job_id>
# ---------------------------------------------
@user_jobs_bp.route("/saved-jobs/<saved_job_id>", methods=["DELETE"])
@token_required
def remove_saved_job(user, saved_job_id):
   if user.get("role") != "candidate":
       return jsonify({"error": "Only candidate can remove saved jobs"}), 403


   try:
       #saved_job 's id is passed and not job_id
       resp = supabase.table("saved_jobs").delete().eq("id", saved_job_id).eq("user_id", user["auth_uid"]).execute()
       if not resp.data or len(resp.data) == 0:
           return jsonify({"error": "Saved job not found"}), 404


       return jsonify({"message": "Saved job removed"}), 200


   except Exception as e:
       return jsonify({"error": f"Failed to remove saved job: {str(e)}"}), 500
