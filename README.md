# 📚🔊 Audio E-Books - PDF to Audiobook Converter

A Django web application that converts PDF documents into audiobooks with customizable voice styles, accents, and timed lyrics/subtitles.

## ✨ Features

- **PDF to Audio Conversion**: Upload PDF files and automatically convert them to audiobooks
- **Multiple Voice Styles**: Choose from 9 different narration styles:
  - Storytelling (Natural)
  - Clear Narration
  - Calm & Slow
  - Energetic
  - Dramatic
  - Whisper
  - Excited
  - Monotone
  - Formal

- **Multiple Accents**: Support for 8 English accent variations:
  - US English
  - British English
  - Australian English
  - Canadian English
  - Indian English
  - Irish English
  - South African English
  - New Zealand English

- **Timed Lyrics/Subtitles**: Automatically generates synchronized lyrics for audiobooks
- **Background Processing**: Asynchronous processing to handle large files without blocking
- **Progress Tracking**: Real-time status updates during audio generation
- **User Management**: Multi-user support with authentication
- **Media Management**: Organized storage for PDFs, audio files, and animations

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package installer)
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   cd d:\myproject2\audio_and_e-books
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Open your browser and navigate to: `http://127.0.0.1:8000`
   - Admin panel: `http://127.0.0.1:8000/admin`

## 📋 Dependencies

- **Django 5.2.7**: Web framework
- **PyPDF2 3.0.1**: PDF text extraction
- **gTTS 2.5.1**: Google Text-to-Speech for audio generation
- **pydub 0.25.1**: Audio file manipulation

## 📁 Project Structure

```
audio_and_e-books/
├── ebooks/                 # Main application
│   ├── models.py          # Database models (Ebook)
│   ├── views.py           # View logic
│   ├── forms.py           # Form definitions
│   ├── utils.py           # Helper functions (PDF extraction, audio generation)
│   ├── urls.py            # URL routing
│   ├── templates/         # HTML templates
│   │   └── ebooks/
│   │       ├── base.html
│   │       ├── list.html
│   │       ├── detail.html
│   │       └── upload.html
│   └── migrations/        # Database migrations
├── myblog/                # Project settings
│   ├── settings.py        # Configuration
│   ├── urls.py            # Main URL routing
│   └── wsgi.py            # WSGI configuration
├── media/                 # User-uploaded content
│   └── uploads/           # PDFs and audio files
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

## 🎯 Usage

### Uploading a PDF

1. Navigate to the upload page
2. Select a PDF file from your computer
3. Choose your preferred voice style (e.g., Storytelling, Dramatic)
4. Select an accent (e.g., US English, British English)
5. Click "Upload" to start processing

### Processing Flow

1. **Upload**: PDF file is uploaded and saved
2. **Text Extraction**: Text is extracted from the PDF in parallel for faster processing
3. **Audio Generation**: Text is converted to speech using gTTS with selected voice style and accent
4. **Lyrics Generation**: Timed lyrics/subtitles are automatically generated based on audio duration
5. **Completion**: Audiobook is ready to play with synchronized lyrics

### Viewing Your Audiobooks

- **List View**: See all your uploaded audiobooks with status indicators
- **Detail View**: Play audio, view synchronized lyrics, and see PDF details
- **Progress Tracking**: Real-time updates during processing

## 🔧 Configuration

### Settings

Key settings in `myblog/settings.py`:

- `MEDIA_ROOT`: Location for uploaded files
- `MEDIA_URL`: URL path for media files
- `ALLOWED_HOSTS`: Permitted host/domain names
- `CSRF_TRUSTED_ORIGINS`: Trusted origins for CSRF protection

### Database

The project uses SQLite by default (`db.sqlite3`). For production, consider PostgreSQL or MySQL.

## 🛠️ Development

### Running Tests

```bash
python manage.py test ebooks
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files (for production)

```bash
python manage.py collectstatic
```

## 📝 Model Structure

### Ebook Model

- `title`: Book title
- `pdf_file`: Uploaded PDF file
- `extracted_text`: Text extracted from PDF
- `audio_file`: Generated audiobook file
- `uploaded_by`: User who uploaded the file
- `upload_date`: Timestamp of upload
- `processing_status`: Current status (uploaded, processing, completed, failed)
- `progress`: Processing progress percentage
- `voice_style`: Selected narration style
- `accent`: Selected accent
- `lyrics`: JSON data with timed lyrics
- `background_animation`: Optional background animation
- `background_voice`: Optional background audio

## 🔒 Security Notes

⚠️ **Important**: This is a development configuration. Before deploying to production:

1. Change `SECRET_KEY` in settings.py
2. Set `DEBUG = False`
3. Configure proper `ALLOWED_HOSTS`
4. Use a production-grade database
5. Set up proper media file serving (e.g., AWS S3, CDN)
6. Configure HTTPS
7. Implement rate limiting for uploads
8. Add file size and type validation

## 🐛 Troubleshooting

### Audio Generation Issues

- Ensure gTTS has internet access (required for Google TTS)
- Check that pydub is properly installed
- Verify media directory permissions

### PDF Extraction Problems

- Ensure PyPDF2 is installed correctly
- Some PDFs may be image-based and require OCR
- Check PDF file permissions

### Performance Issues

- Large PDFs (>50 pages) may take several minutes
- Text is automatically truncated to 50,000 characters
- Background processing prevents UI blocking

## 📄 License

This project is provided as-is for educational and personal use.

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

## 📧 Support

For issues or questions, please check the application logs:
- Django logs are written to the console
- Check browser console for frontend issues

## 🎨 Future Enhancements

- [ ] Support for more languages
- [ ] Advanced voice customization (pitch, speed)
- [ ] Batch processing
- [ ] Export options (MP3, WAV, M4A)
- [ ] Enhanced lyrics editor
- [ ] Background music mixing
- [ ] OCR support for image-based PDFs
- [ ] API endpoints for programmatic access

---

**Made with ❤️ using Django and gTTS**
