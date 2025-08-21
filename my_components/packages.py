import os
import sys
import re
import time
import wave
import hashlib
from uuid import uuid4
from datetime import datetime
import numpy as np
import pygame
import pdfplumber

# import pytesseract
# import soundfile as sf
from scipy.io import wavfile
from pydub import AudioSegment
from IPython.display import display, Audio
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

from pinecone import Pinecone, ServerlessSpec
from langchain import hub
from langchain.schema import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.question_answering import load_qa_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import google.generativeai as genai
import numpy as np
from kokoro import KPipeline
from moviepy.editor import (
    TextClip,
    ColorClip,
    CompositeVideoClip,
    AudioFileClip,
    VideoFileClip,
    concatenate_videoclips,
)
from moviepy.config import change_settings
import json, ast
import whisper
