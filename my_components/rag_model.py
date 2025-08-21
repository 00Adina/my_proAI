# === Step 1: Extract text from PDF ===
def Extract_ext_from_PDF(file_path):
    pdf_text = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            pdf_text += page.extract_text() + "\n"

    return pdf_text


pdf_text = Extract_ext_from_PDF(file_path)


# === Step 2: Create chunker with overlap ===
def chunk_and_overlap(c_size, c_overlap):
    text_splitter = CharacterTextSplitter(
        separator="\n",  # split by newlines
        chunk_size=c_size,  # max characters per chunk
        chunk_overlap=c_overlap,  # overlap between chunks
        length_function=len,
    )

    chunks = text_splitter.split_text(pdf_text)

    # === Step 3: Show result ===
    for i, chunk in enumerate(chunks, start=1):  # first 5 chunks
        print(f"--- Chunk {i} ---")
        print(chunk)
        print()
    return chunks


chunks = chunk_and_overlap(700, 100)


def generating_embeddings(my_model, my_pc_Api):

    embeddings = GoogleGenerativeAIEmbeddings(
        model=my_model, pinecone_api_key=my_pc_Api
    )
    return embeddings


embeddings = generating_embeddings(
    gemini_model_for_embaddings, os.environ["PINECONE_API_KEY"]
)

# Creating index


def creating_Index(my_pc, my_IN):

    pc = my_pc

    cloud = "aws"
    region = "us-east-1"
    spec = ServerlessSpec(cloud=cloud, region=region)

    index_name = my_IN

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name, dimension=embeddings.dimension, metric="cosine", spec=spec
        )

    # See that it is empty
    print("Index before upsert:")
    print(pc.Index(index_name).describe_index_stats())
    print("\n")
    return pc


pc = creating_Index(Pinecone(os.environ["PINECONE_API_KEY"]), Index_name)


# Embed and upsert each chunk as a distinct record in a namespace called myproaiNamespace
def distinct_record(my_ns, my_IN):

    documents = [Document(page_content=chunk) for chunk in chunks]

    # Assign unique but repeatable IDs (hash from text)
    ids = [hashlib.md5(doc.page_content.encode()).hexdigest() for doc in documents]

    docsearch = PineconeVectorStore.from_documents(
        documents=documents,
        index_name=my_IN,
        embedding=embeddings,
        namespace=my_ns,
        ids=ids,
    )

    time.sleep(5)

    # See how many vectors have been upserted
    print("Index after upsert:")
    print(pc.Index(Index_name).describe_index_stats())
    print("\n")
    time.sleep(2)
    return docsearch


docsearch = distinct_record("myproaivectors", Index_name)


def checking_records(my_IN, my_ns):

    index = pc.Index(my_IN)

    for ids in index.list(namespace=my_ns):
        query = index.query(
            id=ids[0],
            namespace=my_ns,
            top_k=1,
            include_values=True,
            include_metadata=True,
        )
        print(query)
        print("\n")


checking_records(Index_name, "myproaivectors")
