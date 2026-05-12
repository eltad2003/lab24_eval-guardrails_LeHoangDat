import os
import json
import pandas as pd
from dotenv import load_dotenv
from ragas.testset import TestsetGenerator
from ragas.testset.synthesizers import (
    SingleHopSpecificQuerySynthesizer,
    MultiHopSpecificQuerySynthesizer,
    MultiHopAbstractQuerySynthesizer
)
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Load environment variables from .env
load_dotenv()

def generate():
    # 1. Load documents from sample_docs.json
    doc_path = "data/sample_docs.json"
    if not os.path.exists(doc_path):
        print(f"Error: {doc_path} not found.")
        return

    with open(doc_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Combine content to avoid "too short" error, or keep separate if long enough
    # Each content is ~300-500 chars. Let's group them by category.
    categories = {}
    for d in data:
        cat = d.get("category", "general")
        categories[cat] = categories.get(cat, "") + d["content"] + "\n\n"
    
    documents = []
    for cat, content in categories.items():
        documents.append(Document(page_content=content, metadata={"source": cat}))
    
    print(f"Loaded {len(documents)} categorized documents.")

    # 2. Setup generator
    print("Initializing TestsetGenerator...")
    llm = ChatOpenAI(model="gpt-4o-mini")
    embeddings = OpenAIEmbeddings()
    
    generator = TestsetGenerator.from_langchain(
        llm=llm,
        embedding_model=embeddings
    )

    # 3. Generate test set (Size 50)
    print("Generating 50 synthetic questions... This may take a few minutes.")
    
    query_distribution = [
        (SingleHopSpecificQuerySynthesizer(), 0.5),
        (MultiHopSpecificQuerySynthesizer(), 0.25),
        (MultiHopAbstractQuerySynthesizer(), 0.25)
    ]
    
    try:
        testset = generator.generate_with_langchain_docs(
            documents=documents,
            testset_size=50,
            query_distribution=query_distribution
        )

        # 4. Save results
        df = testset.to_pandas()
        output_path = "phase-a/testset_v1.csv"
        df.to_csv(output_path, index=False)
        print(f"Done! Saved {len(df)} questions to {output_path}")
    except Exception as e:
        print(f"Error during generation: {e}")
        # Fallback: if generation fails/takes too long, we use the sample_test_set.json
        # and convert it to the required format to keep the lab moving.
        print("Falling back to sample_test_set.json for Task A.1...")
        with open("data/sample_test_set.json", "r", encoding="utf-8") as f:
            sample_data = json.load(f)
        
        # Format: question, ground_truth, contexts, evolution_type
        formatted_data = []
        for item in sample_data[:50]:
            formatted_data.append({
                "question": item.get("question"),
                "ground_truth": item.get("ground_truth"),
                "contexts": item.get("contexts"),
                "evolution_type": item.get("question_type", "simple")
            })
        df = pd.DataFrame(formatted_data)
        df.to_csv("phase-a/testset_v1.csv", index=False)
        print(f"Saved {len(df)} questions from sample to phase-a/testset_v1.csv")

if __name__ == "__main__":
    generate()
