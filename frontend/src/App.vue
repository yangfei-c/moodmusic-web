<script setup>
import { ref } from "vue";
import { recommendMusic } from "./api";

const text = ref("我今天有点累，想听点安慰我的音乐");
const strategy = ref("comfort");
const strength = ref(0.5);
const topK = ref(5);

const loading = ref(false);
const error = ref("");
const result = ref(null);

const strategies = [
  { value: "comfort", label: "安慰我" },
  { value: "calm", label: "让我平静" },
  { value: "energize", label: "让我更有活力" },
  { value: "maintain", label: "保持当前状态" },
];

async function submitRecommend() {
  error.value = "";
  result.value = null;
  loading.value = true;

  try {
    result.value = await recommendMusic({
      text: text.value,
      strategy: strategy.value,
      strength: Number(strength.value),
      top_k: Number(topK.value),
    });
  } catch (e) {
    error.value = e.message || "推荐失败，请检查后端是否启动。";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <main class="page">
    <section class="hero">
      <div>
        <h1>情绪调节型音乐推荐</h1>
        <p>输入你现在的状态，选择希望音乐带来的帮助，系统会推荐更合适的音乐。</p>
      </div>
    </section>

    <section class="panel">
      <label>你现在的状态</label>
      <textarea v-model="text" rows="4" placeholder="例如：我今天有点累，想听点安慰我的音乐"></textarea>

      <div class="grid">
        <div>
          <label>调节目标</label>
          <select v-model="strategy">
            <option v-for="item in strategies" :key="item.value" :value="item.value">
              {{ item.label }}
            </option>
          </select>
        </div>

        <div>
          <label>调节强度：{{ strength }}</label>
          <input v-model="strength" type="range" min="0" max="1" step="0.05" />
        </div>

        <div>
          <label>推荐数量</label>
          <select v-model="topK">
            <option :value="3">3 首</option>
            <option :value="5">5 首</option>
            <option :value="8">8 首</option>
            <option :value="10">10 首</option>
          </select>
        </div>
      </div>

      <button @click="submitRecommend" :disabled="loading">
        {{ loading ? "正在推荐..." : "开始推荐" }}
      </button>

      <p v-if="error" class="error">{{ error }}</p>
    </section>

    <section v-if="result" class="result">
      <h2>推荐结果</h2>

      <div class="state">
        <div>
          <span>当前情绪 VA</span>
          <strong>{{ result.state.z_q.map(x => x.toFixed(3)).join(", ") }}</strong>
        </div>
        <div>
          <span>目标情绪 VA</span>
          <strong>{{ result.state.mu_q.map(x => x.toFixed(3)).join(", ") }}</strong>
        </div>
        <div>
          <span>相关标签</span>
          <strong>{{ result.state.selected_strategy_tags.join(" · ") }}</strong>
        </div>
      </div>

      <div class="songs">
        <article v-for="(song, index) in result.recommendations" :key="song.song_id" class="song-card">
          <div class="song-head">
            <h3>推荐 {{ index + 1 }} · {{ song.song_id }}</h3>
            <span>score {{ song.score.toFixed(4) }}</span>
          </div>

          <p class="tags">
            {{ Array.isArray(song.display_tags) ? song.display_tags.join(" · ") : song.display_tags }}
          </p>

          <p class="va">
            Valence: {{ song.va[0].toFixed(3) }} / Arousal: {{ song.va[1].toFixed(3) }}
          </p>

          <audio v-if="song.audio_url" :src="song.audio_url" controls></audio>
          <p v-else class="error">没有 audio_url</p>
        </article>
      </div>
    </section>
  </main>
</template>