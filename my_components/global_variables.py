pinecone_api_key = apis.pinecone_Api_vector_db
gemini_api_key = apis.gemini_key
Index_name = "myproaiassistant"
# file_path = r"../my_documents/(Book)Linear Algebra and its Application.pdf"
file_path = r"../my_documents/pp_week1.pdf"
os.environ["GOOGLE_API_KEY"] = apis.gemini_key
os.environ["PINECONE_API_KEY"] = apis.pinecone_Api_vector_db
gemini_model_for_embaddings = "models/embedding-001"
gemini_model_for_query = "gemini-2.5-pro"
audio_clip = r"../my_audios/123456.wav"
# ImageMagick  path
change_settings(
    {"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"}
)
unique_id = uuid4()

# AudioSegment.converter = r"C:\Users\user\Downloads\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"
# AudioSegment.ffprobe = (
#     r"C:\Users\user\Downloads\ffmpeg-7.1.1-essentials_build\bin\ffprobe.exe"
# )
print(file_path)
