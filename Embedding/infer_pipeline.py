# embedding/infer_pipeline.py

from embedding.model_loader import load_model
from embedding.embedder import embed_text
from embedding.text_encoder import profile_to_text

# 전역 변수 - 한 번만 로드됨
tokenizer = None
model = None
device = None


def init_infer_pipeline(model_name="kakaocorp/kanana-nano-2.1b-embedding"):
    """
    GUI(Integrated Agent) 시작 시 반드시 한 번 호출됨.
    Kanana 모델을 메모리에 로딩하고 infer mode 준비.
    """
    global tokenizer, model, device

    if tokenizer is None:
        tokenizer, model, device = load_model(model_name)
        print("✓ infer_pipeline initialized — model loaded.")

    else:
        print("✓ infer_pipeline already initialized — model reused.")


def embed_for_agent(user_json_payload: dict):
    """
    1) JSON user payload → 자연어 텍스트 변환
    2) 텍스트 → embedding 생성
    3) embedding 벡터 반환
    """

    if tokenizer is None:
        raise RuntimeError(
            "infer_pipeline not initialized. "
            "Call init_infer_pipeline() before embedding."
        )

    # 1) JSON → 자연어 텍스트
    text = profile_to_text(user_json_payload)

    # 2) 텍스트 → embedding
    vector = embed_text(text, tokenizer, model, device)

    return vector
