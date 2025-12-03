"""
Complete Kanana Embedding Script for SLURM GPU Environment
============================================================

This script is ready to run on your SLURM cluster with GPU support.

Usage:
    srun --gres=gpu:1 python context_embedding.py

Or create a batch script:
    sbatch run_embedding.sh

"""

import json
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
import os
from pathlib import Path


def load_model(model_name="kakaocorp/kanana-nano-2.1b-embedding"):
    """
    Load Kanana model with trust_remote_code=True to avoid prompts.
    """
    print(f"Loading model: {model_name}")
    
    # IMPORTANT: trust_remote_code=True is required for Kanana model
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
    
    model.eval()
    
    # Use GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    
    print(f"✓ Model loaded successfully on {device}")
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  CUDA Version: {torch.version.cuda}")
    
    return tokenizer, model, device


def profile_to_text(profile_data):
    """
    Convert JSON profile to natural language text.
    """
    text_parts = []
    
    text_parts.append(f"Profile: {profile_data.get('profile_name', 'Unknown')}")
    
    if 'current_residence' in profile_data:
        coords = profile_data['current_residence']
        text_parts.append(f"Current residence: latitude {coords[0]:.3f}, longitude {coords[1]:.3f}")
    
    if 'frequently_visited_area' in profile_data:
        areas = profile_data['frequently_visited_area']
        text_parts.append(f"Frequently visits {len(areas)} areas:")
        for i, area in enumerate(areas, 1):
            text_parts.append(f"  Area {i}: ({area[0]:.3f}, {area[1]:.3f})")
    
    if 'preferred_areas' in profile_data:
        areas = profile_data['preferred_areas']
        text_parts.append(f"Preferred areas for meetings ({len(areas)} locations):")
        for i, area in enumerate(areas, 1):
            text_parts.append(f"  Preferred {i}: ({area[0]:.3f}, {area[1]:.3f})")
    
    if 'work_schedule' in profile_data:
        text_parts.append("Work schedule:")
        for day, times in profile_data['work_schedule'].items():
            if times:
                for time_range in times:
                    start = format_time(time_range[0])
                    end = format_time(time_range[1])
                    text_parts.append(f"  {day}: {start} - {end}")
    
    if 'preferred_meeting_schedule' in profile_data:
        text_parts.append("Preferred meeting times:")
        for day, times in profile_data['preferred_meeting_schedule'].items():
            if times:
                for time_range in times:
                    start = format_time(time_range[0])
                    end = format_time(time_range[1])
                    text_parts.append(f"  {day}: {start} - {end}")
    
    return "\n".join(text_parts)


def format_time(hour):
    """Convert decimal hour to HH:MM format."""
    hours = int(hour)
    minutes = int((hour - hours) * 60)
    return f"{hours:02d}:{minutes:02d}"


def generate_embedding(text, tokenizer, model, device, max_length=512):
    """
    Generate embedding vector from text.
    """
    # Tokenize
    inputs = tokenizer(
        text,
        return_tensors="pt",
        max_length=max_length,
        truncation=True,
        padding=True
    )
    
    # Move to device
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    # Generate embeddings
    with torch.no_grad():
        # Kanana model requires pool_mask parameter
        # pool_mask indicates which tokens to use for pooling (same as attention_mask)
        inputs['pool_mask'] = inputs['attention_mask']
        
        outputs = model(**inputs)
        
        # Kanana model returns EmbeddingModelOutput with different attributes
        # Try different possible output formats
        
        # First, try accessing as dict-like object with 'embedding' key
        if hasattr(outputs, '__getitem__') and 'embedding' in outputs:
            # Kanana model uses 'embedding' (singular) as dict key
            embedding = outputs['embedding'].cpu().numpy().squeeze()
        elif hasattr(outputs, 'embedding') and outputs.embedding is not None:
            # Try as attribute 'embedding' (singular)
            embedding = outputs.embedding.cpu().numpy().squeeze()
        elif hasattr(outputs, 'embeddings') and outputs.embeddings is not None:
            # Try 'embeddings' (plural)
            embedding = outputs.embeddings.cpu().numpy().squeeze()
        elif hasattr(outputs, 'pooler_output') and outputs.pooler_output is not None:
            # Pooled output
            embedding = outputs.pooler_output.cpu().numpy().squeeze()
        elif hasattr(outputs, 'last_hidden_state') and outputs.last_hidden_state is not None:
            # Standard transformer output - need manual pooling
            embeddings = outputs.last_hidden_state
            attention_mask = inputs['attention_mask']
            
            # Mean pooling
            mask_expanded = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
            sum_embeddings = torch.sum(embeddings * mask_expanded, 1)
            sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
            embedding = (sum_embeddings / sum_mask).cpu().numpy().squeeze()
        else:
            # Fallback: inspect the output object to find the tensor
            print(f"Warning: Unexpected output format. Type: {type(outputs)}")
            print(f"Available attributes: {[a for a in dir(outputs) if not a.startswith('_')]}")
            
            # Try to extract tensor from the output object
            embedding_found = False
            
            # Check if output is dict-like
            if hasattr(outputs, 'keys'):
                for key in outputs.keys():
                    value = outputs[key]
                    if isinstance(value, torch.Tensor) and value is not None:
                        if len(value.shape) == 2:
                            embedding = value.cpu().numpy().squeeze()
                            embedding_found = True
                            print(f"Using tensor from key: '{key}'")
                            break
            
            # Check __dict__
            if not embedding_found and hasattr(outputs, '__dict__'):
                for key, value in outputs.__dict__.items():
                    if isinstance(value, torch.Tensor) and value is not None:
                        if len(value.shape) == 2:
                            embedding = value.cpu().numpy().squeeze()
                            embedding_found = True
                            print(f"Using tensor from attribute: '{key}'")
                            break
            
            if not embedding_found:
                raise RuntimeError(
                    f"Could not extract embedding from model output.\n"
                    f"Output type: {type(outputs)}\n"
                    f"Available attributes: {[a for a in dir(outputs) if not a.startswith('_')]}\n"
                    f"Please run 'debug_kanana_output.py' to inspect the model output structure."
                )
    
    return embedding


def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def main():
    print("=" * 80)
    print("Kanana Embedding Generation - SLURM GPU Environment")
    print("=" * 80)
    
    # Load model
    tokenizer, model, device = load_model()
    
    # Define input files (update these paths to your actual file locations)
    input_dir = Path("./Data")  # Directory containing profile JSON files
    output_dir = Path.cwd()  # Current directory
    
    profile_files = [
        input_dir / "Base_Info_1.json",
        input_dir / "Base_Info_2.json",
        input_dir / "Base_Info_3.json"
    ]
    
    # Process each profile
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
        embedding = generate_embedding(profile_text, tokenizer, model, device)
        
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
    
    # Calculate similarities
    if len(results) > 1:
        print(f"\n{'=' * 80}")
        print("Similarity Matrix")
        print('=' * 80)
        
        profile_names = list(results.keys())
        for i, name1 in enumerate(profile_names):
            for j, name2 in enumerate(profile_names):
                if i < j:
                    emb1 = results[name1]['embedding']
                    emb2 = results[name2]['embedding']
                    sim = cosine_similarity(emb1, emb2)
                    print(f"{name1} <-> {name2}")
                    print(f"  Cosine Similarity: {sim:.4f}")
                    print()
    
    # Save all embeddings together
    all_embeddings_file = output_dir / "all_embeddings.npz"
    np.savez(
        all_embeddings_file,
        **{name: results[name]['embedding'] for name in results.keys()}
    )
    print(f"✓ All embeddings saved to: {all_embeddings_file}")
    
    print(f"\n{'=' * 80}")
    print("✓ Processing Complete!")
    print('=' * 80)
    print(f"\nGenerated {len(results)} embeddings")
    print("\nOutput files:")
    for name in results.keys():
        print(f"  - {name.replace(' ', '_')}_embedding.npy")
    print(f"  - all_embeddings.npz")


if __name__ == "__main__":
    main()