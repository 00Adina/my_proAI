# ✅ Function: Create highlighted text with color highlighting
def make_highlighted_text(topic, headings, highlight_index):
    lines = [topic, ""]
    for i, h in enumerate(headings):
        if i == highlight_index:
            # Current heading will be colored yellow in video
            lines.append(h)  # Store heading for color highlighting
        else:
            lines.append(h)
    return lines  # Return list instead of joined string for color processing


# ✅ Function: Save to text file
def save_to_simple_text(filename):
    """
    Read text from file
    """
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"❌ File {filename} not found!")
        return ""


# ✅ Function: Extract JSON safely
def clean_and_parse_json(text_output):
    """
    Extracts valid JSON from LLM output and parses it safely.
    """
    # ✅ Debug: print pehle 500 characters
    print("\n🔍 Raw text preview:", text_output[:500])

    # ✅ Extract JSON part using regex (first {...} block)
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


# ✅ Updated Function: Generate separate audio for each heading
def generate_audio_from_slides(slides_json):
    """
    Generate separate audio files for each heading with their content
    """
    all_audio_files = []
    all_transcripts = []
    all_slide_info = []  # Store slide and heading info

    for slide_idx, (slide_name, slide_content) in enumerate(
        slides_json.items(), start=1
    ):
        print(f"🎤 Processing slide {slide_idx}: {slide_name}")

        slide_audio_files = []
        slide_transcripts = []
        slide_heading_info = []

        for heading_idx, (heading, content) in enumerate(slide_content.items()):
            print(f"  📝 Creating audio for heading: {heading}")

            # Create transcript for this specific heading (without "Now discussing")
            transcript_parts = [heading]  # Start with heading name directly

            if isinstance(content, list):
                for item in content:
                    transcript_parts.append(str(item))
            elif isinstance(content, str):
                transcript_parts.append(content)

            # Join all parts into one transcript for this heading
            heading_transcript = ". ".join(transcript_parts)

            try:
                # Generate TTS audio for this heading
                tts = gTTS(text=heading_transcript, lang="en")
                audio_filename = f"slide_{slide_idx}_heading_{heading_idx+1}_{heading.replace(' ', '_')}.mp3"
                tts.save(audio_filename)

                slide_audio_files.append(audio_filename)
                slide_transcripts.append(heading_transcript)
                slide_heading_info.append(
                    {
                        "slide_name": slide_name,
                        "heading": heading,
                        "heading_index": heading_idx,
                    }
                )

                print(f"    ✅ Audio saved: {audio_filename}")

            except Exception as e:
                print(f"    ❌ Failed to generate audio for {heading}: {e}")
                # Create fallback silent audio
                try:
                    silence = AudioClip(make_frame=lambda t: 0, duration=2)
                    fallback_filename = (
                        f"slide_{slide_idx}_heading_{heading_idx+1}_silence.mp3"
                    )
                    silence.write_audiofile(
                        fallback_filename, verbose=False, logger=None
                    )
                    slide_audio_files.append(fallback_filename)
                    slide_transcripts.append(f"{heading} - Audio generation failed")
                    slide_heading_info.append(
                        {
                            "slide_name": slide_name,
                            "heading": heading,
                            "heading_index": heading_idx,
                        }
                    )
                except:
                    print(f"    ❌ Could not create fallback audio for {heading}")

        all_audio_files.extend(slide_audio_files)
        all_transcripts.extend(slide_transcripts)
        all_slide_info.extend(slide_heading_info)

    return all_audio_files, all_transcripts, all_slide_info


# ✅ Function: Create video with dynamic highlighting and proper captions
def create_slides_video_with_audio(
    slides_json, audio_files, transcripts, slide_info, output_file="video.mp4"
):
    """
    Create a video with dynamic highlighting per heading and synced captions
    """
    video_segments = []

    for i, (audio_file, transcript, info) in enumerate(
        zip(audio_files, transcripts, slide_info)
    ):
        print(f"🎬 Creating segment {i+1}: {info['slide_name']} - {info['heading']}")

        try:
            # Load audio for this heading
            audio_clip = AudioFileClip(audio_file)
            duration = audio_clip.duration
        except Exception as e:
            print(f"❌ Error loading audio {audio_file}: {e}")
            continue

        # Get slide content for highlighting
        slide_content = slides_json[info["slide_name"]]
        headings = list(slide_content.keys())

        # Create text clips with color highlighting
        text_clips = []
        y_position = 80

        # Add actual topic name as title (instead of slide1, slide2)
        topic_name = info["slide_name"]  # This contains the actual topic
        title_clip = (
            TextClip(
                topic_name,  # Show actual topic name like "Ethics and Philosophy"
                fontsize=36,
                color="white",
                font="Arial",
            )
            .set_position((120, y_position))
            .set_duration(duration)
        )
        text_clips.append(title_clip)
        y_position += 60

        # Add headings with color highlighting
        for idx, heading in enumerate(headings):
            if idx == info["heading_index"]:
                # Current heading - Yellow color
                heading_color = "yellow"
                heading_fontsize = 34
            else:
                # Other headings - White color
                heading_color = "white"
                heading_fontsize = 32

            heading_clip = (
                TextClip(
                    heading,
                    fontsize=heading_fontsize,
                    color=heading_color,
                    font="Arial",
                )
                .set_position((120, y_position))
                .set_duration(duration)
            )
            text_clips.append(heading_clip)
            y_position += 50

        # Use full transcript content for captions (no length limit)
        caption_text = transcript

        # Create captions clip for current heading content (full content)
        captions_clip = (
            TextClip(
                f"🎤 {caption_text}",
                fontsize=18,  # Slightly smaller font for longer text
                color="yellow",
                size=(1100, 200),  # Increased height for more text
                method="caption",
                align="center",
                font="Arial",
            )
            .set_position(("center", 520))  # Adjusted position for larger caption area
            .set_duration(duration)
        )

        # Create background and combine all text clips
        bg_clip = ColorClip(size=(1280, 720), color=(0, 0, 0)).set_duration(duration)
        all_clips = [bg_clip] + text_clips + [captions_clip]
        segment = CompositeVideoClip(all_clips).set_audio(audio_clip)

        video_segments.append(segment)
        print(f"✅ Created segment for: {info['heading']}")

    # Combine all segments
    if video_segments:
        print("🎬 Combining all video segments...")
        final_clip = concatenate_videoclips(video_segments)

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        final_clip.write_videofile(output_file, fps=24)

        # Cleanup
        for seg in video_segments:
            seg.close()
        final_clip.close()

        print(f"🎬 Video saved with dynamic highlighting: {output_file}")
    else:
        print("❌ No video segments generated.")


# ------------------ MAIN FLOW ------------------ #
# ✅ Step 1: Load text result
text_output = save_to_simple_text("my_result.txt")

# ✅ Step 2: Parse into JSON (returns dict)
slides_json = clean_and_parse_json(text_output)

if not slides_json:
    raise ValueError("❌ Could not parse slides JSON. Please check LLM output.")

# ✅ Step 3: Generate separate audios for each heading
print("🎵 Generating individual audio files for each heading...")
audio_files, transcripts, slide_info = generate_audio_from_slides(slides_json)

print(f"✅ Generated {len(audio_files)} individual audio segments")

# ✅ Step 4: Ask user for video name and generate final video
path = r"../Video_lectures"
video_lect = input("Enter the video name (without extension): ")

# ✅ Create video with dynamic highlighting and proper captions
create_slides_video_with_audio(
    slides_json, audio_files, transcripts, slide_info, f"{path}/{video_lect}.mp4"
)

# ✅ Optional: Cleanup temporary audio files
cleanup_choice = input("Do you want to delete temporary audio files? (y/n): ")
if cleanup_choice.lower() == "y":
    for audio_file in audio_files:
        try:
            os.remove(audio_file)
            print(f"🗑️ Deleted: {audio_file}")
        except Exception as e:
            print(f"⚠️ Could not delete {audio_file}: {e}")

print("🎉 Video creation completed with dynamic highlighting and synced captions!")

# Required packages:
# pip install moviepy gtts
