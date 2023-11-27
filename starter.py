#STARTER PY WHAT THE FUCK
import os
import logging
import sys
from llama_index import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage

# Set up logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

# Set the OpenAI API Key from an environment variable
os.environ['OPENAI_API_KEY'] = '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'


# Check if the indexed storage already exists
if not os.path.exists("./storage"):
    # If not, load the documents and create the index
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents)

    # Persist the index for later use
    index.storage_context.persist()
else:
    # If it exists, load the index from storage
    storage_context = StorageContext.from_defaults(persist_dir="./storage")
    index = load_index_from_storage(storage_context)

# Create a query engine and query the index
query_engine = index.as_query_engine()
response = query_engine.query("Does Jacob Fast Like Pizza??")
print(response)
