import os
import re
import concurrent.futures
from io import BytesIO
try:
    from PyPDF2 import PdfReader
except ImportError:
    from PyPDF2 import PdfFileReader as PdfReader
from gtts import gTTS
from moviepy import AudioFileClip, concatenate_audioclips
from django.conf import settings
import logging
import tempfile

logger = logging.getLogger(__name__)

def extract_text_from_pdf(ebook):
    """Extract text from PDF with optimized processing."""
    pdf_path = ebook.pdf_file.path
    
    try:
        reader = PdfReader(pdf_path)
        text = ""
        
        # Get total pages
        if hasattr(reader, 'pages'):
            total_pages = len(reader.pages)
            pages = reader.pages
        else:
            total_pages = reader.numPages
            pages = [reader.getPage(i) for i in range(total_pages)]
        
        # Process pages in parallel for faster extraction
        def extract_page_text(page):
            if hasattr(page, 'extract_text'):
                return page.extract_text()
            else:
                return page.extractText()
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_page = {executor.submit(extract_page_text, page): i for i, page in enumerate(pages)}
            
            page_texts = [None] * total_pages
            for future in concurrent.futures.as_completed(future_to_page):
                page_idx = future_to_page[future]
                try:
                    page_texts[page_idx] = future.result()
                except Exception as e:
                    logger.warning(f"Error extracting page {page_idx}: {e}")
                    page_texts[page_idx] = ""
        
        # Combine text in order
        text = "\n".join(filter(None, page_texts))
        
        # Clean and optimize text
        text = clean_text_for_tts(text)
        
        # Limit text length to prevent processing issues
        if len(text) > 50000:  # ~50k characters limit
            text = text[:50000] + "\n\n[Text truncated for audio processing]"
        
        ebook.extracted_text = text
        ebook.save()
        
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        raise

def clean_text_for_tts(text):
    """Clean and optimize text for better TTS processing."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Fix common PDF extraction issues
    text = re.sub(r'([a-z])([A-Z])', r'\1. \2', text)  # Add periods between sentences
    text = re.sub(r'(\d)([A-Za-z])', r'\1. \2', text)  # Number to text
    text = re.sub(r'([A-Za-z])(\d)', r'\1. \2', text)  # Text to number
    
    # Remove special characters that TTS struggles with
    text = re.sub(r'[^\w\s\.,!?;:\-\n]', '', text)
    
    # Fix line breaks
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Double line breaks for paragraphs
    text = re.sub(r'\n(?!\n)', ' ', text)    # Single line breaks to spaces
    
    # Add proper sentence endings
    text = re.sub(r'(?<=[a-z])(?=\s+[A-Z])', '.', text)
    
    return text.strip()

def generate_timed_lyrics(text):
    """Generate timed lyrics data from text."""
    # Split text into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Combine sentences into lines of approximately 10-15 words each
    lyrics_lines = []
    current_line = ""
    target_words_per_line = 12

    for sentence in sentences:
        words = sentence.split()
        if len(current_line.split()) + len(words) <= target_words_per_line:
            current_line += " " + sentence if current_line else sentence
        else:
            if current_line:
                lyrics_lines.append(current_line.strip())
            current_line = sentence

    if current_line:
        lyrics_lines.append(current_line.strip())

    lyrics = []
    current_time = 0.0
    words_per_minute = 80  # Further reduced speaking rate for better sync
    words_per_second = words_per_minute / 60.0

    for line in lyrics_lines:
        word_count = len(line.split())
        duration = word_count / words_per_second

        lyrics.append({
            'time': round(current_time, 2),
            'text': line.strip()
        })

        current_time += duration + 0.5  # Add 0.5 second pause between lines

    return lyrics

def generate_timed_lyrics_based_on_duration(text, total_duration):
    """Generate timed lyrics data based on actual audio duration."""
    # Split text into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Combine sentences into lines of approximately 10-15 words each
    lyrics_lines = []
    current_line = ""
    target_words_per_line = 12

    for sentence in sentences:
        words = sentence.split()
        if len(current_line.split()) + len(words) <= target_words_per_line:
            current_line += " " + sentence if current_line else sentence
        else:
            if current_line:
                lyrics_lines.append(current_line.strip())
            current_line = sentence

    if current_line:
        lyrics_lines.append(current_line.strip())

    # Distribute timing based on total duration
    if not lyrics_lines:
        return []

    # Calculate time per line
    time_per_line = total_duration / len(lyrics_lines)

    lyrics = []
    current_time = 0.0

    for line in lyrics_lines:
        lyrics.append({
            'time': round(current_time, 2),
            'text': line.strip()
        })
        current_time += time_per_line

    return lyrics

def generate_audiobook(ebook, voice_style='storytelling', accent='us'):
    """Generate high-quality TTS audio with customizable voice."""
    text = ebook.extracted_text
    if not text:
        return

    try:
        ebook.progress = 0
        ebook.save()

        # Voice configuration based on user preference
        accent_tlds = {
            'us': 'com',
            'uk': 'co.uk',
            'au': 'com.au',
            'ca': 'ca',
            'in': 'co.in',
            'ie': 'ie',
            'za': 'co.za',
            'nz': 'co.nz'
        }

        voice_configs = {
            'storytelling': {
                'lang': 'en',
                'tld': accent_tlds.get(accent, 'com'),
                'slow': False
            },
            'narration': {
                'lang': 'en',
                'tld': 'com',
                'slow': False
            },
            'calm': {
                'lang': 'en',
                'tld': accent_tlds.get(accent, 'co.uk'),
                'slow': True
            },
            'energetic': {
                'lang': 'en',
                'tld': accent_tlds.get(accent, 'com'),
                'slow': False
            },
            'dramatic': {
                'lang': 'en',
                'tld': accent_tlds.get(accent, 'com'),
                'slow': False
            },
            'whisper': {
                'lang': 'en',
                'tld': accent_tlds.get(accent, 'co.uk'),
                'slow': True
            },
            'excited': {
                'lang': 'en',
                'tld': accent_tlds.get(accent, 'com'),
                'slow': False
            },
            'monotone': {
                'lang': 'en',
                'tld': accent_tlds.get(accent, 'com'),
                'slow': True
            },
            'formal': {
                'lang': 'en',
                'tld': accent_tlds.get(accent, 'co.uk'),
                'slow': False
            }
        }

        config = voice_configs.get(voice_style, voice_configs['storytelling'])

        # Split text into chunks for better processing
        chunks = split_text_into_chunks(text)
        audio_segments = []

        # Process each chunk
        for i, chunk in enumerate(chunks):
            try:
                # Generate TTS for each chunk
                tts = gTTS(
                    text=chunk,
                    lang=config['lang'],
                    tld=config['tld'],
                    slow=config['slow']
                )

                # Save to temporary buffer
                buffer = BytesIO()
                tts.write_to_fp(buffer)
                buffer.seek(0)
                audio_segments.append(buffer)

                # Update progress
                ebook.progress = int((i + 1) / len(chunks) * 50)  # 50% for TTS generation
                ebook.save()

                logger.info(f"Processed chunk {i+1}/{len(chunks)}")

            except Exception as e:
                logger.warning(f"Error processing chunk {i+1}: {e}")
                continue

        if not audio_segments:
            raise Exception("No audio segments were generated")

        # Combine audio segments
        final_audio = combine_audio_segments(audio_segments)

        # Update progress
        ebook.progress = 90
        ebook.save()

        # Save final audio
        audio_filename = f"{ebook.pk}_audiobook_{voice_style}.mp3"
        audio_path = os.path.join(settings.MEDIA_ROOT, 'ebooks', 'audio', audio_filename)
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)

        with open(audio_path, 'wb') as f:
            f.write(final_audio.getvalue())

        ebook.audio_file = f"ebooks/audio/{audio_filename}"

        # Generate timed lyrics based on actual audio duration
        from moviepy import AudioFileClip
        audio_clip = AudioFileClip(audio_path)
        total_duration = audio_clip.duration
        audio_clip.close()

        lyrics_data = generate_timed_lyrics_based_on_duration(text, total_duration)
        ebook.lyrics = lyrics_data

        ebook.progress = 100
        ebook.save()

        logger.info(f"Audio generated successfully for ebook {ebook.pk}, duration: {total_duration}s, lyrics: {len(lyrics_data)} lines")

    except Exception as e:
        ebook.progress = 0
        ebook.save()
        logger.error(f"Error generating audiobook: {e}")
        raise

def split_text_into_chunks(text, max_length=4000):
    """Split text into optimal chunks for TTS processing."""
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk + paragraph) <= max_length:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # If chunks are still too long, split by sentences
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_length:
            final_chunks.append(chunk)
        else:
            sentences = re.split(r'[.!?]+', chunk)
            temp_chunk = ""
            for sentence in sentences:
                if len(temp_chunk + sentence) <= max_length:
                    temp_chunk += sentence + ". "
                else:
                    if temp_chunk:
                        final_chunks.append(temp_chunk.strip())
                    temp_chunk = sentence + ". "
            if temp_chunk:
                final_chunks.append(temp_chunk.strip())
    
    return [chunk for chunk in final_chunks if chunk.strip()]

def combine_audio_segments(segments):
    """Combine multiple audio segments into one using moviepy."""
    if not segments:
        return BytesIO()

    if len(segments) == 1:
        segments[0].seek(0)
        return segments[0]

    temp_files = []
    clips = []

    try:
        logger.info(f"Combining {len(segments)} audio segments")
        # Create temp files for each segment
        for segment in segments:
            segment.seek(0)
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_file.write(segment.read())
                temp_path = temp_file.name
            temp_files.append(temp_path)
            clips.append(AudioFileClip(temp_path, fps=24000))

        logger.info(f"Loaded {len(clips)} clips")
        # Concatenate clips
        combined = concatenate_audioclips(clips)
        logger.info("Concatenated clips")

        # Export to temp file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as output_file:
            combined.write_audiofile(output_file.name, fps=24000, codec='mp3', bitrate='128k', verbose=False, logger=None)
            output_path = output_file.name

        logger.info("Wrote combined audio")
        # Read back to BytesIO
        with open(output_path, 'rb') as f:
            output = BytesIO(f.read())

        # Clean up temp files
        for path in temp_files + [output_path]:
            try:
                os.unlink(path)
            except:
                pass

        output.seek(0)
        return output

    except Exception as e:
        logger.error(f"Error combining audio segments: {e}")
        # Clean up on error
        for path in temp_files:
            try:
                os.unlink(path)
            except:
                pass
        raise e