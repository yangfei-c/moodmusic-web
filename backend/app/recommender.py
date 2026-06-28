from __future__ import annotations

import numpy as np

from app.config import (
    strategy_tag,
    tags_26,
    prototype_alpha,
    prototype_top_percent,
    rerank_pool_size,
)
from app.services.music_repository import load_tracks
from app.services.scoring import compute_scores
from app.services.tag_prototype import compute_tag_prototypes
from app.services.user_state import UserStateEstimator
from app.services.utils import (
    make_prototype_prior,
    make_uniform_prior,
    select_nearest_tags,
    mmr_rerank,
)


class RecommenderService:
    def __init__(self):
        self.estimator = UserStateEstimator()
        self.tracks = load_tracks()

        if not self.tracks:
            raise RuntimeError("No tracks loaded. Please check semantic_db.json path and format.")

        self.prototypes = compute_tag_prototypes(
            self.tracks,
            top_percent=prototype_top_percent,
        )

        self.z_matrix = np.asarray([t["va"] for t in self.tracks], dtype=np.float32)
        self.y_matrix = np.asarray([t["tag26"] for t in self.tracks], dtype=np.float32)

    def build_tag_prior(self, strategy: str, mu_q, prior_mode: str = "prototype"):
        labels = strategy_tag.get(strategy, [])

        if labels == "auto" or labels == ["auto"]:
            labels = select_nearest_tags(
                mu_q=mu_q,
                prototypes=self.prototypes,
                tag26=tags_26,
            )

        if prior_mode == "uniform":
            return make_uniform_prior(labels, tags_26), labels

        return make_prototype_prior(
            mu_q=mu_q,
            labels=labels,
            tag26=tags_26,
            prototypes=self.prototypes,
            alpha=prototype_alpha,
        ), labels

    def recommend(
        self,
        text: str,
        strategy: str,
        strength: float = 0.5,
        top_k: int = 5,
        gamma: float = 1.0,
        alpha: float = 1.0,
        beta: float = 1.0,
        diversity_weight: float = 0.0,
    ):
        state = self.estimator.process(
            text=text,
            strategy=strategy,
            strength=strength,
        )

        tau, selected_labels = self.build_tag_prior(
            strategy=strategy,
            mu_q=state["mu_q"],
            prior_mode="prototype",
        )

        scores = compute_scores(
            z_matrix=self.z_matrix,
            y_matrix=self.y_matrix,
            z_q=state["z_q"],
            mu_q=state["mu_q"],
            tau=tau,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
        )

        results = []

        for i, track in enumerate(self.tracks):
            z_i = track["va"]

            results.append({
                "song_id": track["song_id"],
                "audio_url": track.get("audio_url", ""),
                "song_path": track.get("song_path", ""),
                "display_tags": track.get("display_tags", []),
                "tag26": track.get("tag26", []),
                "va": [float(z_i[0]), float(z_i[1])],
                "valence": float(z_i[0]),
                "arousal": float(z_i[1]),
                "score": float(scores["total_score"][i]),
                "curr_dist": float(scores["curr_dist"][i]),
                "target_dist": float(scores["target_dist"][i]),
                "tag_score": float(scores["tag_score"][i]),
            })

        ranked = sorted(results, key=lambda x: x["score"], reverse=True)

        if diversity_weight > 0:
            pool_size = min(len(ranked), max(rerank_pool_size, top_k))
            ranked = mmr_rerank(
                ranked[:pool_size],
                score_key="score",
                top_k=top_k,
                diversity_weight=diversity_weight,
                vector_key="tag26",
            )
        else:
            ranked = ranked[:top_k]

        return {
            "state": {
                "z_q": state["z_q"],
                "mu_q": state["mu_q"],
                "anchor": state["anchor"],
                "delta": state["delta"],
                "strategy": state["strategy"],
                "strength": state["strength"],
                "selected_strategy_tags": selected_labels,
            },
            "recommendations": ranked,
        }
