<script setup lang="ts">
import Icon from './Icon.vue'
const props = defineProps<{modelValue: string; busy: boolean; locked: boolean; error: string; notice?: string}>()
const emit = defineEmits<{ 'update:modelValue': [value: string]; submit: []; 'clear-error': []; stop: [] }>()
function keydown(e: KeyboardEvent) { if(e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); if(!props.busy && !props.locked && props.modelValue.trim()) emit('submit') } }
</script>
<template>
  <div class="composer-area">
    <div v-if="error" class="notice error" role="alert"><span>{{ error }}</span><button @click="emit('clear-error')" aria-label="关闭错误提示"><Icon name="close" /></button></div>
    <p v-if="notice" class="composer-notice" role="status">{{ notice }}</p>
    <form class="composer" @submit.prevent="emit('submit')">
      <label class="sr-only" for="question">你的问题</label>
      <textarea id="question" :value="modelValue" maxlength="1200" rows="2" placeholder="此刻，你想问些什么？" aria-describedby="question-help question-scope" :disabled="busy || locked" @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)" @keydown="keydown"></textarea>
      <div class="composer-footer">
        <span id="question-help" class="input-help"><kbd>Enter</kbd> 发送 · <kbd>Shift + Enter</kbd> 换行</span>
        <div class="send-group"><span v-if="modelValue.length" class="character-count">{{ modelValue.length }}/1200</span>
          <button v-if="busy" type="button" class="text-button" @click="emit('stop')">停止等待</button>
          <el-button v-else type="primary" native-type="submit" :disabled="!modelValue.trim() || locked">问一问<Icon name="arrow" :size="18" /></el-button>
        </div>
      </div>
    </form>
    <p id="question-scope" class="disclaimer">AI 解读附原文出处。每次独立回答，不读取之前的问答；追问时请写明背景。</p>
    <details class="question-guide"><summary>如何提问与核对回答</summary><p>可写明书名、篇章和你想理解的地方。点击回答中的引用编号核对原文；现代延伸解读不等同于孔子原话。资料不足时，可以换个问法或到典籍文库查找原文。</p></details>
  </div>
</template>
