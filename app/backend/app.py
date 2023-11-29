import io
import json
import mimetypes
import os
from pathlib import Path
from typing import AsyncGenerator

from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from azure.search.documents import IndexDocumentsBatch
from quart import (
    Blueprint,
    Quart,
    abort,
    current_app,
    jsonify,
    make_response,
    request,
    send_file,
    send_from_directory,
)
from quart_cors import cors
from llm import chat as chatgpt
from config import config, az, logger
from utils import filename_to_id


ERROR_MESSAGE = """The app encountered an error processing your request.
If you are an administrator of the app, view the full error in the logs. See aka.ms/appservice-logs for more information.
Error type: {error_type}
"""

bp = Blueprint("routes", __name__, static_folder="static")


# ! Static files
@bp.route("/")
async def index():
    return await bp.send_static_file("index.html")


@bp.route("/redirect")
async def redirect():
    return ""


@bp.route("/favicon.ico")
async def favicon():
    return await bp.send_static_file("favicon.ico")


@bp.route("/assets/<path:path>")
async def assets(path):
    return await send_from_directory(
        Path(__file__).resolve().parent / "static" / "assets", path
    )


@bp.route("/fonts/<path:path>")
async def fonts(path):
    return await send_from_directory(
        Path(__file__).resolve().parent / "static" / "fonts", path
    )


@bp.route("/health")
async def health():
    return "Healthy", 200


# ! Blob storage request
@bp.route("/content/<path>")
async def content_file(path: str):
    # Remove page number from path, filename-1.txt -> filename.txt
    if path.find("#page=") > 0:
        path_parts = path.rsplit("#page=", 1)
        path = path_parts[0]
    logger.info(f"Opening file {path} at page {path}")
    try:
        blob = az.blob_container.get_blob_client(path).download_blob()
    except ResourceNotFoundError:
        logger.exception(f"Path not found: {path}")
        abort(404)
    if not blob.properties or not blob.properties.has_key("content_settings"):
        abort(404)
    mime_type = blob.properties["content_settings"]["content_type"]
    if mime_type == "application/octet-stream":
        mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    blob_file = io.BytesIO()
    blob.readinto(blob_file)
    blob_file.seek(0)
    return await send_file(
        blob_file, mimetype=mime_type, as_attachment=False, attachment_filename=path
    )


@bp.route("/content/sourcefiles/<path>")
async def source_file(path: str):
    logger.info(f"Opening file {path} at page {path}")
    try:
        blob = az.blob_container.get_blob_client(f"sourcefiles/{path}").download_blob()
    except ResourceNotFoundError:
        logger.exception(f"Path not found: {path}")
        abort(404)
    if not blob.properties or not blob.properties.has_key("content_settings"):
        abort(404)
    mime_type = blob.properties["content_settings"]["content_type"]
    if mime_type == "application/octet-stream":
        mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    blob_file = io.BytesIO()
    blob.readinto(blob_file)
    blob_file.seek(0)
    return await send_file(
        blob_file, mimetype=mime_type, as_attachment=False, attachment_filename=path
    )


def error_dict(error: Exception) -> dict:
    return {"error": ERROR_MESSAGE.format(error_type=type(error))}


# ! LLM API Endpoints
@bp.route("/chat", methods=["POST"])
async def chat():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415
    request_json = await request.get_json()
    context = request_json.get("context", {})
    try:
        result = await chatgpt.run(
            request_json["messages"],
            context=context,
            session_state=request_json.get("session_state"),
        )
        if isinstance(result, dict):
            return jsonify(result)
        else:
            response = await make_response(format_as_ndjson(result))
            response.timeout = None  # type: ignore
            return response
    except Exception as error:
        logger.exception(f"Exception in /chat: {error}")
        return jsonify(error_dict(error)), 500


@bp.route("/upload_documents", methods=["POST"])
async def upload_documents():
    files = await request.files
    if not files:
        return jsonify({"error": "request must be in formData"}), 400
    results = []
    for _, file in files.items():
        try:
            # 1. Upload blob
            logger.info(
                f"Uploading source file '{file.filename}' to Azure Blob Storage"
            )
            if file.filename.endswith(".v-scan"):
                v_scan = True
                file.filename = file.filename[:-7]
            else:
                v_scan = False
            file_id = filename_to_id(file.filename)
            az.blob_container.upload_blob(
                f"sourcefiles/{file.filename}",
                data=file.read(),
                overwrite=True,
                metadata={"id": file_id, "vscan": str(int(v_scan))},
            )
            # 2. Send message to the queue
            logger.info(f"Sending message to the queue for file '{file.filename}'")
            az.queue.send_message(
                json.dumps(
                    {
                        "filename": file.filename,
                        "sourcefile": f"sourcefiles/{file.filename}",
                        "id": file_id,
                        "v-scan": v_scan,
                    }
                )
            )
            results.append({"filename": file.filename, "success": True})
        except Exception as error:
            logger.error(f"Exception in /upload_document: {error}")
            results.append({"filename": file.filename, "error": str(error)})
    return jsonify(results)


async def format_as_ndjson(r: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    """Used to format response for streaming"""
    try:
        async for event in r:
            if not isinstance(event, dict):
                event = dict(event)
                event["choices"] = [dict(c) for c in event["choices"]]
                for choice in event["choices"]:
                    choice["delta"] = dict(choice["delta"])
            yield json.dumps(event, ensure_ascii=False) + "\n"
    except Exception as e:
        logger.exception(f"Exception while generating response stream: {e}")
        yield json.dumps(error_dict(e))


# ! No-LLM API Endpoints
@bp.route("/get_docs_info", methods=["GET"])
async def get_docs_info():
    try:
        results = await az.search_client.search(
            search_text="*",
            select="title, category, content, sourcefile, id",
            filter="is_summary eq true",
        )
        res = []
        async for result in results:
            result["filename"] = result.pop("sourcefile")
            result["summary"] = result.pop("content")
            res.append(result)
        return jsonify(res)
    except Exception as error:
        logger.exception(f"Exception in /get_docs_info: {error}")
        return jsonify(error_dict(error)), 500


@bp.route("/delete_documents", methods=["DELETE"])
async def delete_documents():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415
    request_json = await request.get_json()
    if "filename" not in request_json:
        return jsonify({"error": "filename is required"}), 400
    filename = request_json["filename"]
    logger.info(f"Looking for documents from file: {filename}")
    filter_ = f"sourcefile eq '{filename}'"
    try:
        batch = IndexDocumentsBatch()
        results = await az.search_client.search(
            search_text="*", select="id", filter=filter_
        )
        async for result in results:
            batch.add_delete_actions(result)
        logger.info(f"Found {len(batch.actions)} documents to delete")

        logger.info(f"Deleting documents from file: {filename}")
        await az.search_client.index_documents(batch)

        # Validating
        results = await az.search_client.search(
            search_text="*", select="id", filter=filter_
        )
        return jsonify({"success": True}), 200
    except HttpResponseError as ex:
        if "No indexing actions found in the request" in str(ex):
            return jsonify({"success": True}), 200
        else:
            raise ex
    except Exception as error:
        logger.exception(f"Exception in /delete_documents: {error}")
        return jsonify(error_dict(error)), 500


# ! Auth
@bp.route("/auth_setup", methods=["GET"])
def auth_setup():
    """Turned Off"""
    return jsonify(
        {
            "useLogin": False,
            "loginRequest": {"scopes": []},
            "loginRequest": {"scopes": []},
        }
    )


@bp.before_app_serving
async def configure():
    az.configure_clients()
    az.create_search_index()


def create_app():
    app = Quart(__name__)
    app.register_blueprint(bp)

    if allowed_origin := os.getenv("ALLOWED_ORIGIN"):
        app.logger.info(f"CORS enabled for {allowed_origin}")
        cors(app, allow_origin=allowed_origin, allow_methods=["GET", "POST"])
    return app
