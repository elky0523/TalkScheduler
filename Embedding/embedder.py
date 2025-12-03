import torch

def embed_text(text, tokenizer, model, device):
    """
    Generate embedding vector from text.
    """
    max_length=512
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