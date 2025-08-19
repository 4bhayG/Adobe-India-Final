import shutil
from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse, Http404
import mimetypes
from dotenv import load_dotenv
import os 
import re
import logging
import threading
import time

from backend.feature.genai_util import process_document
from backend.feature.podcast import create_audio

# --- Session processing state ---
session_processing_results = {}
session_processing_threads = {}
session_processing_locks = {}

# ADD THIS: Global lock for thread-safe dictionary access
processing_data_lock = threading.Lock()

def process_pdf_for_session(session_id):
    """Process the PDF for a session and store the result + generate podcast automatically."""
    past_folder = get_session_folder(session_id, "past")
    current_folder = get_session_folder(session_id, "current")
    file_name = None
    
    # Always get the filename from the current folder
    if os.path.exists(current_folder):
        for f in os.listdir(current_folder):
            if f.lower().endswith('.pdf'):
                file_name = f
                break
    
    if not file_name:
        with processing_data_lock:
            session_processing_results[session_id] = {"error": "No PDF file found in session current folder."}
        return
    
    try:
        # Always search for the JSON in the past folder's temp_files
        results, text = process_document(past_folder, file_name)
        if not results:
            with processing_data_lock:
                session_processing_results[session_id] = {"error": "Invalid Document or file name"}
        else:
            # Store insights results - THREAD SAFE
            with processing_data_lock:
                session_processing_results[session_id] = {
                    "results": results, 
                    "text": text,
                    "file_name": file_name
                }
            
            # NEW: Automatically generate podcast after insights are ready
            try:
                audio_dir = os.path.join(past_folder, "audio_files")
                os.makedirs(audio_dir, exist_ok=True)
                audio_loc = os.path.join(audio_dir, file_name.replace('.pdf', '.mp3'))
                
                print(f"info - Generating podcast for session {session_id}")
                create_audio(f"{text} \n {results}", audio_loc)
                
                # Update with podcast path - THREAD SAFE
                with processing_data_lock:
                    if session_id in session_processing_results:
                        session_processing_results[session_id]['podcast'] = audio_loc
                print(f"info - Podcast generated successfully for session {session_id}")
                
            except Exception as e:
                print(f"error - Failed to generate podcast for session {session_id}: {e}")
                with processing_data_lock:
                    if session_id in session_processing_results:
                        session_processing_results[session_id]['podcast_error'] = str(e)
                
    except Exception as e:
        with processing_data_lock:
            session_processing_results[session_id] = {"error": str(e)}
    finally:
        # Release lock if present - THREAD SAFE 
        with processing_data_lock:
            lock = session_processing_locks.get(session_id)
            if lock:
                lock.release()
            # Remove thread reference for this session
            if session_id in session_processing_threads:
                del session_processing_threads[session_id]

logger = logging.getLogger(__name__)

load_dotenv()

from .models import PdfFile
from .serializers import PdfFileSerializer

# Assuming main_functionality is in this path
from backend.feature.base_feature import create_output_json, main_functionality

# --- Session-based file management config ---
SESSION_BASE_DIR = os.path.join(settings.MEDIA_ROOT, "PDFsUploaded", "sessions")
SESSION_TIMEOUT_SECONDS = 60 * 60  # 1 hour
CLEANUP_INTERVAL_SECONDS = 10 * 60  # 10 minutes

def get_session_id(request):
    session_id = request.META.get('HTTP_X_SESSION_ID')
    if not session_id:
        raise ValueError("Session ID (x-session-id) header is required.")
    # Sanitize session_id to avoid path traversal
    session_id = re.sub(r'[^a-zA-Z0-9_-]', '_', session_id)
    return session_id

def get_session_folder(session_id, category):
    # category: 'current', 'past', etc.
    return os.path.join(SESSION_BASE_DIR, session_id, category)

def get_temp_files_folder(session_id):
    return os.path.join(SESSION_BASE_DIR, session_id, "past", "temp_files")

def update_last_accessed(session_id):
    session_dir = os.path.join(SESSION_BASE_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    last_accessed_path = os.path.join(session_dir, "last_accessed.txt")
    with open(last_accessed_path, "w") as f:
        f.write(str(int(time.time())))

def get_last_accessed(session_dir):
    last_accessed_path = os.path.join(session_dir, "last_accessed.txt")
    try:
        with open(last_accessed_path, "r") as f:
            return int(f.read().strip())
    except Exception:
        return None

def cleanup_sessions():
    while True:
        try:
            now = int(time.time())
            if not os.path.exists(SESSION_BASE_DIR):
                time.sleep(CLEANUP_INTERVAL_SECONDS)
                continue
            for session_id in os.listdir(SESSION_BASE_DIR):
                session_dir = os.path.join(SESSION_BASE_DIR, session_id)
                if not os.path.isdir(session_dir):
                    continue
                last_accessed = get_last_accessed(session_dir)
                if last_accessed is None:
                    continue
                if now - last_accessed > SESSION_TIMEOUT_SECONDS:
                    try:
                        shutil.rmtree(session_dir)
                        print("info - " + f"Session {session_id} expired and removed.")
                    except Exception as e:
                        print("error - " + f"Failed to remove session {session_id}: {e}")
        except Exception as e:
            print("error - " + f"Error in session cleanup thread: {e}")
        time.sleep(CLEANUP_INTERVAL_SECONDS)

# Start cleanup thread on import
cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
cleanup_thread.start()

def frontend_static_render(request):
    """ Server Frontend Application"""
    try:
        with open(os.path.join(settings.BASE_DIR , 'static' , 'index.html') , 'r') as f:
            return HttpResponse(f.read())
    except FileNotFoundError:
        return HttpResponse("Frontend not built yet", status=404)

import os, re

def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        return ""

    filename = os.path.basename(name)
    base, _ = os.path.splitext(filename)  

    base = base.lower()
    base = re.sub(r"[^a-z0-9]+", "_", base)   
    base = re.sub(r"^_+|_+$", "", base)       

    return base + ".pdf"

# This view remains unchanged
def home(req):
    return HttpResponse("Hello Adobe")

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def uploadPdf(request):
    try:
        session_id = get_session_id(request)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    update_last_accessed(session_id)

    # Define session-specific folder paths
    current_folder = get_session_folder(session_id, "current")
    past_folder = get_session_folder(session_id, "past")
    temp_files_folder = get_temp_files_folder(session_id)

    # Helper to clear a folder
    def clear_folder(folder_path):
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print("error - " + f"Failed to delete {file_path}. Reason: {e}")

    # 1. Clear old data from session folder only
    clear_folder(current_folder)
    clear_folder(past_folder)
    os.makedirs(current_folder, exist_ok=True)
    os.makedirs(past_folder, exist_ok=True)
    os.makedirs(temp_files_folder, exist_ok=True)

    # CLEAR OLD PROCESSING RESULTS for this session when new PDFs are uploaded - THREAD SAFE
    with processing_data_lock:
        if session_id in session_processing_results:
            del session_processing_results[session_id]
            print(f"info - Cleared old processing results for session {session_id}")

    # 2. Get uploaded files and form data
    current_files = request.FILES.getlist('files_current')
    past_files = request.FILES.getlist('files_past')

    if not current_files:
        return Response({"error": "No current PDF was uploaded."}, status=status.HTTP_400_BAD_REQUEST)

    # 3. Save files to the session-specific filesystem (not DB)
    for file in current_files:
        file.name = normalize_name(file.name)
        with open(os.path.join(current_folder, file.name), 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

    for file in past_files:
        file.name = normalize_name(file.name)
        with open(os.path.join(past_folder, file.name), 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

    print("File Upload Successful")

    # Create JSON files for PDFs in both current and past folders
    for folder in [current_folder, past_folder]:
        pdf_files = [f for f in os.listdir(folder) if f.lower().endswith('.pdf')]
        for item in pdf_files:
            full_item_path = os.path.join(folder, item)
            create_output_json(full_item_path, temp_files_folder)

    # Start background thread to process insights for this session
    def start_processing_thread():
        # ALWAYS START NEW THREAD - THREAD SAFE
        with processing_data_lock:
            if session_id in session_processing_threads and session_processing_threads[session_id].is_alive():
                print(f"info - Stopping existing processing thread for session {session_id}")
        
        lock = threading.Lock()
        with processing_data_lock:
            session_processing_locks[session_id] = lock
        lock.acquire()
        
        t = threading.Thread(target=process_pdf_for_session, args=(session_id,), daemon=True)
        with processing_data_lock:
            session_processing_threads[session_id] = t
        t.start()
        print(f"info - Started new processing thread for session {session_id}")
        
    start_processing_thread()

    return Response({
        "message": "Files Stored Successfully. Processing started in background."
    }, status=status.HTTP_200_OK)

#Send Pdf and Text Logic
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def Get_Relevant_Topics(request):
    try:
        session_id = get_session_id(request)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    update_last_accessed(session_id)

    files_past_path = get_session_folder(session_id, "past")
    files_current_path = get_session_folder(session_id, "current")
    json_folder = get_temp_files_folder(session_id)

    user_text = request.data.get("selected_text")
    print(user_text)

    if not user_text:
        return Response({
            "error": "The 'selected_text' field is required and cannot be empty."
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        os.makedirs(json_folder, exist_ok=True)
        os.makedirs(files_current_path, exist_ok=True)

        result_data = main_functionality(
            json_folder=json_folder,
            text=user_text,
            input_dir=files_past_path,
            curr_dir=files_current_path
        )

        if result_data and result_data.get("extracted_sections"):
            return Response(result_data, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "Analysis completed, but no relevant sections were found.",
                "extracted_sections": []
            }, status=status.HTTP_200_OK)

    except Exception as e:
        print("error - " + f"An unexpected error occurred in Get_Relevant_Topics view: {e}", exc_info=True)
        return Response({
            "error": "An unexpected error occurred on the server during document analysis."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Generate insights
@api_view(['GET'])
@parser_classes([MultiPartParser, FormParser])
def generate_insights(request):
    try:
        session_id = get_session_id(request)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    update_last_accessed(session_id)

    # If already processed, return result - THREAD SAFE
    with processing_data_lock:
        if session_id in session_processing_results:
            result = session_processing_results[session_id]
            if "results" in result:
                return Response(result["results"], status=status.HTTP_201_CREATED)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

    # If processing thread is running, wait for it - THREAD SAFE
    with processing_data_lock:
        lock = session_processing_locks.get(session_id)
    if lock:
        lock.acquire()
        lock.release()
        # After thread finishes, return result - THREAD SAFE
        with processing_data_lock:
            result = session_processing_results.get(session_id)
        if result and "results" in result:
            return Response(result["results"], status=status.HTTP_201_CREATED)
        else:
            return Response(result or {"error": "Processing failed."}, status=status.HTTP_400_BAD_REQUEST)

    # If not started, start processing synchronously
    process_pdf_for_session(session_id)
    with processing_data_lock:
        result = session_processing_results.get(session_id)
    if result and "results" in result:
        return Response(result["results"], status=status.HTTP_201_CREATED)
    else:
        return Response(result or {"error": "Processing failed."}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def podcast(request):
    try:
        session_id = get_session_id(request)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    update_last_accessed(session_id)

    # Retrieve the file_name just as in process_pdf_for_session
    current_folder = get_session_folder(session_id, "current")
    file_name = None
    if os.path.exists(current_folder):
        for f in os.listdir(current_folder):
            if f.lower().endswith('.pdf'):
                file_name = f
                break

    if not file_name:
        return Response({"error": "No PDF file found in session current folder."}, status=status.HTTP_400_BAD_REQUEST)

    past_folder = get_session_folder(session_id, "past")
    audio_dir = os.path.join(past_folder, "audio_files")
    os.makedirs(audio_dir, exist_ok=True)
    audio_loc = os.path.join(audio_dir, file_name.replace('.pdf', '.mp3'))

    # Wait for insight thread to finish if it is running - THREAD SAFE
    with processing_data_lock:
        lock = session_processing_locks.get(session_id)
    if lock:
        print(f"info - Waiting for background processing to complete for session {session_id}")
        lock.acquire()
        lock.release()
        print(f"info - Background processing completed for session {session_id}")

    with processing_data_lock:
        result = session_processing_results.get(session_id)

    # Case 1: Podcast already generated
    if result and "podcast" in result and result["podcast"] and os.path.exists(result["podcast"]):
        print(f"info - Returning pre-generated podcast for session {session_id}")
        audio_file_path = result["podcast"]
        
    # Case 2: Insights ready; podcast not generated
    elif result and "results" in result and "text" in result:
        try:
            print(f"info - Generating podcast on-demand for session {session_id}")
            create_audio(f"{result['text']} \n {result['results']}", audio_loc)
            with processing_data_lock:
                session_processing_results[session_id]["podcast"] = audio_loc
            audio_file_path = audio_loc
        except Exception as e:
            print(f"error - Failed to generate podcast for session {session_id}: {e}")
            return Response({
                "error": f"Failed to generate audio: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Case 3: Processing failed
    elif result and "error" in result:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    # Case 4: No processing yet - do everything now
    else:
        try:
            print(f"info - No background processing found, processing manually for session {session_id}")
            results, text = process_document(past_folder, file_name)
            if not results:
                return Response({"error": "Invalid Document or file name"}, status=status.HTTP_400_BAD_REQUEST)
            create_audio(f"{text} \n {results}", audio_loc)
            with processing_data_lock:
                session_processing_results[session_id] = {
                    "results": results,
                    "text": text,
                    "podcast": audio_loc,
                    "file_name": file_name
                }
            audio_file_path = audio_loc
        except Exception as e:
            print(f"error - Manual podcast generation failed for session {session_id}: {e}")
            return Response({
                "error": f"Failed to process document or generate audio: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Return the actual audio file
    try:
        if os.path.exists(audio_file_path):
            # Get the MIME type
            content_type, _ = mimetypes.guess_type(audio_file_path)
            if content_type is None:
                content_type = 'audio/mpeg'  # Default for MP3
            
            # Create filename for download
            download_filename = f"podcast_{file_name.replace('.pdf', '.mp3')}"
            
            # Return the file as response
            response = FileResponse(
                open(audio_file_path, 'rb'),
                content_type=content_type,
                filename=download_filename
            )
            response['Content-Disposition'] = f'attachment; filename="{download_filename}"'
            return response
        else:
            return Response({
                "error": "Audio file was generated but cannot be found"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        print(f"error - Failed to serve audio file for session {session_id}: {e}")
        return Response({
            "error": f"Failed to serve audio file: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
