import os
import io
import json
import requests
import pypdf
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Project
from ai.chunker import split_text
from ai.embeddings import create_embedding
from ai.vector_store import search_embedding

# 🚀 IMPORT YOUR NEW TEMPLATE FILTER LAYERS
from .template_filter import filter_boilerplate_chunks


# --- 🛡️ ROLE SECURITY DECORATOR ---
def teacher_only(view_func):
    @login_required(login_url='login')
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.role == 'TEACHER':
            return view_func(request, *args, **kwargs)
        raise PermissionDenied  # Triggers a safe 403 Forbidden screen
    return _wrapped_view


# --- 🔑 AUTHENTICATION & PORTAL GATEWAYS ---

def login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.role == 'TEACHER':
            return redirect('teacher_dashboard')
        return redirect('compare_document')

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                
                if hasattr(user, 'profile') and user.profile.role == 'TEACHER':
                    return redirect('teacher_dashboard')
                return redirect('compare_document')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
        
    return render(request, "thefirst/login.html", {"form": form})


def signup_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.role == 'TEACHER':
            return redirect('teacher_dashboard')
        return redirect('compare_document')

    if request.method == "POST":
        uname = request.POST.get('username', '').strip()
        pword = request.POST.get('password', '')
        pword_confirm = request.POST.get('password_confirm', '')
        selected_role = request.POST.get('role', 'STUDENT')
        teacher_key = request.POST.get('teacher_key', '').strip()

        error_context = {
            "typed_username": uname,
            "selected_role": selected_role,
            "typed_teacher_key": teacher_key
        }

        if not uname or not pword:
            messages.error(request, "All fields are required.")
            return render(request, "thefirst/signup.html", error_context)

        if pword != pword_confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, "thefirst/signup.html", error_context)

        if User.objects.filter(username=uname).exists():
            messages.error(request, "Username is already taken.")
            return render(request, "thefirst/signup.html", error_context)

        if selected_role == 'TEACHER' and teacher_key != "faculty123":
            messages.error(request, "Invalid Teacher Secret Key! Authorization failed.")
            return render(request, "thefirst/signup.html", error_context)

        user = User.objects.create_user(username=uname, password=pword)
        user.profile.role = selected_role
        user.profile.save()

        messages.success(request, "Account configured! Please log in below.")
        return redirect('login')

    return render(request, "thefirst/signup.html")


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


# --- 1. STUDENT UPLOAD & SIMILARITY CHECK ---
@login_required(login_url='login')
def compare_document_view(request):
    if request.method == "POST" and request.FILES.get("uploaded_file"):
        uploaded_file = request.FILES["uploaded_file"]
        
        input_student_name = request.POST.get("student_name", "Anonymous Student")
        input_project_title = request.POST.get("project_title", "Untitled Project")
        
        file_stream = io.BytesIO(uploaded_file.read())
        
        try:
            reader = pypdf.PdfReader(file_stream)
            aggregated_results = []
            pages_chart_dict = {}
            files_chart_dict = {}
            
            # --- STAGE 1: EXTRACT ALL RAW CHUNKS WITH PAGE TRACKING ---
            all_student_chunks = []
            for page_idx, page in enumerate(reader.pages):
                student_page = page_idx + 1
                text = page.extract_text()
                if not text or not text.strip(): 
                    continue
                
                chunks = split_text(text)
                for chunk in chunks:
                    if len(chunk.strip()) < 15: 
                        continue
                    all_student_chunks.append({
                        'text': chunk,
                        'page_num': student_page
                    })
            
            # --- STAGE 2: STRIP OUT UNIVERSITY BOILERPLATE TEXT CHUNKS ---
            clean_student_chunks = filter_boilerplate_chunks(
                student_chunks=all_student_chunks,
                boilerplate_index_path='Pdf Media/boilerplate.index',
                similarity_threshold=0.75  # Masks blocks matching template structure over 75%
            )
            
            # --- STAGE 3: RUN VECTOR MATCHES ONLY ON CLEAN CONTENT ---
            for chunk_item in clean_student_chunks:
                chunk = chunk_item['text']
                student_page = chunk_item['page_num']
                
                chunk_vector = create_embedding(chunk)
                matches = search_embedding(chunk_vector, k=2)
                
                for match in matches:
                    similarity = match["similarity"]
                    source_file = match["source_file"]
                    
                    aggregated_results.append({
                        "student_page": student_page,
                        "matched_file": source_file,
                        "matched_page": match["page"],
                        "similarity": similarity,
                        "text_snippet": match["text"][:1000]  # Expanded slice to capture whole context block
                    })
                    pages_chart_dict[student_page] = max(pages_chart_dict.get(student_page, 0), similarity)
                    files_chart_dict[source_file] = max(files_chart_dict.get(source_file, 0), similarity)
            
            # Sort all hits structural matching across the repository
            aggregated_results = sorted(aggregated_results, key=lambda x: x['similarity'], reverse=True)
            
            # 🛡️ Diversity Heuristic implementation
            filtered_results = []
            page_slots = {}
            
            for match in aggregated_results:
                page_num = match["student_page"]
                if page_num not in page_slots:
                    page_slots[page_num] = 0
                
                # Cap maximum display elements allocated to an individual document section/page
                if page_slots[page_num] < 2:
                    filtered_results.append(match)
                    page_slots[page_num] += 1
            
            final_top_10 = filtered_results[:10]
            
            peak_score = max(pages_chart_dict.values()) if pages_chart_dict else 0.0
            top_matching_file = final_top_10[0]["matched_file"] if final_top_10 else "None"
            
            sorted_pages = sorted(pages_chart_dict.items())
            chart_pages_labels = [f"Page {p}" for p, _ in sorted_pages]
            chart_pages_data = [sim for _, sim in sorted_pages]
            
            sorted_files = sorted(files_chart_dict.items(), key=lambda x: x[1], reverse=True)[:5]
            chart_files_labels = [f[:25] + "..." if len(f) > 25 else f for f, _ in sorted_files] 
            chart_files_data = [sim for _, sim in sorted_files]

            pages_json_payload = {"labels": chart_pages_labels, "data": chart_pages_data}
            files_json_payload = {"labels": chart_files_labels, "data": chart_files_data}
            
            uploaded_file.seek(0)
            new_project = Project.objects.create(
                title=input_project_title,
                student_name=input_student_name,
                pdf_file=uploaded_file,
                similarity_score=peak_score,
                similar_project=top_matching_file[:300],
                chart_pages_json=json.dumps(pages_json_payload),
                chart_files_json=json.dumps(files_json_payload),
                detailed_logs_json=json.dumps(final_top_10)
            )
            
            request.session['rendered_project_id'] = new_project.pk
            return redirect(request.path)
            
        except Exception as e:
            return render(request, "thefirst/upload.html", {"error": f"Error processing PDF: {e}"})

    context = {}
    saved_project_id = request.session.pop('rendered_project_id', None)
    
    if saved_project_id:
        project = get_object_or_404(Project, pk=saved_project_id)
        pages_chart = json.loads(project.chart_pages_json) if project.chart_pages_json else {"labels": [], "data": []}
        files_chart = json.loads(project.chart_files_json) if project.chart_files_json else {"labels": [], "data": []}
        detailed_logs = json.loads(project.detailed_logs_json) if project.detailed_logs_json else []
        
        context = {
            "project": project,
            "results": detailed_logs[:10],
            "chart_pages_labels": pages_chart.get("labels", []),
            "chart_pages_data": pages_chart.get("data", []),
            "chart_files_labels": files_chart.get("labels", []),
            "chart_files_data": files_chart.get("data", []),
        }

    return render(request, "thefirst/upload.html", context)


# --- 2. THE MAIN TEACHER DASHBOARD VIEW ---
@teacher_only
def teacher_dashboard_view(request):
    submissions = Project.objects.all().order_by('-uploaded_at')
    return render(request, "thefirst/teacher_dashboard.html", {"submissions": submissions})


# --- 3. INDIVIDUAL REVIEW & ANALYTICS VIEW ---
@teacher_only
def project_review_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    pages_chart = json.loads(project.chart_pages_json) if project.chart_pages_json else {"labels": [], "data": []}
    files_chart = json.loads(project.chart_files_json) if project.chart_files_json else {"labels": [], "data": []}
    detailed_logs = json.loads(project.detailed_logs_json) if project.detailed_logs_json else []
    
    context = {
        "project": project,
        "chart_pages_labels": pages_chart.get("labels", []),
        "chart_pages_data": pages_chart.get("data", []),
        "chart_files_labels": files_chart.get("labels", []),
        "chart_files_data": files_chart.get("data", []),
        "results": detailed_logs[:10],
    }
    return render(request, "thefirst/project_review.html", context)


# --- 4. TEACHER DECISION ENDPOINT ---
@teacher_only
def update_submission_status(request, pk):
    if request.method == "POST":
        project = get_object_or_404(Project, pk=pk)
        action = request.POST.get("action")
        comments = request.POST.get("remarks", "")
        
        if action == "ACCEPT":
            project.status = "Accepted"
            project.teacher_comments = comments
            project.save()
            
            try:
                from ai.vector_store import add_document_to_index
                add_document_to_index(project.pdf_file.path, source_filename=project.title)
                messages.success(request, f"Approved and automatically indexed into FAISS: {project.title}")
            except Exception as e:
                messages.error(request, f"Database updated to Accepted, but AI Indexing failed: {e}")
            
        elif action == "REJECT":
            project_title = project.title
            
            if project.pdf_file:
                project.pdf_file.delete(save=False)
                
            project.delete() 
            messages.warning(request, f"Rejected and permanently removed from storage: {project_title}")
        
    return redirect("teacher_dashboard")


# --- 🧠 5. INTERACTIVE LLM EVALUATION ASSISTANT ---
@teacher_only
def get_ai_insight(request, project_id):
    """
    Handles background AJAX queries from the teacher panel targeting Llama 3 
    running on the local machine via Ollama.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid HTTP request method"}, status=400)

    try:
        # Load user query from JavaScript fetch interface payload
        body_data = json.loads(request.body)
        user_prompt = body_data.get("prompt", "").strip()
        
        # Grab target record using the verified model identifier
        project = get_object_or_404(Project, pk=project_id)
        
        if not user_prompt:
            return JsonResponse({"error": "Query prompt cannot be blank."}, status=400)

        # Inject runtime context variables straight into system generation layer
        system_context = f"""
        You are an AI Academic Integrity Assistant built for a university FYP Supervisor Evaluation Panel.
        You are reviewing the project proposal titled: "{project.title}" submitted by student: "{project.student_name}".
        The system detected a peak similarity score of {project.similarity_score}%.
        
        Answer the teacher's query accurately based on general academic principles and this metadata. 
        Keep your response concise, clear, and professional.
        """

        # Dispatch execution payload directly to local background listener
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3",
            "prompt": f"{system_context}\n\nTeacher Question: {user_prompt}\nAssistant Response:",
            "stream": False
        }

        response = requests.post(url, json=payload, timeout=40)
        
        if response.status_code == 200:
            ai_response = response.json().get("response", "").strip()
            return JsonResponse({"status": "success", "response": ai_response})
        else:
            return JsonResponse({"error": "Local Ollama server returned an invalid operational status code."}, status=500)

    except requests.exceptions.ConnectionError:
        return JsonResponse({"error": "Could not connect to Ollama. Ensure 'ollama run llama3' is active in your terminal."}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Internal system parsing failure: {str(e)}"}, status=500)