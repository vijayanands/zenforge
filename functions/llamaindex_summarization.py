import json
import uuid

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SimpleNodeParser
from helpers.get_llm import get_llm

def summarize_data(data, id=None):
    # Check if data is a string (possibly a JSON string)
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            raise ValueError("The input string is not a valid JSON")

    # Ensure data is a dictionary
    if not isinstance(data, dict):
        raise ValueError(
            "Input must be a dictionary or a JSON string representing a dictionary"
        )

    # Convert the dictionary to LlamaIndex Document objects
    documents = []
    if not isinstance(data, dict):
        raise ValueError(
            f"Each value in the dictionary must be a dictionary, found {type(doc)} for key {key}"
        )

    content = data.get("content")
    if not content:
        raise ValueError(f"The dictionary for key {data} must contain a 'content' key")

    extra_info = {k: v for k, v in data.items() if k != "content"}
    # Initialize id randomly if not provided
    if id is None:
        id = str(uuid.uuid4())
    extra_info["id"] = id  # Add the id to extra_info

    # Create Document object with the updated method
    documents.append(Document(text=content, metadata=extra_info))

    # 2. Parse the document into nodes
    parser = SimpleNodeParser.from_defaults(chunk_size=1024, chunk_overlap=20)
    nodes = parser.get_nodes_from_documents(documents)

    # 3. Create an index
    index = VectorStoreIndex(nodes)

    # 4. Create a query engine
    query_engine = index.as_query_engine()

    # 5. Generate the summary
    summary_prompt = "Please provide a comprehensive summary of the document."
    # Customize the LLM
    llm = get_llm(model="gpt-3.5-turbo", temperature=0.1)
    query_engine_custom = index.as_query_engine(llm=llm)
    summary_custom = query_engine_custom.query(summary_prompt)

    print(summary_custom.response)
    return summary_custom.response
