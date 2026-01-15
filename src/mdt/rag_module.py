import os
from tqdm import tqdm
from typing import List
from pathlib import Path
import aiofiles
from autogen_core.memory import Memory, MemoryContent, MemoryMimeType
from autogen_ext.memory.chromadb import ChromaDBVectorMemory, PersistentChromaDBVectorMemoryConfig
from autogen_ext.memory.chromadb._chroma_configs import SentenceTransformerEmbeddingFunctionConfig

# Try to import SentenceTransformerEmbeddingFunction for open source embeddings
try:
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    # Use a standard open source model. This requires sentence-transformers to be installed.
    # If not, it might fail, so we can fallback or let the user know.
    # We use all-MiniLM-L6-v2 which is the default for ChromaDB anyway, but being explicit is good.
    embedding_function = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
except ImportError:
    # Fallback to None, which will use ChromaDB's default embedding function (also all-MiniLM-L6-v2 usually)
    print("Warning: sentence-transformers not found. Using ChromaDB default embedding function.")
    embedding_function = None

class SimpleDocumentIndexer:
    """Basic document indexer for AutoGen Memory."""

    def __init__(self, memory: Memory, chunk_size: int = 1000, overlap: int = 200) -> None:
        self.memory = memory
        self.chunk_size = chunk_size
        self.overlap = overlap

    async def _read_text_file(self, file_path: str) -> str:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            return await f.read()

    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap."""
        chunks: list[str] = []
        if not text:
            return chunks
        
        start = 0
        text_len = len(text)
        
        # If text is shorter than chunk size, just return it
        if text_len <= self.chunk_size:
            return [text]

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk = text[start:end]
            chunks.append(chunk.strip())
            
            # Move start forward, but ensure we don't get stuck if overlap >= chunk_size
            step = max(1, self.chunk_size - self.overlap)
            start += step
            
            # Break if we've reached the end
            if start >= text_len:
                break
            
        return chunks

    async def index_folder(self, folder_path: str) -> int:
        """Index all txt files in a folder into memory."""
        total_chunks = 0
        folder = Path(folder_path)
        
        if not folder.exists():
            # print(f"Warning: Knowledge base folder {folder_path} does not exist.")
            return 0

        # Get all txt files
        files = list(folder.glob("*.txt"))
        
        for file_path in files:
            try:
                content = await self._read_text_file(str(file_path))
                chunks = self._split_text(content)

                for i, chunk in tqdm(enumerate(chunks)):
                    # Use file name as source
                    source = file_path.name
                    await self.memory.add(
                        MemoryContent(
                            content=chunk, 
                            mime_type=MemoryMimeType.TEXT, 
                            metadata={"source": source, "chunk_index": i}
                        )
                    )

                total_chunks += len(chunks)
                print(f"Indexed {len(chunks)} chunks from {file_path.name}")

            except Exception as e:
                print(f"Error indexing {file_path}: {str(e)}")

        return total_chunks

def get_persistent_memory(agent_name: str) -> ChromaDBVectorMemory:
    """Get a persistent memory instance for an agent."""
    # Store vector db in a dedicated folder in data/rag_storage
    # Assuming we are in src/, so data is ../data
    db_path = os.path.join("./data", "rag_storage", agent_name)
    
    # Ensure directory exists
    os.makedirs(db_path, exist_ok=True)
    
    return ChromaDBVectorMemory(
        config=PersistentChromaDBVectorMemoryConfig(
            collection_name=f"{agent_name}_docs",
            persistence_path=db_path,
            k=10,  # Return top 10 results
            score_threshold=0.7,  # Minimum similarity score
            embedding_function_config=SentenceTransformerEmbeddingFunctionConfig()
        ),
    )

async def initialize_agent_memory(agent_name: str, kb_folder: str):
    """Initialize memory for an agent and index documents if needed."""
    memory = get_persistent_memory(agent_name)
    
    # Check if we need to index by looking for a marker file
    # This avoids re-indexing every time
    db_path = memory._config.persistence_path
    marker_file = Path(db_path) / ".indexed"
    
    if not marker_file.exists():
        print(f"Indexing documents for {agent_name} from {kb_folder}...")
        indexer = SimpleDocumentIndexer(memory=memory)
        count = await indexer.index_folder(kb_folder)
        
        # Create marker file even if count is 0 to avoid retrying empty folders constantly
        # unless we want to support dynamic addition. For now, assume static KB.
        marker_file.touch()
        if count > 0:
            print(f"Completed indexing for {agent_name}. Total chunks: {count}")
        else:
            print(f"No documents found or indexed for {agent_name}.")
    # else:
        # print(f"Memory for {agent_name} already indexed. Skipping.")
        
    return memory
