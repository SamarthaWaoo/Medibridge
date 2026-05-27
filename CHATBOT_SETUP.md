# MediBridge Gemini Chatbot Setup Guide

## Overview
The MediBridge Health Assistant is a Gemini-powered chatbot that helps patients get information about home remedies and wellness tips.

## Features
- **Home Remedy Suggestions**: Get personalized home remedy recommendations for various symptoms
- **General Wellness Chat**: Ask general health and wellness questions
- **Quick Actions**: Pre-defined buttons for common symptoms
- **Real-time Responses**: Instant AI-powered responses using Google Gemini

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

The chatbot requires:
- `google-generativeai==0.3.0` (already added to requirements.txt)

### 2. Get Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your API key

### 3. Set Environment Variable
Set the `GEMINI_API_KEY` environment variable:

**On Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=your_api_key_here
```

**On Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

**On Linux/Mac:**
```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 4. Run the Application
```bash
python app.py
```

## Usage

### For Patients
1. Log in as a patient
2. Go to Patient Dashboard
3. Click "Chat Now" on the Health Assistant card
4. Ask questions about home remedies or wellness

### Features Available
- **Quick Actions**: Click pre-defined symptom buttons for instant suggestions
- **Free Chat**: Type any health-related question
- **Message History**: All messages are displayed in the chat window
- **Real-time Responses**: Get instant AI-powered responses

## API Endpoints

### Chat Message Endpoint
- **URL**: `/api/chatbot/message`
- **Method**: `POST`
- **Authentication**: Required (Patient only)
- **Body**: `{"message": "Your question here"}`
- **Response**: `{"success": true, "response": "AI response"}`

### Home Remedy Endpoint
- **URL**: `/api/chatbot/remedy`
- **Method**: `POST`
- **Authentication**: Required (Patient only)
- **Body**: `{"symptoms": "symptom1, symptom2"}`
- **Response**: `{"success": true, "response": "Home remedy suggestions"}`

## Important Notes

### Disclaimers
- The chatbot provides **general wellness information only**
- It is **NOT a substitute for professional medical advice**
- Always consult a healthcare professional for serious health concerns
- The chatbot cannot diagnose diseases or prescribe medications

### Error Handling
- If `GEMINI_API_KEY` is not set, the chatbot feature will be disabled
- Users will see an error message if the chatbot is unavailable
- API errors are handled gracefully with user-friendly messages

### Rate Limiting
- Google Gemini API has rate limits based on your plan
- Monitor your API usage in Google AI Studio
- Consider implementing rate limiting if needed

## Troubleshooting

### Chatbot Not Working
1. Verify `GEMINI_API_KEY` is set correctly
2. Check internet connection
3. Verify API key is valid in Google AI Studio
4. Check application logs for error messages

### Slow Responses
- Gemini API responses may take a few seconds
- Check your internet connection
- Verify API quota hasn't been exceeded

### Access Denied
- Ensure you're logged in as a patient
- Other user types (doctors, admins) cannot access the chatbot

## Future Enhancements
- Store chat history in database
- Add multi-language support
- Implement chat export functionality
- Add sentiment analysis
- Integration with appointment booking

## Support
For issues or questions, contact the administrator or check the application logs.
