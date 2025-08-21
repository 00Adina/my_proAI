import json
import re
from moviepy.editor import *
from gtts import gTTS
import os
import math
import numpy as np
import time

# ✅ Function: Create SRT file
def create_srt_file(transcripts, slide_info, audio_files, output_file="captions.srt"):
    """Create SRT subtitle file with word chunks"""
    srt_content = []
    subtitle_index = 1
    current_time = 0
    
    for i, (transcript, info, audio_file) in enumerate(zip(transcripts, slide_info, audio_files)):
        try:
            audio_clip = AudioFileClip(audio_file)
            duration = audio_clip.duration
            audio_clip.close()
        except:
            duration = 5  # fallback duration
        
        # Split transcript into chunks of 5-6 words
        words = transcript.split()
        chunk_size = 6
        word_chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
        
        if not word_chunks:
            continue
            
        chunk_duration = duration / len(word_chunks)
        
        for chunk in word_chunks:
            chunk_text = " ".join(chunk)
            start_time = current_time
            end_time = current_time + chunk_duration
            
            # Convert to SRT time format
            def seconds_to_srt_time(seconds):
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                millis = int((seconds % 1) * 1000)
                return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
            
            start_srt = seconds_to_srt_time(start_time)
            end_srt = seconds_to_srt_time(end_time)
            
            srt_content.append(f"{subtitle_index}")
            srt_content.append(f"{start_srt} --> {end_srt}")
            srt_content.append(chunk_text)
            srt_content.append("")  # Empty line
            
            subtitle_index += 1
            current_time = end_time
        
        current_time = current_time  # Continue from where we left off
    
    # Write SRT file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    
    print(f"✅ SRT file created: {output_file}")
    return output_file

# ✅ Function: Save to text file
def save_to_simple_text(filename):
    """Read text from file"""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"❌ File {filename} not found!")
        return ""

# ✅ Function: Extract JSON safely
def clean_and_parse_json(text_output):
    """Extracts valid JSON from LLM output and parses it safely."""
    print("\n🔍 Raw text preview:", text_output[:500])
    
    json_match = re.search(r"\{.*\}", text_output, re.DOTALL)
    if not json_match:
        print("❌ No JSON object found in text. Returning None.")
        return None
    
    json_str = json_match.group(0)
    
    try:
        slides = json.loads(json_str)
        print("✅ JSON parsed successfully")
        return slides
    except json.JSONDecodeError as e:
        print("❌ JSON parsing failed:", e)
        return None

# ✅ FIXED Function: Generate separate audio for each heading
def generate_audio_from_slides(slides_json):
    """Generate separate audio files for each heading with their content"""
    all_audio_files = []
    all_transcripts = []
    all_slide_info = []
    
    for slide_idx, (slide_name, slide_content) in enumerate(slides_json.items(), start=1):
        print(f"🎤 Processing slide {slide_idx}: {slide_name}")
        
        # ✅ Skip non-dictionary entries (like "topic")
        if not isinstance(slide_content, dict):
            print(f"⏭️ Skipping {slide_name} (not a slide dictionary)")
            continue
        
        slide_audio_files = []
        slide_transcripts = []
        slide_heading_info = []
        
        for heading_idx, (heading, content) in enumerate(slide_content.items()):
            print(f"  📝 Creating audio for heading: {heading}")
            
            # Create transcript for this specific heading
            transcript_parts = [heading]
            
            if isinstance(content, list):
                for item in content:
                    transcript_parts.append(str(item))
            elif isinstance(content, str):
                transcript_parts.append(content)
            
            heading_transcript = ". ".join(transcript_parts)
            
            try:
                # Generate TTS audio for this heading with FIXED SETTINGS
                tts = gTTS(text=heading_transcript, lang="en", slow=False)
                audio_filename = f"slide_{slide_idx}_heading_{heading_idx+1}_{heading.replace(' ', '_').replace('/', '_').replace('?', '').replace('!', '')}.mp3"
                
                # Clean filename more thoroughly
                audio_filename = re.sub(r'[^\w\-_\.]', '_', audio_filename)
                
                tts.save(audio_filename)
                
                # ✅ IMPORTANT: Add small delay to ensure file is saved properly
                time.sleep(0.5)
                
                # ✅ Verify audio file exists and has content
                if os.path.exists(audio_filename) and os.path.getsize(audio_filename) > 1000:  # At least 1KB
                    try:
                        # Test load the audio to make sure it's valid
                        test_audio = AudioFileClip(audio_filename)
                        test_duration = test_audio.duration
                        test_audio.close()
                        
                        if test_duration > 0:
                            slide_audio_files.append(audio_filename)
                            slide_transcripts.append(heading_transcript)
                            slide_heading_info.append({
                                "slide_name": slide_name,
                                "heading": heading,
                                "heading_index": heading_idx,
                            })
                            print(f"    ✅ Audio saved and verified: {audio_filename} ({test_duration:.2f}s)")
                        else:
                            raise Exception("Zero duration audio")
                            
                    except Exception as verify_error:
                        print(f"    ❌ Audio verification failed for {audio_filename}: {verify_error}")
                        raise verify_error
                else:
                    raise Exception(f"Audio file not created or too small: {audio_filename}")
                
            except Exception as e:
                print(f"    ❌ Failed to generate audio for {heading}: {e}")
                print(f"    🔄 Creating fallback audio...")
                
                # Create fallback audio with simple text
                try:
                    fallback_text = heading  # Just use heading text
                    fallback_tts = gTTS(text=fallback_text, lang="en", slow=False)
                    fallback_filename = f"slide_{slide_idx}_heading_{heading_idx+1}_fallback.mp3"
                    fallback_filename = re.sub(r'[^\w\-_\.]', '_', fallback_filename)
                    
                    fallback_tts.save(fallback_filename)
                    time.sleep(0.5)
                    
                    slide_audio_files.append(fallback_filename)
                    slide_transcripts.append(fallback_text)
                    slide_heading_info.append({
                        "slide_name": slide_name,
                        "heading": heading,
                        "heading_index": heading_idx,
                    })
                    print(f"    ✅ Fallback audio created: {fallback_filename}")
                    
                except Exception as fallback_error:
                    print(f"    ❌ Could not create fallback audio: {fallback_error}")
        
        all_audio_files.extend(slide_audio_files)
        all_transcripts.extend(slide_transcripts)
        all_slide_info.extend(slide_heading_info)
    
    return all_audio_files, all_transcripts, all_slide_info

# ✅ FIXED Function: Create video with proper audio handling
def create_slides_video_with_audio(slides_json, audio_files, transcripts, slide_info, output_file="video.mp4"):
    """Create a video with dynamic highlighting per heading and chunked captions"""
    video_segments = []
    audio_clips_to_close = []  # Keep track of audio clips for cleanup
    
    for i, (audio_file, transcript, info) in enumerate(zip(audio_files, transcripts, slide_info)):
        print(f"🎬 Creating segment {i+1}: {info['slide_name']} - {info['heading']}")
        
        # ✅ Load and verify audio properly with error handling
        try:
            # Verify file exists first
            if not os.path.exists(audio_file):
                print(f"❌ Audio file not found: {audio_file}")
                continue
                
            # Load audio for this heading
            audio_clip = AudioFileClip(audio_file)
            duration = audio_clip.duration
            
            # Verify audio has valid duration
            if duration <= 0:
                print(f"⚠️ Invalid audio duration: {duration}")
                audio_clip.close()
                continue
                
            # Keep track of audio clip for later cleanup
            audio_clips_to_close.append(audio_clip)
                
            print(f"    🔊 Audio loaded successfully: {duration:.2f}s from {audio_file}")
            
            # ✅ Test audio data
            try:
                # Sample a small portion to check if audio has data
                sample_audio = audio_clip.subclip(0, min(1.0, duration))
                audio_array = sample_audio.to_soundarray()
                sample_audio.close()
                
                if audio_array.max() == 0:
                    print(f"    ⚠️ Audio appears to be silent, but proceeding...")
                else:
                    print(f"    🎵 Audio has sound data (max amplitude: {audio_array.max():.3f})")
            except Exception as test_error:
                print(f"    ⚠️ Could not test audio data ({test_error}), but proceeding...")
                
        except Exception as e:
            print(f"❌ Error loading audio {audio_file}: {e}")
            continue
        
        # Get slide content for highlighting
        slide_content = slides_json[info["slide_name"]]
        if not isinstance(slide_content, dict):
            print(f"⏭️ Skipping segment for {info['slide_name']} (not a dictionary)")
            continue
        
        headings = list(slide_content.keys())
        
        # Create text clips with color highlighting
        text_clips = []
        y_position = 50
        
        # Add slide title
        title_clip = (
            TextClip(
                info["slide_name"],
                fontsize=40,
                color="white",
                font="Arial-Bold",
            )
            .set_position(("center", y_position))
            .set_duration(duration)
        )
        text_clips.append(title_clip)
        y_position += 80
        
        # Add headings with color highlighting
        for idx, heading in enumerate(headings):
            if idx == info["heading_index"]:
                # Current heading - Yellow color (highlighted)
                heading_color = "yellow"
                heading_fontsize = 36
            else:
                # Other headings - White color
                heading_color = "lightgray"
                heading_fontsize = 32
            
            heading_clip = (
                TextClip(
                    heading,
                    fontsize=heading_fontsize,
                    color=heading_color,
                    font="Arial-Bold" if idx == info["heading_index"] else "Arial",
                )
                .set_position(("center", y_position))
                .set_duration(duration)
            )
            text_clips.append(heading_clip)
            y_position += 60
        
        # Create chunked captions (5-6 words at a time)
        words = transcript.split()
        chunk_size = 6
        word_chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
        
        if not word_chunks:
            word_chunks = [["No content available"]]
        
        chunk_duration = duration / len(word_chunks)
        caption_clips = []
        
        for chunk_idx, chunk in enumerate(word_chunks):
            chunk_text = " ".join(chunk)
            start_time = chunk_idx * chunk_duration
            end_time = (chunk_idx + 1) * chunk_duration
            
            chunk_clip = (
                TextClip(
                    chunk_text,
                    fontsize=28,
                    color="yellow",
                    size=(1100, 150),
                    method="caption",
                    align="center",
                    font="Arial-Bold",
                )
                .set_position(("center", 550))
                .set_start(start_time)
                .set_duration(chunk_duration)
            )
            caption_clips.append(chunk_clip)
        
        # Create background and combine all clips
        bg_clip = ColorClip(size=(1280, 720), color=(20, 20, 40)).set_duration(duration)
        border_clip = ColorClip(size=(1260, 700), color=(40, 40, 60)).set_position((10, 10)).set_duration(duration)
        
        all_clips = [bg_clip, border_clip] + text_clips + caption_clips
        
        # ✅ CRITICAL FIX: Properly set audio to the composite
        try:
            segment = CompositeVideoClip(all_clips, size=(1280, 720))
            
            # ✅ Set audio with proper error handling
            segment = segment.set_audio(audio_clip)
            segment = segment.set_duration(duration)
            
            # ✅ Verify the segment has audio
            if segment.audio is not None:
                print(f"    ✅ Audio successfully attached to segment: {audio_clip.duration:.2f}s")
            else:
                print(f"    ⚠️ Warning: Segment audio is None")
            
            video_segments.append(segment)
            print(f"✅ Created segment for: {info['heading']}")
            
        except Exception as segment_error:
            print(f"❌ Error creating video segment: {segment_error}")
            continue
    
    # Combine all segments
    if video_segments:
        print(f"🎬 Combining {len(video_segments)} video segments...")
        
        try:
            final_clip = concatenate_videoclips(video_segments)
            
            # ✅ Verify final clip has audio
            if final_clip.audio is not None:
                print("✅ Final video has audio track")
                try:
                    total_duration = final_clip.duration
                    audio_duration = final_clip.audio.duration
                    print(f"📊 Video duration: {total_duration:.2f}s, Audio duration: {audio_duration:.2f}s")
                except:
                    print("📊 Could not get duration info, but proceeding...")
            else:
                print("⚠️ WARNING: Final video has no audio track!")
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            
            # ✅ Write video with explicit audio settings
            final_clip.write_videofile(
                output_file, 
                fps=24, 
                codec='libx264', 
                audio_codec='aac',
                verbose=True,
                logger='bar'  # Show progress bar
            )
            
            # Cleanup
            final_clip.close()
            for seg in video_segments:
                seg.close()
            
            print(f"🎬 Video saved successfully: {output_file}")
            
        except Exception as video_error:
            print(f"❌ Error creating final video: {video_error}")
            return False
    
    else:
        print("❌ No video segments generated.")
        return False
    
    # Cleanup audio clips
    for audio_clip in audio_clips_to_close:
        try:
            audio_clip.close()
        except:
            pass
    
    return True

# ------------------ MAIN FLOW ------------------ #
# ✅ Step 1: Load text result
text_output = save_to_simple_text("my_result.txt")

if not text_output.strip():
    print("❌ No content found in my_result.txt")
    exit()

# ✅ Step 2: Parse into JSON
slides_json = clean_and_parse_json(text_output)

if not slides_json:
    raise ValueError("❌ Could not parse slides JSON. Please check LLM output.")

print(f"✅ Parsed {len(slides_json)} slides from JSON")

# ✅ Step 3: Generate separate audios for each heading
print("🎵 Generating individual audio files for each heading...")
audio_files, transcripts, slide_info = generate_audio_from_slides(slides_json)

print(f"✅ Generated {len(audio_files)} individual audio segments")

if len(audio_files) == 0:
    print("❌ No audio files generated. Exiting...")
    exit()

# ✅ Display generated files for verification
print("\n📁 Generated Audio Files:")
for i, (audio_file, info) in enumerate(zip(audio_files, slide_info), 1):
    file_size = os.path.getsize(audio_file) if os.path.exists(audio_file) else 0
    print(f"  {i}. {audio_file} ({file_size} bytes) - {info['heading']}")

# ✅ Step 4: Create SRT file
srt_file = create_srt_file(transcripts, slide_info, audio_files)

# ✅ Step 5: Ask user for video name and generate final video
path = r"../Video_lectures"
if not os.path.exists(path):
    os.makedirs(path)
    print(f"📁 Created directory: {path}")

video_lect = input("Enter the video name (without extension): ")

# ✅ Create video with chunked captions
print("🎬 Starting video creation...")
success = create_slides_video_with_audio(
    slides_json, audio_files, transcripts, slide_info, f"{path}/{video_lect}.mp4"
)

if success:
    print("🎉 Video creation completed successfully!")
    print(f"📄 SRT file: {srt_file}")
    print(f"🎬 Video file: {path}/{video_lect}.mp4")
    
    # ✅ Optional: Cleanup temporary audio files
    cleanup_choice = input("Do you want to delete temporary audio files? (y/n): ")
    if cleanup_choice.lower() == "y":
        for audio_file in audio_files:
            try:
                os.remove(audio_file)
                print(f"🗑️ Deleted: {audio_file}")
            except Exception as e:
                print(f"⚠️ Could not delete {audio_file}: {e}")
else:
    print("❌ Video creation failed. Please check the errors above.")

print("\n📋 Required packages:")
print("pip install moviepy gtts")
