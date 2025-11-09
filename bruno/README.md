# YouTube FastAPI - Bruno Collection

This is a Bruno API collection for testing the YouTube FastAPI backend.

## What is Bruno?

Bruno is a fast, git-friendly, open-source API client. Unlike Postman, Bruno stores collections as plain text files in your repository, making it perfect for version control and team collaboration.

Download: https://www.usebruno.com/

## Getting Started

### 1. Install Bruno
Download and install Bruno from https://www.usebruno.com/downloads

### 2. Open Collection
1. Open Bruno
2. Click "Open Collection"
3. Navigate to this `bruno` folder
4. Bruno will load all the requests

### 3. Select Environment
1. Click on "Env" dropdown (top right)
2. Select "Local"
3. The base URL is set to `http://localhost:8000`

### 4. Start Your Server
```bash
uvicorn src.main:app --reload
```

## API Testing Workflow

### Step 1: Authentication

Run these requests in order:

1. **Register** - Create a new user account
   - Creates a test user
   - Returns user object

2. **Login** - Get access tokens
   - Automatically saves `accessToken` and `refreshToken` to environment
   - These tokens are used in subsequent requests

3. **Get Current User** - Verify authentication
   - Uses the saved access token
   - Returns current user info

### Step 2: Video Management

4. **Create Video** - Create video metadata
   - Automatically saves `videoId` for subsequent requests
   - Initial status: `"processing_status": "pending"`

5. **Get All Videos** - List published videos (public)
   - No authentication required
   - Paginated results

6. **Get My Videos** - List your videos
   - Requires authentication
   - Shows all videos (published and unpublished)

7. **Get Video by ID** - Get specific video
   - Increments view count
   - Change `videoId` variable in pre-request vars

8. **Update Video** - Update video metadata
   - Owner only
   - Can update title, description, thumbnail, is_published

9. **Delete Video** - Remove video
   - Owner only
   - Deletes from database and S3

### Step 3: Video Processing Workflow

10. **Get Presigned Upload URL** - Get S3 upload URL
    - Returns a presigned URL for uploading to S3
    - Automatically saves `uploadUrl` and `videoKey`
    - Use this URL with PUT request to upload your video file

11. **Mark Upload Complete** - Trigger HLS conversion
    - Call this after uploading to S3
    - Saves raw video URL
    - Triggers go-api for HLS conversion
    - Status changes: `pending` → `processing`

12. **Processing Webhook (Simulate go-api)** - Simulate completion
    - Simulates go-api calling webhook
    - Updates video with processed HLS URLs
    - Status changes: `processing` → `completed`

13. **Processing Webhook - Failed (Simulate)** - Simulate failure
    - Simulates go-api reporting a failure
    - Status changes: `processing` → `failed`

## Environment Variables

The collection uses these environment variables (automatically managed):

- `baseUrl` - API base URL (default: http://localhost:8000)
- `accessToken` - JWT access token (auto-saved after login)
- `refreshToken` - JWT refresh token (auto-saved after login)
- `videoId` - Last created video ID (auto-saved after create video)
- `videoKey` - S3 video key (auto-saved after get presigned URL)
- `uploadUrl` - S3 upload URL (auto-saved after get presigned URL)

## Request Variables

Some requests use local variables that you can customize:

- `videoId` in Update/Delete/Get Video - Change to test specific videos
- `page` and `page_size` in list endpoints - Adjust pagination

## Tips

### Auto-Save Variables

Several requests automatically save response data to variables:
- **Login** saves access and refresh tokens
- **Create Video** saves the video ID
- **Get Presigned Upload URL** saves upload URL and video key

### Testing Full Workflow

1. Register → Login (saves tokens)
2. Create Video (saves videoId)
3. Get Presigned Upload URL (saves uploadUrl and videoKey)
4. Upload video to S3 using uploadUrl (external tool or curl)
5. Mark Upload Complete (triggers processing)
6. Simulate webhook callback (simulate go-api completion)
7. Get Video by ID (check processed URLs and status)

### Uploading to S3

After getting the presigned URL, upload your video file:

```bash
curl -X PUT "{{uploadUrl}}" \
  -H "Content-Type: video/mp4" \
  --data-binary "@your-video.mp4"
```

Or use Bruno to test:
1. Create a new request
2. Method: PUT
3. URL: Use the saved `{{uploadUrl}}`
4. Headers: `Content-Type: video/mp4`
5. Body: Binary file upload

## Collection Structure

```
bruno/
├── bruno.json                   # Collection metadata
├── environments/
│   └── Local.bru               # Local environment variables
├── Auth/
│   ├── Register.bru
│   ├── Login.bru
│   ├── Get Current User.bru
│   └── Refresh Token.bru
└── Videos/
    ├── Create Video.bru
    ├── Get All Videos.bru
    ├── Get My Videos.bru
    ├── Get Video by ID.bru
    ├── Update Video.bru
    ├── Delete Video.bru
    ├── Get Presigned Upload URL.bru
    ├── Mark Upload Complete.bru
    ├── Processing Webhook (Simulate go-api).bru
    └── Processing Webhook - Failed (Simulate).bru
```

## S3 Configuration

To test S3 features (presigned URLs, video upload), configure your `.env`:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=your_bucket_name
AWS_REGION=us-east-1
```

## go-api Integration

The webhook endpoints simulate what your go-api service should call.

Your go-api should:
1. Receive POST request to `/api/v1/videos/process`
2. Convert video to HLS with multiple qualities
3. Upload processed files to S3
4. Call the webhook URL with results

## Troubleshooting

### 401 Unauthorized
- Run the Login request again
- Check that `accessToken` is saved in environment
- Token might be expired (30 min default)

### 503 Service Unavailable (Presigned URL)
- S3 is not configured
- Check AWS credentials in `.env`

### Video Not Found
- Make sure `videoId` variable is set correctly
- Check if you're using the right user (videos are user-specific)

## Contributing

When adding new endpoints:
1. Create a new `.bru` file in the appropriate folder
2. Follow the naming convention
3. Add documentation in the `docs` section
4. Update this README if needed
