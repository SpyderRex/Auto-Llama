from autollama.llm.base import ChatModelInfo, EmbeddingModelInfo, TextModelInfo

GROQ_CHAT_MODELS = {
    info.name: info
    for info in [
        ChatModelInfo(
            name="llama3-8b-8192",
            prompt_token_cost=0.0,
            completion_token_cost=0.0,
            max_tokens=8000,
        ),
        ChatModelInfo(
            name="llama-3.1-70b-versatile",
            prompt_token_cost=0.0,
            completion_token_cost=0.0,
            max_tokens=8000,
            )
    ]
}

GROQ_TEXT_MODELS = {
    info.name: info
    for info in [
        TextModelInfo(
            name="llama3-8b-8192",
            prompt_token_cost=0.0,
            completion_token_cost=0.0,
            max_tokens=8000,
        ),
        TextModelInfo(
            name="llama-3.1-70b-versatile",
            prompt_token_cost=0.0,
            completion_token_cost=0.0,
            max_tokens=8000,
            )

    ]
}

EMBEDDING_MODELS = {
    info.name: info
    for info in [
        EmbeddingModelInfo(
            name="en_core_web_md",
            prompt_token_cost=0.0,
            completion_token_cost=0.0,
            max_tokens=500,
            embedding_dimensions=300,
        ),
    ]
}

GROQ_MODELS: dict[str, ChatModelInfo | EmbeddingModelInfo | TextModelInfo] = {
    **GROQ_CHAT_MODELS,
    **GROQ_TEXT_MODELS,
    **EMBEDDING_MODELS,
}
