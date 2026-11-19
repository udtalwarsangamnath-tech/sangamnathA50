import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from postgrest import APIError
from supabase import Client, create_client

load_dotenv()

app = Flask(__name__)

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY")
supabase: Client | None = (
    create_client(supabase_url, supabase_key)
    if supabase_url and supabase_key
    else None
)


@app.after_request
def add_cors_headers(response):
    """Allow browser clients from any origin to call this API."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def database():
    if supabase is None:
        return None, (jsonify(error="Database is not configured"), 503)
    return supabase, None


def api_error(error):
    return jsonify(error=error.message), 400


@app.get("/")
def index():
    return jsonify(message="Events API"), 200


@app.get("/api/events")
def list_events():
    client, error = database()
    if error:
        return error
    try:
        result = client.table("events").select("*").execute()
        return jsonify(result.data), 200
    except APIError as exc:
        return api_error(exc)


@app.get("/api/events/<event_id>")
def get_event(event_id):
    client, error = database()
    if error:
        return error
    try:
        result = (
            client.table("events")
            .select("*")
            .eq("id", event_id)
            .maybe_single()
            .execute()
        )
        if result.data is None:
            return jsonify(error="Event not found"), 404
        return jsonify(result.data), 200
    except APIError as exc:
        return api_error(exc)


@app.post("/api/registrations")
def create_registration():
    client, error = database()
    if error:
        return error

    body = request.get_json(silent=True) or {}
    user_id = body.get("user_id")
    event_id = body.get("event_id")
    if not user_id or not event_id:
        return jsonify(error="user_id and event_id are required"), 400

    try:
        event_result = (
            client.table("events")
            .select("id, capacity")
            .eq("id", event_id)
            .maybe_single()
            .execute()
        )
        event = event_result.data
        if event is None:
            return jsonify(error="Event not found"), 404

        existing = (
            client.table("registrations")
            .select("id")
            .eq("user_id", user_id)
            .eq("event_id", event_id)
            .execute()
        )
        if existing.data:
            return jsonify(error="User is already registered for this event"), 409

        registrations = (
            client.table("registrations")
            .select("id", count="exact")
            .eq("event_id", event_id)
            .execute()
        )
        capacity = event.get("capacity")
        if capacity is not None and registrations.count is not None:
            if registrations.count >= capacity:
                return jsonify(error="Event is at capacity"), 409

        created = (
            client.table("registrations")
            .insert({"user_id": user_id, "event_id": event_id})
            .execute()
        )
        return jsonify(created.data[0]), 201
    except APIError as exc:
        return api_error(exc)


@app.get("/api/me/registrations")
def user_registrations():
    # With authentication disabled, the caller supplies the user ID explicitly.
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify(error="user_id query parameter is required"), 400

    client, error = database()
    if error:
        return error
    try:
        result = (
            client.table("registrations")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        return jsonify(result.data), 200
    except APIError as exc:
        return api_error(exc)


@app.get("/api/events/<event_id>/registrations")
def event_registrations(event_id):
    # This endpoint is public because no authentication/authorization is used.
    client, error = database()
    if error:
        return error
    try:
        result = (
            client.table("registrations")
            .select("*")
            .eq("event_id", event_id)
            .execute()
        )
        return jsonify(result.data), 200
    except APIError as exc:
        return api_error(exc)


if __name__ == "__main__":
    app.run(debug=True)
