# app.py

import base64
import io
import fitz  # PyMuPDF
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import google.generativeai as genai
import re

genai.configure(api_key="AIzaSyCcoQ40u_iM1BIvp26iLqVTWdHp3Ky0TAw")

app = FastAPI()

# Allow CORS (so Wix frontend can access it)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Your prompt templates
input_prompt1 = """You are a highly skilled and experienced HR specializing..."""
input_prompt2 = """You are a highly skilled and experienced career coach..."""
input_prompt3 = """You are a skilled and advanced ATS..."""

def extract_match_percentage(response_text):
    match = re.search(r"Match Percentage:\s*(\d+)%", response_text)
    return int(match.group(1)) if match else 0

def input_pdf_setup(uploaded_file):
    pdf_doc = fitz.open(stream=uploaded_file, filetype="pdf")
    first_page = pdf_doc[0].get_pixmap()
    img_byte_arr = io.BytesIO(first_page.tobytes("jpeg"))
    return base64.b64encode(img_byte_arr.getvalue()).decode()

def get_gemini_response(input_text, pdf_base64, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([
        input_text,
        {"mime_type": "image/jpeg", "data": pdf_base64},
        prompt
    ])
    return response.text

@app.post("/analyze")
async def analyze_resume(file: UploadFile = File(...), mode: str = Form(...)):
    resume_data = await file.read()
    pdf_base64 = input_pdf_setup(resume_data)

    default_input_text = "Analyze this resume based on general job-fit for a technology/business/finance/agriculture role."

    # Choose which prompt to use
    if mode == "analysis":
        prompt = input_prompt1
    elif mode == "improvement":
        prompt = input_prompt2
    elif mode == "match":
        prompt = input_prompt3
    else:
        return {"error": "Invalid mode. Use: analysis, improvement, or match."}

    response_text = get_gemini_response(default_input_text, pdf_base64, prompt)

    return {
        "response": response_text,
        "match_percentage": extract_match_percentage(response_text) if mode == "match" else None
    }
