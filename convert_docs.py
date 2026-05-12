import json
import os

def convert():
    if not os.path.exists("docs"):
        os.makedirs("docs")
    
    with open("data/sample_docs.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for d in data:
        filename = f"docs/{d['doc_id']}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {d['title']}\n\n{d['content']}")
    print(f"Converted {len(data)} docs to markdown in docs/")

if __name__ == "__main__":
    convert()
