def System_prompts(mode: str):
    """
    Returns a system prompt based on the mode.
    mode ∈ {"pdf", "audio", "video", "text"}
    """
    prompts = {
        "pdf": """You are a helpful assistant that prepares lectures in a structured and well-mannered PDF-friendly format. 
Instructions:
1. Always include the topic name at the very top.
2. Always include the headings (use the actual heading names, NOT the word "heading").
3. For each heading, provide its content in full detail.
4. Keep the order logical and clean.
5. Do not include any extra commentary outside the retrieved lecture content.
6. Strictly use only the retrieved content and do not extract or fabricate any unrelated information.
7. Do not include any contact information related to Ms. Kainat Anjum.""",
        "audio": """You are a helpful assistant that prepares lecture content for audio narration. 
Instructions:
1. Only provide the lecture's content/paragraphs.
2. Do NOT include the topic name.
3. Do NOT include any heading names.
4. Keep the flow natural for spoken audio.
5. Strictly use only the retrieved content and do not extract or fabricate any unrelated information.
6. Do not include any contact information related to Ms. Kainat Anjum.""",
        "video": """You are a helpful assistant that prepares lecture outlines for video format. 
Instructions:
1. Provide only the topic name and all of the headings names included in the asked context.
2. Do NOT include the content under each heading.
3. List the topic name first, then list all headings separately (not merged).
4. Strictly use only the retrieved content and do not extract or fabricate any unrelated information.
5. Do not include any contact information related to Ms. Kainat Anjum.""",
        "text": """You are a helpful assistant that extract the headings from the paragraph and the provide the result in this formate: Output Format (MUST be valid JSON), content should be different for each slide. for example first slide should contain first heading as key and first paragraph as value then 2nd heading as key and then 2nd paragraph as value and up to so on this process will continue till the first slide must have 4 headings and 4 paragraphs then make a 2nd slide and repeat the formate, include the rest of the headings and paragraphs in the 2nd slide as key and value:
{
    slide1: {
        keypoint1: <explanation of key point 1/paragraph>,
        keypoint2: <explanation of key point 2/paragraph>,
    
    }
    slide2: {
        keypoint1: <explanation of key point 1/paragraph>,
        keypoint2: <explanation of key point 2/paragraph>,
    }
           .
           .
           .
           .
           .
    slideN: {
        keypoint1: <explanation of key point 1/paragraph>,
        keypoint2: <explanation of key point 2/paragraph>,
    }
}.
Instructions:
2: First of all, Include the topic name. topic name is not included in dict.
1. Include the headings and the material under them.
3. Keep formatting clean and easy to read.
4. Strictly use only the retrieved content and do not extract or fabricate any unrelated information.
5. Do not include any contact information related to Ms. Kainat Anjum.



Rules:
- Only return valid JSON — no explanations, no extra text.
- Keep all paragraph quotes intact.
- Do not add Markdown formatting like ** or * or headings.
- Place all definitions or descriptions that are not headings into the paragraphs array.
- Preserve the exact wording from the input."""
        f"Extract the content from this pdf{file_path}",
    }

    if mode not in prompts:
        raise ValueError(f"Invalid mode '{mode}'. Choose from: {list(prompts.keys())}")

    return ("system", prompts[mode])


# Example usage
role, prompt = System_prompts("text")
print(role)  # system
print(prompt)  # pdf prompt text


def relevant_knowledge(
    my_g_api_k,
    my_ns,
    my_k,
    my_g_qmodel,
    task_instruction,
    prompt_type,
    mode,
    instructions,
):

    # ✅ Load retrieval QA prompt from LangChain Hub
    retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")

    # ✅ Create a retriever from your Pinecone vectorstore
    retriever = docsearch.as_retriever(search_kwargs={"namespace": my_ns, "k": my_k})

    # ✅ Gemini model for retrieval step
    llm_for_retrieval = ChatGoogleGenerativeAI(
        model=my_g_qmodel, temperature=0.0, google_api_key=my_g_api_k
    )

    # ✅ Combine docs chain
    combine_docs_chain = create_stuff_documents_chain(
        llm_for_retrieval, retrieval_qa_chat_prompt
    )

    # ✅ Retrieval chain
    retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

    # 🔹 Step 1: Get context from vectorstore
    retrieval_result = retrieval_chain.invoke({"input": task_instruction})
    context = retrieval_result["answer"]

    messages = [
        prompt_type(mode),
        (
            "user",
            f"Based only on the following content:\n\n{retrieval_result}\n\nTask: {task_instruction}",
        ),
    ]

    # ✅ Step 3: Final LLM call
    llm_for_task = ChatGoogleGenerativeAI(
        model=my_g_qmodel, temperature=0.0, google_api_key=my_g_api_k
    )

    final_result = llm_for_task.invoke(messages)
    content_text = final_result.content.strip()
    print(content_text)

    return final_result.content.strip()


task_instruction = "extract the text from page number 3 of given pdf..."


# 🔹 Common function for LLM call with mode
def run_llm(mode, instructions=None):
    return relevant_knowledge(
        gemini_api_key,
        "myproaivectors",
        18,
        gemini_model_for_query,
        task_instruction,  # for task_instruction param
        System_prompts,  # for prompt_type
        mode,  # for mode
        task_instruction,  # for instructions param
    )
