# learn_pipeline.py

from embedding.model_loader import load_model
from embedding.embedder import embed_text
import json
import numpy as np
from pathlib import Path
from embedding.text_encoder import format_time, profile_to_text

def run_learn_mode():
    print("=" * 80)
    print("Kanana Embedding Generation - Learning Mode")
    print("=" * 80)
    
    tokenizer, model, device = load_model()
    
    input_dir = Path("./Data")
    output_dir = Path.cwd()
    
    profile_files = [...]
    
    results = {}
    
    for filepath in profile_files:
        if not filepath.exists():
            print(f"⚠ Warning: {filepath} not found, skipping...")
            continue
        
        print(f"\n{'=' * 80}")
        print(f"Processing: {filepath.name}")
        print('=' * 80)
        
        # Load JSON
        with open(filepath, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        
        # Convert to text
        profile_text = profile_to_text(profile_data)
        print("\nText representation:")
        print("-" * 80)
        print(profile_text)
        print("-" * 80)
        
        # Generate embedding
        print("\nGenerating embedding...")
        embedding = embed_text(profile_text, tokenizer, model, device)
        
        print(f"✓ Embedding generated")
        print(f"  Shape: {embedding.shape}")
        print(f"  First 10 values: {embedding[:10]}")
        
        # Save results
        profile_name = profile_data['profile_name']
        results[profile_name] = {
            'profile_data': profile_data,
            'text': profile_text,
            'embedding': embedding
        }
        
        # Save individual embedding as numpy file
        output_file = output_dir / f"{filepath.stem}_embedding.npy"
        np.save(output_file, embedding)
        print(f"✓ Saved to: {output_file}")
        
        # Save as JSON too
        json_output = output_dir / f"{filepath.stem}_embedded.json"
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump({
                'profile_data': profile_data,
                'profile_text': profile_text,
                'embedding': embedding.tolist(),
                'embedding_shape': list(embedding.shape)
            }, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved JSON to: {json_output}")
    
    # 끝 부분
    np.savez(...)
    print("✓ Completed")
