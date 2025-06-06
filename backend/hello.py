from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn
import os
from hyperbrowser import Hyperbrowser
from hyperbrowser.models import StartScrapeJobParams, ScrapeOptions, CreateSessionParams
from dotenv import load_dotenv
import requests
import json
import traceback
import asyncio
from typing import AsyncGenerator
import aiohttp

# Load environment variables from .env file
load_dotenv()

# Create FastAPI instance
app = FastAPI(
    title="Orchids Challenge API",
    description="A starter FastAPI template for the Orchids Challenge backend",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Allow both common dev ports
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize Hyperbrowser client
try:
    client = Hyperbrowser(api_key=os.getenv("HYPERBROWSER_API_KEY"))
    print("✅ Hyperbrowser client initialized")
except Exception as e:
    print("❌ Failed to initialize Hyperbrowser client:", str(e))
    print(traceback.format_exc())
    raise

class URLInput(BaseModel):
    url: str

async def stream_html(url: str) -> AsyncGenerator[str, None]:
    """Stream a joke from OpenRouter API"""
    try:
        print("📸 Initiating scrape job...")
        scrape_result = client.scrape.start_and_wait(
            StartScrapeJobParams(
                url=url,
                session_options=CreateSessionParams(use_stealth=True),
                scrape_options=ScrapeOptions(
                    formats=["screenshot", "html"],
                    exclude_tags=[
                        "script", "iframe", "noscript", "meta", "base", "object", "embed"
                    ],
                    screenshot_options={
                        "full_page": True,
                        "format": "jpeg",
                        "quality": 80
                    }
                )
            )
        )
        
        print("✅ Scrape job completed")
        
        if not hasattr(scrape_result.data, 'screenshot'):
            print("❌ No screenshot URL in response")
            raise HTTPException(status_code=500, detail="No screenshot URL in response")
            
        screenshot_url = scrape_result.data.screenshot
        html_content = scrape_result.data.html
        
        print(f"🖼️ Screenshot URL obtained: {screenshot_url[:100]}...")
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        }
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Replicate this website in HTML. Provided will be an image and some HTML of the website. RETURN THE HTML ONLY, NO OTHER TEXT. DO NOT INCLUDE ANY OTHER TEXT IN YOUR RESPONSE. The website you generate should be view only, and does not need to have any functionality. DO NOT FORGET TO GENERATE THE HEADER AND FOOTER IF IT EXISTS. MAKE SURE COLORS ARE CORRECT, DO NOT FORGET TO STYLE THE HTML. DO NOT ADD ENCLOSE THE HTML IN ```html``` OR ANYTHING SIMILAR. THE HTML MUST WORK AS IS."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": screenshot_url
                        }
                    },
                    {
                        "type": "text",
                        "text": html_content
                    }
                ]
            }
        ]
        payload = {
            "model": "google/gemini-2.5-flash-preview-05-20",
            "messages": messages,
            "stream": True
        }
        
        print("📤 Sending request to OpenRouter API...")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ OpenRouter API error: {response.status}")
                    print(f"📄 Response content: {error_text}")
                    raise HTTPException(status_code=500, detail="Failed to get response")
                
                print("✅ Successfully received streaming response from OpenRouter API")
                
                async for line in response.content:
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]  # Remove 'data: ' prefix
                            if data == '[DONE]':
                                break
                            try:
                                json_data = json.loads(data)
                                if 'choices' in json_data and len(json_data['choices']) > 0:
                                    content = json_data['choices'][0].get('delta', {}).get('content', '')
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
                        
    except Exception as e:
        print(f"❌ Error in stream_joke: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")
    finally:
        yield "\n"  # Ensure the stream is properly terminated

@app.post("/stream")
async def get_stream(input: URLInput) -> StreamingResponse:
    """
    Stream a joke word by word
    """
    return StreamingResponse(
        stream_html(input.url),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

async def take_screenshot(url: str) -> str:
    """Take a screenshot of the given URL using Hyperbrowser and return the URL"""
    try:
        print(f"\n🔄 Starting screenshot process for URL: {url}")
        
        # Start scraping and wait for completion
        print("📸 Initiating scrape job...")
        scrape_result = client.scrape.start_and_wait(
            StartScrapeJobParams(
                url=url,
                session_options=CreateSessionParams(use_stealth=True),
                scrape_options=ScrapeOptions(
                    formats=["screenshot", "html"],
                    exclude_tags=[
                        "script", "iframe", "noscript", "meta", "base", "object", "embed"
                    ],
                    screenshot_options={
                        "full_page": True,
                        "format": "jpeg",
                        "quality": 80
                    }
                )
            )
        )
        
        print("✅ Scrape job completed")
        print(f"📊 Scrape result type: {type(scrape_result)}")
        print(f"📊 Scrape result data type: {type(scrape_result.data)}")
        
        if not hasattr(scrape_result.data, 'screenshot'):
            print("❌ No screenshot URL in response")
            print(f"📋 Available attributes: {dir(scrape_result.data)}")
            raise HTTPException(status_code=500, detail="No screenshot URL in response")
            
        screenshot_url = scrape_result.data.screenshot
        html_content = scrape_result.data.html
        
        print(f"🖼️ Screenshot URL obtained: {screenshot_url[:100]}...")
        print(f"📄 HTML content length: {len(html_content)} characters")

        # Call OpenRouter API for image analysis
        print("\n🤖 Initiating OpenRouter API call...")
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        }
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Replicate this website in HTML. Provided will be an image and some HTML of the website. RETURN THE HTML ONLY, NO OTHER TEXT. DO NOT INCLUDE ANY OTHER TEXT IN YOUR RESPONSE. The website you generate should be view only, and does not need to have any functionality. DO NOT FORGET TO GENERATE THE HEADER AND FOOTER IF IT EXISTS. MAKE SURE COLORS ARE CORRECT, DO NOT FORGET TO STYLE THE HTML. DO NOT ADD ENCLOSE THE HTML IN ```html``` OR ANYTHING SIMILAR. THE HTML MUST WORK AS IS."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": screenshot_url
                        }
                    },
                    {
                        "type": "text",
                        "text": html_content
                    }
                ]
            }
        ]
        payload = {
            "model": "google/gemini-2.5-flash-preview-05-20",
            "messages": messages
        }
        
        print("📤 Sending request to OpenRouter API...")
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"❌ OpenRouter API error: {response.status_code}")
            print(f"📄 Response content: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to analyze image")
            
        print("✅ Successfully received response from OpenRouter API")
        return JSONResponse(content={
            "status": "success",
            "code": response.json().get("choices")[0].get("message").get("content")
        })
    except Exception as e:
        print(f"❌ Error in take_screenshot: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Screenshot failed: {str(e)}")

@app.post("/process-url")
async def process_url(input: URLInput):
    """
    Take a screenshot of the provided URL and return the screenshot URL
    """
    try:
        print(f"\n🌐 Processing URL: {input.url}")
        screenshot = await take_screenshot(input.url)
        print("✅ URL processing completed successfully")
        return screenshot
    except Exception as e:
        print(f"❌ Error in process_url: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Run the application"""
    print("\n🚀 Starting FastAPI application...")
    uvicorn.run(
        "hello:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()
