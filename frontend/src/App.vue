<script setup>
import { computed, ref } from "vue";
import { nextRecommendation, recommendMusic, submitFeedback } from "./api";

const text = ref("我今天有点累，想听点安慰我的音乐");
const strategy = ref("comfort");
const strength = ref(0.5);

const loading = ref(false);
const nextLoading = ref(false);
const feedbackLoading = ref(false);
const error = ref("");
const feedbackMessage = ref("");
const result = ref(null);
const audioRef = ref(null);
const playDuration = ref(0);
const repeatCount = ref(0);
const endedOnce = ref(false);
const musicPreference = ref(3);
const regulationEffect = ref(3);

const strategies = [
  { value: "comfort", label: "Comfort 安慰" },
  { value: "calm", label: "Calm 平静" },
  { value: "energize", label: "Energize 激活" },
  { value: "maintain", label: "Maintain 保持" },
];

const strengthLevel = computed(() => {
  const value = Number(strength.value);
  if (value < 0.34) return "弱";
  if (value < 0.67) return "中";
  return "强";
});

async function submitRecommend() {
  error.value = "";
  feedbackMessage.value = "";
  result.value = null;
  loading.value = true;
  resetPlayback();

  try {
    result.value = await recommendMusic({
      text: text.value,
      strategy: strategy.value,
      strength: Number(strength.value),
    });
  } catch (e) {
    error.value = e.message || "推荐失败，请检查后端是否启动。";
  } finally {
    loading.value = false;
  }
}

async function changeSong() {
  if (!result.value?.session_id || !result.value?.track) return;

  error.value = "";
  feedbackMessage.value = "";
  nextLoading.value = true;

  try {
    updatePlayDuration();
    result.value = await nextRecommendation(result.value.session_id, {
      current_song_id: result.value.track.song_id,
      play_duration_seconds: roundedDuration(),
      repeat_count: repeatCount.value,
    });
    resetPlayback();
  } catch (e) {
    error.value = e.message || "暂时没有更多候选歌曲。";
  } finally {
    nextLoading.value = false;
  }
}

async function sendFeedback() {
  if (!result.value?.session_id || !result.value?.track) return;

  error.value = "";
  feedbackMessage.value = "";
  feedbackLoading.value = true;

  try {
    updatePlayDuration();
    await submitFeedback({
      session_id: result.value.session_id,
      song_id: result.value.track.song_id,
      music_preference: Number(musicPreference.value),
      regulation_effect: Number(regulationEffect.value),
      play_duration_seconds: roundedDuration(),
      skipped: false,
      repeat_count: repeatCount.value,
    });
    feedbackMessage.value = "反馈已记录。";
  } catch (e) {
    error.value = e.message || "反馈提交失败。";
  } finally {
    feedbackLoading.value = false;
  }
}

function updatePlayDuration() {
  const audio = audioRef.value;
  if (!audio) return;
  playDuration.value = Math.max(playDuration.value, audio.currentTime || 0);
}

function roundedDuration() {
  return Number(playDuration.value.toFixed(1));
}

function resetPlayback() {
  playDuration.value = 0;
  repeatCount.value = 0;
  endedOnce.value = false;
}

function handlePlay() {
  if (endedOnce.value) {
    repeatCount.value += 1;
    endedOnce.value = false;
  }
}

function handleTimeUpdate() {
  updatePlayDuration();
}

function handleEnded() {
  updatePlayDuration();
  endedOnce.value = true;
}
</script>

<template>
  <main class="page">
    <header class="app-header">
      <h1><span class="title-icon">♪</span> MoodMusic · 情绪调节型音乐推荐</h1>
    </header>

    <div class="workspace">
      <section class="panel input-panel">
        <div class="panel-title">
          <h2><span class="icon">✎</span> 输入</h2>
        </div>

        <label>情绪文本</label>
        <textarea v-model="text" rows="7" placeholder="例如：我今天有点累，想听点安慰我的音乐"></textarea>

        <label>调节策略</label>
        <select v-model="strategy">
          <option v-for="item in strategies" :key="item.value" :value="item.value">
            {{ item.label }}
          </option>
        </select>

        <div class="strength-block">
          <label>调节强度：{{ Number(strength).toFixed(2) }} · {{ strengthLevel }}</label>
          <input v-model="strength" type="range" min="0" max="1" step="0.05" />
          <div class="strength-labels">
            <span>弱</span>
            <span>中</span>
            <span>强</span>
          </div>
        </div>

        <button class="primary-button" @click="submitRecommend" :disabled="loading">
          <span class="button-icon">▶</span>
          {{ loading ? "正在推荐..." : "开始推荐" }}
        </button>

        <p v-if="error" class="error">{{ error }}</p>
      </section>

      <section class="panel result-panel">
        <div class="panel-title">
          <h2><span class="icon">♫</span> 推荐音乐</h2>
          <span v-if="result" class="session-status">单曲推荐</span>
        </div>

        <div v-if="result" class="result-content">
          <article class="track">
            <div class="track-head">
              <div>
                <span class="eyebrow">当前歌曲</span>
                <h3>{{ result.track.song_id }}</h3>
              </div>
              <button class="secondary-button" @click="changeSong" :disabled="nextLoading || !result.has_next">
                <span class="button-icon">↻</span>
                {{ nextLoading ? "换歌中..." : result.has_next ? "不满意，换一首" : "没有更多候选" }}
              </button>
            </div>

            <p class="explanation">{{ result.explanation }}</p>

            <p class="tags">
              {{ Array.isArray(result.track.display_tags) ? result.track.display_tags.join(" · ") : result.track.display_tags }}
            </p>

            <audio
              v-if="result.track.audio_url"
              ref="audioRef"
              :key="result.track.song_id"
              :src="result.track.audio_url"
              controls
              @play="handlePlay"
              @timeupdate="handleTimeUpdate"
              @ended="handleEnded"
            ></audio>
            <p v-else class="error">这首歌缺少可播放地址。</p>
          </article>

          <form class="feedback" @submit.prevent="sendFeedback">
            <div class="feedback-head">
              <h3><span class="icon">✓</span> 反馈</h3>
              <p class="playback">已播放 {{ roundedDuration() }} 秒 · 重复播放 {{ repeatCount }} 次</p>
            </div>

            <div class="feedback-grid">
              <label>
                音乐偏好
                <select v-model="musicPreference">
                  <option :value="1">1 很不喜欢</option>
                  <option :value="2">2 不太喜欢</option>
                  <option :value="3">3 一般</option>
                  <option :value="4">4 喜欢</option>
                  <option :value="5">5 很喜欢</option>
                </select>
              </label>

              <label>
                调节效果
                <select v-model="regulationEffect">
                  <option :value="1">1 没有效果</option>
                  <option :value="2">2 效果较弱</option>
                  <option :value="3">3 一般</option>
                  <option :value="4">4 有帮助</option>
                  <option :value="5">5 很有帮助</option>
                </select>
              </label>
            </div>

            <button class="primary-button" type="submit" :disabled="feedbackLoading">
              <span class="button-icon">✓</span>
              {{ feedbackLoading ? "提交中..." : "提交反馈" }}
            </button>

            <p v-if="feedbackMessage" class="success">{{ feedbackMessage }}</p>
          </form>
        </div>

        <div v-else class="empty-state">
          <h3><span class="icon">♫</span> 等待推荐</h3>
        </div>
      </section>
    </div>
  </main>
</template>
