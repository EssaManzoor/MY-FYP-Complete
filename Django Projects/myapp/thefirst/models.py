from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# --- 1. EXISTING PROJECT MODEL (YOUR CORE CODE) ---
class Project(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]

    title = models.CharField(max_length=300)
    student_name = models.CharField(max_length=200)
    pdf_file = models.FileField(upload_to='fyp/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    similarity_score = models.FloatField(default=0)
    similar_project = models.CharField(max_length=300, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    teacher_comments = models.TextField(blank=True)

    # --- CACHING FIELDS FOR VISUAL REPORTING & PLAGIARISM LOGS ---
    chart_pages_json = models.TextField(blank=True, null=True)   # Stores page-by-page trend data
    chart_files_json = models.TextField(blank=True, null=True)   # Stores distribution across top reference files
    detailed_logs_json = models.TextField(blank=True, null=True) # Stores complete array of document matches

    def __str__(self):
        return self.title


# --- 2. NEW ROLE PROFILE MODEL (FOR LOGIN SYSTEM) ---
class Profile(models.Model):
    ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('TEACHER', 'Teacher'),
    ]
    # Link directly to Django's built-in User table (Handles username/password)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STUDENT')

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


# --- 3. AUTOMATIC SIGNALS (SAFEGUARDED FROM PROFILE MISSING ERRORS) ---
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # ✨ FIX: Check if profile exists before trying to save it
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # If an old user logs in and lacks a profile record, build it on the spot
        Profile.objects.create(user=instance)