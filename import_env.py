import os

HUGGINGFACE_ENABLED = os.environ.get('HUGGINGFACE_ENABLED', 'false')

if HUGGINGFACE_ENABLED == 'false':
    from dotenv import load_dotenv
    load_dotenv()

