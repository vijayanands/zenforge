import os
import random
import shutil
import time
from typing import List
from uuid import NAMESPACE_DNS, uuid5

from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from pydantic import ValidationError

from functions.confluence.confluence import get_confluence_contributions_per_user
from model.pydantic_models import UserData, JiraData, GitHubData, ConfluenceData
from functions.github.github import get_github_contributions_by_repo

# Initialize Pinecone
index_name = "pathforge-data"
local_persist_path = "/tmp/talent-copilot/data/pinecone_store"


def _generate_key(user: str) -> str:
    return str(uuid5(NAMESPACE_DNS, user))


def _get_documents_to_ingest() -> List[Document]:
    jira_documents = get_jira_contributions_per_user()
    github_documents = get_github_contributions_by_repo()
    confluence_documents = get_confluence_contributions_per_user()

    all_user_data = {}
    for email in (
        set(jira_documents.keys())
        | set(github_documents.keys())
        | set(confluence_documents.keys())
    ):
        try:
            user_data = UserData(
                jira=JiraData(
                    **jira_documents.get(
                        email,
                        {
                            "author": email,
                            "total_resolved_issues": 0,
                            "jiras_data": [],
                            "jira_list": [],
                        },
                    )
                ),
                github=GitHubData(
                    **github_documents.get(email, {"commits": [], "pull_requests": []})
                ),
                confluence=ConfluenceData(pages=confluence_documents.get(email, {})),
            )
            all_user_data[email] = user_data
        except ValidationError as e:
            print(f"Error parsing data for user {email}: {e}")
            continue

    documents = []
    for email, user_data in all_user_data.items():
        content = user_data.json()
        metadata = {
            "email": email,
            "has_jira": bool(user_data.jira.jiras_data),
            "has_github": bool(
                user_data.github.commits or user_data.github.pull_requests
            ),
            "has_confluence": bool(user_data.confluence.pages),
        }
        user_id = _generate_key(email)
        doc = Document(text=content, metadata=metadata, id_=user_id)
        documents.append(doc)

    return documents


def create_pinecone_index(pc):
    try:
        print(f"Creating new Pinecone index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

        while True:
            try:
                index_description = pc.describe_index(index_name)
                if index_description.status["ready"]:
                    print(f"Pinecone index {index_name} is ready.")
                    return True
                else:
                    print("Waiting for Pinecone index to be ready...")
                    time.sleep(10)
            except Exception as e:
                print(f"Error checking index status: {e}")
                time.sleep(10)
    except Exception as e:
        print(f"Failed to create Pinecone index: {e}")
        return False


def verify_index_creation_with_retries(documents: List[Document], max_retries: int = 5, retry_delay: int = 10,
                                       sample_size: int = 5, similarity_threshold: float = 0.5) -> bool:
    for attempt in range(max_retries):
        print(f"Verification attempt {attempt + 1} of {max_retries}")
        if verify_index_creation(documents, sample_size, similarity_threshold):
            print("Index verification successful!")
            return True
        else:
            if attempt < max_retries - 1:
                print(f"Verification failed. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("All verification attempts failed.")
    return False


def verify_index_creation(documents: List[Document], sample_size: int = 5, similarity_threshold: float = 0.5) -> bool:
    if not verify_vector_count():
        return False

    sampled_docs = random.sample(documents, min(sample_size, len(documents)))
    query_engine = index.as_query_engine()

    for doc in sampled_docs:
        if not verify_document_retrieval(query_engine, doc, similarity_threshold):
            return False

    return True


def verify_vector_count() -> bool:
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    pinecone_index = pc.Index(index_name)

    stats = pinecone_index.describe_index_stats()
    vector_count = stats["total_vector_count"]

    print(f"Pinecone index stats - Total vectors: {vector_count}")
    return vector_count > 0


def verify_document_retrieval(
    query_engine: BaseQueryEngine, document: Document, similarity_threshold: float
) -> bool:
    snippets = extract_snippets(document.text, num_snippets=3, snippet_length=100)

    for snippet in snippets:
        response = query_engine.query(snippet)
        similarity = calculate_similarity(response.response, document.text)

        if similarity >= similarity_threshold:
            print(f"Successfully retrieved content for document: {document.id_}")
            return True

    print(f"Failed to retrieve content for document: {document.id_}")
    return False


def extract_snippets(
    text: str, num_snippets: int = 3, snippet_length: int = 100
) -> List[str]:
    if len(text) <= snippet_length:
        return [text]

    snippets = []
    for _ in range(num_snippets):
        start = random.randint(0, max(0, len(text) - snippet_length))
        snippets.append(text[start : start + snippet_length])

    return snippets


def calculate_similarity(text1: str, text2: str) -> float:
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    overlap = len(words1.intersection(words2))
    return overlap / min(len(words1), len(words2))


def ingest_data():
    recreate_index = os.getenv("RECREATE_INDEX", "False").lower() == "true"

    embed_model = OpenAIEmbedding()
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))

    if recreate_index or not os.path.exists(local_persist_path):
        if os.path.exists(local_persist_path):
            print(f"Deleting existing local store at {local_persist_path}")
            shutil.rmtree(local_persist_path)

        if index_name in pc.list_indexes().names():
            print(f"Deleting existing Pinecone index: {index_name}")
            pc.delete_index(index_name)

        if not create_pinecone_index(pc):
            print("Failed to create Pinecone index. Exiting.")
            return None

        print("Initializing Pinecone vector store...")
        vector_store = PineconeVectorStore(index_name=index_name)

        print("Creating new storage context...")
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        print("Creating index with new documents...")
        documents = _get_documents_to_ingest()
        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context, embed_model=embed_model
        )

        if verify_index_creation_with_retries(documents):
            print(
                "Index created and verified successfully. Persisting Pinecone store locally..."
            )
            os.makedirs(os.path.dirname(local_persist_path), exist_ok=True)
            storage_context.persist(persist_dir=local_persist_path)
        else:
            print(
                "Failed to verify index creation after multiple attempts. Please check the logs and try again."
            )
            return None
    else:
        print("Loading existing Pinecone store from local persistence...")
        vector_store = PineconeVectorStore(index_name=index_name)
        storage_context = StorageContext.from_defaults(
            persist_dir=local_persist_path, vector_store=vector_store
        )
        index = VectorStoreIndex.from_vector_store(
            vector_store, storage_context=storage_context
        )

    return index


def answer_question(index: VectorStoreIndex, email: str, question: str) -> str:
    query_engine = index.as_query_engine()

    # Construct a query that includes the email and the question
    query = f"For the user with email {email}, {question}"
    response = query_engine.query(query)

    # The response is already in natural language, so we can return it directly
    return response.response


def answer_jira_question(jira_data: JiraData, question: str) -> str:
    if "how many" in question.lower() and "resolved" in question.lower():
        return f"The user has resolved {jira_data.total_resolved_issues} Jira issues."
    elif "links" in question.lower() and "jira" in question.lower():
        return f"Here are the links to the user's Jira issues:\n" + "\n".join(
            jira_data.jira_list
        )
    else:
        return "I'm not sure how to answer this specific Jira question. Please try rephrasing your question."


def answer_github_question(github_data: GitHubData, question: str) -> str:
    if "how many" in question.lower() and "pull requests" in question.lower():
        return f"The user has {len(github_data.pull_requests)} pull requests."
    elif "commits" in question.lower():
        return f"The user has made {len(github_data.commits)} commits."
    else:
        return "I'm not sure how to answer this specific GitHub question. Please try rephrasing your question."


def answer_confluence_question(confluence_data: ConfluenceData, question: str) -> str:
    if "how many" in question.lower() and "pages" in question.lower():
        return f"The user has created {len(confluence_data.pages)} Confluence pages."
    elif "content" in question.lower() and "page" in question.lower():
        page_id = question.split("page")[1].strip()
        if page_id in confluence_data.pages:
            return f"The content of the page '{confluence_data.pages[page_id].title}' is:\n{confluence_data.pages[page_id].content}"
        else:
            return "I couldn't find the specified page. Please provide a valid page ID."
    else:
        return "I'm not sure how to answer this specific Confluence question. Please try rephrasing your question."


def check_pinecone_directly(email):
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    index = pc.Index(index_name)
    results = index.query(
        vector=[0] * 1536, filter={"email": email}, top_k=1, include_metadata=True
    )
    print(f"Direct Pinecone query for {email}: {results}")


# Example usage
if __name__ == "__main__":
    questions = [
        "What are the Jira issues for vijayanands@gmail.com?",
        "How many Jira issues were resolved by vijayanands@gmail.com, can you give the links for those jiras",
        "What are the Jira issues resolved by vijayanands@gmail.com?",
        "How many pull requests are there for vijayanands@yahoo.com?",
        "What is the content of the 'Getting started in Confluence' page for vjy1970@gmail.com?",
        "Which users have GitHub data?",
        "List all email addresses that have Confluence data.",
    ]

    index = ingest_data()
    if index is None:
        print("Failed to create or load index. Exiting.")
        exit(1)

    check_pinecone_directly("vijayanands@gmail.com")

    for question in questions:
        email = "vijayanands@gmail.com"  # You can modify this for different questions if needed
        try:
            answer = answer_question(index, email, question)
            print(f"Question: {question}")
            print(f"Answer: {answer}")
        except Exception as e:
            print(f"An error occurred while answering the question: {str(e)}")
        print()  # Add a blank line for better readability between questions
