import torch
from transformers import AutoTokenizer, AutoModel

def load_model(model_name="kakaocorp/kanana-nano-2.1b-embedding"):
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    return tokenizer, model, device
