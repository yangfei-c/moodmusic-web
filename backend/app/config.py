from __future__ import annotations

from pathlib import Path

current_dir = Path(__file__).resolve().parent
backend_root = current_dir.parent

# Paths
music_db_path = backend_root / "data" / "semantic_db.json"
text_ckpt = backend_root / "data" / "last.ckpt"
feedback_log_path = backend_root / "data" / "feedback_events.jsonl"

# Text VA model
text_model_name = "xlm-roberta-base"
text_max_length = 128

# Strategy
strategies = ["maintain", "calm", "energize", "comfort"]
strength = 0.5
recommendation_pool_size = 10

# Tag List
tags_26 = [
    "ambient", "classical", "electronic", "folk", "hiphop", "jazz",
    "metal", "pop", "rock", "soundtrack",
    "bass", "drums", "guitar", "piano", "strings", "synthesizer", "voice",
    "dark", "dream", "energetic", "epic", "film", "happy", "love", "relaxing", "sad",
]

strategy_anchors = {
    "calm": [-0.2437, -0.3755],      # ambient, relaxing, piano, dream, classical
    "energize": [0.1588, 0.2711],    # energetic, electronic, rock, pop, happy, drums
    "comfort": [-0.1940, -0.3179],   # piano, sad, classical, dream, relaxing
}

strategy_tag = {
    "maintain": ["auto"],
    "calm": ["ambient", "relaxing", "piano", "dream", "classical"],
    "energize": ["energetic", "electronic", "rock", "pop", "happy"],
    "comfort": ["piano", "sad", "classical", "dream", "relaxing"],
}
prototype_top_percent = 0.05
prototype_alpha = 10.0
text_list = [
    {"text": "我现在有点低落。", "intent": "comfort"},
    {"text": "I feel tired and quiet tonight.", "intent": "comfort"},
]

# Diversity
diversity_weights = {
    "关闭": 0.00,
    "低": 0.15,
    "中": 0.30,
    "高": 0.50,
}
default_diversity = "低"
rerank_pool_size = 200
