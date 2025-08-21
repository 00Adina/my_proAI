def save_to_simple_text(filename):
    final_result = run_llm("text", instructions=task_instruction)

    if not final_result:
        print("⚠️ No result returned from run_llm")
        return None

    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_result.strip())

    print(f"✅ Text file saved: {filename}")
    return final_result.strip()


output = save_to_simple_text("my_result.txt")
print("Returned:", output)


def clean_and_parse_json(text_output):
    """
    Extracts valid JSON from LLM output and parses it safely.
    """
    # ✅ Extract JSON part using regex (first {...} block)
    json_match = re.search(r"\{.*\}", text_output, re.DOTALL)
    if not json_match:
        print("❌ No JSON object found in text.")
        return None

    json_str = json_match.group(0).strip()

    # ✅ Try loading with json
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        print("⚠️ json.loads failed, trying ast.literal_eval...")
        try:
            return ast.literal_eval(json_str)
        except Exception as e:
            print("❌ Parsing failed completely:", e)
            return None


def generate_audio_from_slides(text_output, chunk_length_sec=60):
    """
    Generate separate audio files for each slide in JSON.
    """
    slides = clean_and_parse_json(text_output)
    if not slides:
        print("❌ Could not parse JSON")
        return None

    saved_files = []

    for i, (slide_name, slide_content) in enumerate(slides.items(), start=1):
        # ✅ Skip non-dictionary entries (like "topic_name")
        if not isinstance(slide_content, dict):
            print(f"⏭️ Skipping {slide_name} (not a slide dictionary)")
            continue

        for heading_idx, (heading, content) in enumerate(slide_content.items()):
            # ✅ Ensure content is a string
            if not isinstance(content, str):
                print(f"⏭️ Skipping {heading} (not a string)")
                continue

            # ✅ Clean up content
            slide_content[heading] = content.strip()

        # ✅ Convert slide content into text (paragraphs)
        text_data = " ".join([f"{k}: {v}" for k, v in slide_content.items()])

        print(f"\n🎤 Generating audio for {slide_name}...")

        # Step 1: Generate audio narration
        pipeline = KPipeline(lang_code="a")
        generator = pipeline(text_data, voice="am_onyx", speed=1)

        audio_data = []
        for j, (gs, ps, audio) in enumerate(generator):
            display(Audio(data=audio, rate=24000, autoplay=(j == 0)))
            audio_data.append(audio)

        if audio_data:
            combined_audio = np.concatenate(audio_data)

            # Normalize
            max_val = np.max(np.abs(combined_audio))
            if max_val > 0:
                combined_audio = combined_audio / max_val * 0.9

            # Save audio file for this slide
            # ✅ Use slide index based on actual slides processed
            slide_num = len(saved_files) + 1
            Audio_file_name = f"slide{slide_num}_audio.wav"
            my_audio_file_path = rf"../my_audios/{Audio_file_name}"

            wavfile.write(my_audio_file_path, 24000, combined_audio)
            saved_files.append(my_audio_file_path)

            print(f"✅ Saved {my_audio_file_path}")
            display(Audio(my_audio_file_path))

    return saved_files


# Usage
text_output = save_to_simple_text("my_result.txt")
audio_files = generate_audio_from_slides(text_output)
print("All audios generated:", audio_files)
