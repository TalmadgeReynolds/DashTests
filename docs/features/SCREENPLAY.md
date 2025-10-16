# Screenplay Feature Documentation

## Overview

The Screenplay feature allows users to upload PDF screenplays, view them side-by-side with the dashboard, and select portions of text to convert into prompts for video generation jobs.

## Features

### 1. PDF Upload
- Upload screenplay PDFs up to 50MB
- Automatic text extraction from PDF
- Store screenplay metadata (title, page count, file size)
- Drag-and-drop file upload interface

### 2. Screenplay Viewer
- View PDF screenplays in browser
- Zoom in/out controls (50% - 200%)
- Page navigation
- Text selection capability
- Side-by-side with job creation interface

### 3. Text Selection & Prompt Generation
- Select any text from the screenplay
- Automatic text cleanup and formatting
- Preview selected text with character/word count
- One-click conversion to prompt for job creation

### 4. Screenplay Management
- List all uploaded screenplays
- View screenplay details
- Delete screenplays
- Search and filter (future enhancement)

## Architecture

### Backend Components

#### Models (`backend/models/job.py`)
- **Screenplay Model**: Stores screenplay metadata
  - `id`: UUID primary key
  - `title`: Screenplay title
  - `filename`: Original PDF filename
  - `pdf_url`: S3/MinIO URL to PDF file
  - `text_content`: Extracted text from PDF
  - `page_count`: Number of pages
  - `file_size_bytes`: File size
  - `created_at`, `updated_at`: Timestamps

#### Routes (`backend/routes/screenplay.py`)
- `POST /api/v1/screenplays`: Create screenplay record after PDF upload
- `GET /api/v1/screenplays`: List all screenplays with pagination
- `GET /api/v1/screenplays/{id}`: Get specific screenplay
- `DELETE /api/v1/screenplays/{id}`: Delete screenplay
- `POST /api/v1/screenplays/text-selection`: Process selected text

#### Services
- **StorageService** (`backend/services/storage.py`): Extended to support SCREENPLAY file type
- **PDFProcessor** (`backend/utils/pdf_processor.py`): Extract text from PDF files using PyPDF2

#### Database Migration
- Alembic migration created: `20251013_125000_b7f9e1d8c2a1_add_screenplay_table.py`

### Frontend Components

#### Pages
- **Screenplay** (`frontend/src/pages/Screenplay.tsx`): Main page with 3-panel layout
  - Left: Screenplay list sidebar
  - Center: PDF viewer or upload form
  - Right: Prompt editor panel

#### Components
- **ScreenplayViewer** (`frontend/src/components/screenplay/ScreenplayViewer.tsx`)
  - PDF rendering using react-pdf
  - Text selection handling
  - Page navigation and zoom controls
  
- **ScreenplayUpload** (`frontend/src/components/screenplay/ScreenplayUpload.tsx`)
  - Drag-and-drop file upload
  - File validation (PDF only, max 50MB)
  - Upload progress indicator

#### Hooks
- **useScreenplay** (`frontend/src/hooks/useScreenplay.ts`)
  - React Query hooks for all screenplay operations
  - Automatic cache management
  - Error handling and loading states

#### Types
- **screenplay.ts** (`frontend/src/types/screenplay.ts`)
  - TypeScript interfaces for all screenplay-related data

## User Workflow

### 1. Upload a Screenplay
1. Navigate to "Script" in the navigation rail
2. Click "Upload Screenplay" button
3. Drag and drop PDF or click to browse
4. Enter screenplay title
5. Click "Upload Screenplay"
6. System extracts text and displays screenplay

### 2. View and Select Text
1. Select a screenplay from the left sidebar
2. PDF displays in the center panel
3. Use zoom controls and page navigation as needed
4. Click and drag to select text from the screenplay
5. Selected text appears in the right panel

### 3. Create Job from Selection
1. Review selected text in the prompt editor
2. Edit prompt if needed
3. Click "Create Job with Prompt"
4. Redirected to job creation page with prompt pre-filled

## API Endpoints

### Upload Screenplay
```http
POST /api/v1/uploads/presign
Content-Type: application/json

{
  "filename": "my-screenplay.pdf",
  "mime": "application/pdf",
  "kind": "SCREENPLAY",
  "content_length": 5242880
}
```

Response:
```json
{
  "uploadUrl": "https://storage.example.com/...",
  "fileUrl": "https://storage.example.com/screenplays/..."
}
```

### Create Screenplay Record
```http
POST /api/v1/screenplays
Content-Type: application/json

{
  "title": "My Awesome Screenplay",
  "filename": "my-screenplay.pdf",
  "pdf_url": "https://storage.example.com/screenplays/...",
  "file_size_bytes": 5242880
}
```

Response:
```json
{
  "id": "uuid",
  "title": "My Awesome Screenplay",
  "filename": "my-screenplay.pdf",
  "pdf_url": "https://...",
  "text_content": "Full extracted text...",
  "page_count": 120,
  "file_size_bytes": 5242880,
  "created_at": "2025-10-13T12:00:00Z",
  "updated_at": "2025-10-13T12:00:00Z"
}
```

### List Screenplays
```http
GET /api/v1/screenplays?skip=0&limit=50
```

### Get Screenplay
```http
GET /api/v1/screenplays/{id}
```

### Delete Screenplay
```http
DELETE /api/v1/screenplays/{id}
```

### Process Text Selection
```http
POST /api/v1/screenplays/text-selection
Content-Type: application/json

{
  "screenplay_id": "uuid",
  "selected_text": "Selected text from screenplay"
}
```

Response:
```json
{
  "screenplay_id": "uuid",
  "selected_text": "Selected text from screenplay",
  "processed_prompt": "Cleaned up text ready for use"
}
```

## Installation & Setup

### Backend Dependencies
Already added to `requirements.txt`:
```
PyPDF2>=3.0.0,<4.0.0
```

Install with:
```bash
pip install -r requirements.txt
```

### Frontend Dependencies
Already added to `package.json`:
```json
"react-pdf": "^9.1.1"
```

Install with:
```bash
cd frontend
npm install
```

### Database Migration
Run the migration:
```bash
alembic upgrade head
```

## Configuration

### Storage Settings
Screenplays are stored using the same S3/MinIO configuration as other assets:
- `STORAGE_ENDPOINT`: S3/MinIO endpoint
- `STORAGE_BUCKET`: Bucket name
- `STORAGE_ACCESS_KEY`: Access key
- `STORAGE_SECRET_KEY`: Secret key

### File Limits
- Max file size: 50MB
- Accepted MIME types: `application/pdf`
- Storage path: `{bucket}/SCREENPLAY/{hash}-{timestamp}.pdf`

## Future Enhancements

1. **Search & Filter**
   - Full-text search within screenplay content
   - Filter by date, page count, etc.

2. **Annotations**
   - Highlight and annotate screenplay sections
   - Save annotations with timestamps

3. **Scene Detection**
   - Automatically detect scenes and breaks
   - Navigate by scene

4. **Collaboration**
   - Share screenplays with team members
   - Comment on specific sections

5. **Version Control**
   - Track screenplay revisions
   - Compare versions

6. **Export**
   - Export selected sections
   - Generate shot lists from scenes

## Troubleshooting

### PDF Won't Load
- Check PDF file is not corrupted
- Verify PDF URL is accessible
- Check browser console for errors
- Ensure react-pdf worker is loaded

### Text Extraction Failed
- Some PDFs may have protected text
- Scanned PDFs (images) won't extract text
- Check backend logs for PyPDF2 errors

### Upload Fails
- Verify file size is under 50MB
- Check file is valid PDF
- Ensure storage service is running
- Check network connectivity

## Testing

### Backend Tests
```bash
pytest tests/routes/test_screenplay.py
```

### Frontend Tests
```bash
cd frontend
npm test -- screenplay
```

## Security Considerations

1. **File Validation**: Only PDF files accepted
2. **Size Limits**: 50MB maximum enforced
3. **Access Control**: Future enhancement for user-based access
4. **Storage Security**: Uses presigned URLs with expiration
5. **Input Sanitization**: Text content sanitized before storage

## Performance

- PDF text extraction runs asynchronously
- Extracted text cached in database
- React Query handles caching on frontend
- Pagination for screenplay lists
- Lazy loading of PDF pages

## License

Same as main project license.
