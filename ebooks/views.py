from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import Ebook
from .forms import EbookForm
from .utils import extract_text_from_pdf, generate_audiobook, generate_timed_lyrics, generate_timed_lyrics_based_on_duration
from moviepy import AudioFileClip
import os
from django.conf import settings
import logging
import threading
import time

logger = logging.getLogger(__name__)

def process_ebook_background(ebook):
    """Process ebook in background thread."""
    print(f"Starting background processing for ebook {ebook.pk}")
    try:
        print("Extracting text...")
        extract_text_from_pdf(ebook)
        print(f"Text extracted: {len(ebook.extracted_text or '')} chars")
        print("Generating audiobook...")
        generate_audiobook(ebook, voice_style=ebook.voice_style, accent=ebook.accent)
        if ebook.audio_file:
            ebook.processing_status = 'completed'
            print("Processing completed successfully")
        else:
            ebook.processing_status = 'failed'
            print("Processing failed: no audio file")
        ebook.save()
        logger.info(f"Background processing completed for ebook {ebook.pk}")
    except Exception as e:
        ebook.processing_status = 'failed'
        ebook.progress = 0
        ebook.save()
        print(f"Background processing failed for ebook {ebook.pk}: {e}")
        logger.error(f"Background processing failed for ebook {ebook.pk}: {e}")

def upload_ebook(request):
    if request.method == 'POST':
        form = EbookForm(request.POST, request.FILES, user=request.user if request.user.is_authenticated else None)
        if form.is_valid():
            try:
                ebook = form.save()
                ebook.processing_status = 'processing'
                ebook.progress = 0
                ebook.save()
                
                # Start background processing
                thread = threading.Thread(target=process_ebook_background, args=(ebook,))
                thread.daemon = True
                thread.start()
                
                messages.success(request, f'Upload started! "{ebook.title}" is being processed with {ebook.get_voice_style_display()} voice.')
                return redirect('ebook_detail', pk=ebook.pk)
            except Exception as e:
                logger.error(f'Error uploading ebook: {str(e)}')
                messages.error(request, f'Upload failed: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EbookForm(user=request.user if request.user.is_authenticated else None)
    
    return render(request, 'ebooks/upload.html', {'form': form})

def ebook_list(request):
    if request.user.is_authenticated:
        ebooks = Ebook.objects.filter(uploaded_by=request.user).order_by('-upload_date')
    else:
        ebooks = Ebook.objects.all().order_by('-upload_date')
    
    return render(request, 'ebooks/list.html', {'ebooks': ebooks})

def ebook_detail(request, pk):
    if request.user.is_authenticated:
        ebook = get_object_or_404(Ebook, pk=pk, uploaded_by=request.user)
    else:
        ebook = get_object_or_404(Ebook, pk=pk)

    # Generate lyrics if they don't exist and we have extracted text, or regenerate if needed
    if ebook.extracted_text and ebook.audio_file:
        try:
            # Get actual audio duration
            audio_path = os.path.join(settings.MEDIA_ROOT, ebook.audio_file.name)
            if os.path.exists(audio_path):
                audio_clip = AudioFileClip(audio_path)
                total_duration = audio_clip.duration
                audio_clip.close()

                lyrics_data = generate_timed_lyrics_based_on_duration(ebook.extracted_text, total_duration)
                ebook.lyrics = lyrics_data
                ebook.save()
                logger.info(f"Generated/updated lyrics for ebook {ebook.pk}: {len(lyrics_data)} lines, duration: {total_duration}s")
            else:
                # Fallback to estimated timing
                lyrics_data = generate_timed_lyrics(ebook.extracted_text)
                ebook.lyrics = lyrics_data
                ebook.save()
                logger.info(f"Generated/updated lyrics (estimated) for ebook {ebook.pk}: {len(lyrics_data)} lines")
        except Exception as e:
            logger.error(f"Error generating lyrics for ebook {ebook.pk}: {e}")
            # Don't fail the page load, just log the error

    if request.method == 'POST' and 'regenerate' in request.POST:
        # Handle regeneration with new voice/accent
        voice_style = request.POST.get('voice_style')
        accent = request.POST.get('accent')
        if voice_style and accent:
            ebook.voice_style = voice_style
            ebook.accent = accent
            ebook.processing_status = 'processing'
            ebook.progress = 0
            ebook.save()

            # Start background regeneration
            thread = threading.Thread(target=process_ebook_background, args=(ebook,))
            thread.daemon = True
            thread.start()

            messages.success(request, f'Regenerating audio with {ebook.get_voice_style_display()} voice and {ebook.get_accent_display()} accent.')
            return redirect('ebook_detail', pk=ebook.pk)

    if request.method == 'POST' and 'upload_background' in request.POST:
        # Handle background file uploads
        background_animation = request.FILES.get('background_animation')
        background_voice = request.FILES.get('background_voice')

        if background_animation:
            ebook.background_animation = background_animation
            messages.success(request, 'Background animation uploaded successfully.')
        if background_voice:
            ebook.background_voice = background_voice
            messages.success(request, 'Background voice uploaded successfully.')

        if background_animation or background_voice:
            ebook.save()
            return redirect('ebook_detail', pk=ebook.pk)
        else:
            messages.warning(request, 'Please select at least one file to upload.')

    # Create form for regeneration
    from .forms import RegenerateForm
    regenerate_form = RegenerateForm(initial={'voice_style': ebook.voice_style, 'accent': ebook.accent})

    return render(request, 'ebooks/detail.html', {'ebook': ebook, 'regenerate_form': regenerate_form})

def check_processing_status(request, pk):
    """AJAX endpoint to check processing status"""
    ebook = get_object_or_404(Ebook, pk=pk)
    return JsonResponse({
        'status': ebook.processing_status,
        'has_audio': bool(ebook.audio_file),
        'progress': ebook.progress
    })

def delete_ebook(request, pk):
    """Delete entire ebook and all associated files"""
    if request.user.is_authenticated:
        ebook = get_object_or_404(Ebook, pk=pk, uploaded_by=request.user)
    else:
        ebook = get_object_or_404(Ebook, pk=pk)

    if request.method == 'POST':
        title = ebook.title
        # Delete associated files
        if ebook.pdf_file:
            ebook.pdf_file.delete(save=False)
        if ebook.audio_file:
            ebook.audio_file.delete(save=False)

        # Delete the ebook record
        ebook.delete()
        messages.success(request, f'Ebook "{title}" and all associated files have been permanently deleted.')

    return redirect('ebook_list')
