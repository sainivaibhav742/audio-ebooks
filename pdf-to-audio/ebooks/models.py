from django.db import models
from django.contrib.auth.models import User

class Ebook(models.Model):
    VOICE_STYLES = [
        ('storytelling', 'Storytelling (Natural)'),
        ('narration', 'Clear Narration'),
        ('calm', 'Calm & Slow'),
        ('energetic', 'Energetic'),
        ('dramatic', 'Dramatic'),
        ('whisper', 'Whisper'),
        ('excited', 'Excited'),
        ('monotone', 'Monotone'),
        ('formal', 'Formal'),
    ]

    ACCENT_CHOICES = [
        ('us', 'US English'),
        ('uk', 'British English'),
        ('au', 'Australian English'),
        ('ca', 'Canadian English'),
        ('in', 'Indian English'),
        ('ie', 'Irish English'),
        ('za', 'South African English'),
        ('nz', 'New Zealand English'),
    ]
    
    title = models.CharField(max_length=200)
    pdf_file = models.FileField(upload_to='uploads/')
    extracted_text = models.TextField(blank=True)
    audio_file = models.FileField(upload_to='uploads/', blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    processing_status = models.CharField(max_length=20, default='uploaded', choices=[
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    progress = models.IntegerField(default=0)
    voice_style = models.CharField(max_length=20, choices=VOICE_STYLES, default='storytelling')
    accent = models.CharField(max_length=2, choices=ACCENT_CHOICES, default='us')
    lyrics = models.JSONField(blank=True, null=True)  # Store timed lyrics as list of {"time": seconds, "text": "line"}
    background_animation = models.FileField(upload_to='uploads/', blank=True, null=True)
    background_voice = models.FileField(upload_to='uploads/', blank=True, null=True)

    def __str__(self):
        return self.title
