<template>
  <div class="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 p-8">
    <div class="max-w-4xl mx-auto">
      <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-8">{{ $t('sidebar.communicate') }}</h1>
      
      <!-- Speech-to-Text Control Panel -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 mb-6">
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
              {{ $t('communicate.speechToText') }}
            </h2>
            <p class="text-gray-600 dark:text-gray-400">
              {{ $t('communicate.speechToTextDescription') }}
            </p>
          </div>
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <div :class="[
                'w-3 h-3 rounded-full',
                isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
              ]"></div>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                {{ isActive ? $t('communicate.active') : $t('communicate.inactive') }}
              </span>
            </div>
            <button
              @click="toggleSpeechToText"
              :disabled="isLoading"
              :class="[
                'px-6 py-3 rounded-lg font-semibold transition-all duration-200',
                isActive
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-primary-600 hover:bg-primary-700 text-white',
                isLoading ? 'opacity-50 cursor-not-allowed' : ''
              ]"
            >
              <span v-if="isLoading">{{ $t('communicate.loading') }}</span>
              <span v-else-if="isActive">{{ $t('communicate.stop') }}</span>
              <span v-else>{{ $t('communicate.start') }}</span>
            </button>
          </div>
        </div>
        
        <!-- Status Messages -->
        <div v-if="error" class="mb-4 p-4 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg">
          <p class="text-red-800 dark:text-red-200 text-sm">{{ error }}</p>
        </div>
        
        <div v-if="successMessage" class="mb-4 p-4 bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700 rounded-lg">
          <p class="text-green-800 dark:text-green-200 text-sm">{{ successMessage }}</p>
        </div>
      </div>
      
      <!-- Transcription Display -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          {{ $t('communicate.transcriptions') }}
        </h3>
        
        <!-- Speech Started Indicator -->
        <div v-if="isSpeaking" class="mb-4 p-4 bg-blue-100 dark:bg-blue-900/30 border border-blue-300 dark:border-blue-700 rounded-lg flex items-center space-x-3">
          <div class="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
          <span class="text-blue-800 dark:text-blue-200 font-medium">
            {{ $t('communicate.speaking') }}
          </span>
        </div>
        
        <!-- Transcriptions List -->
        <div v-if="transcriptions.length === 0" class="text-center py-12 text-gray-500 dark:text-gray-400">
          <p>{{ $t('communicate.noTranscriptions') }}</p>
        </div>
        
        <div v-else class="space-y-4">
          <div
            v-for="(transcription, index) in transcriptions"
            :key="index"
            class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600"
          >
            <div class="flex items-start justify-between">
              <p class="text-gray-900 dark:text-white flex-1">{{ transcription.text }}</p>
              <span class="text-xs text-gray-500 dark:text-gray-400 ml-4">
                {{ formatTime(transcription.timestamp) }}
              </span>
            </div>
          </div>
        </div>
        
        <!-- Clear Button -->
        <div v-if="transcriptions.length > 0" class="mt-6 flex justify-end">
          <button
            @click="clearTranscriptions"
            class="px-4 py-2 text-sm bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
          >
            {{ $t('communicate.clear') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';

const { t } = useI18n();

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

const isActive = ref(false);
const isLoading = ref(false);
const isSpeaking = ref(false);
const error = ref(null);
const successMessage = ref(null);
const transcriptions = ref([]);
let ws = null;
let successTimeout = null;

const connectWebSocket = () => {
  try {
    const wsUrl = `${WS_BASE_URL}/ws/speech-to-text`;
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('Speech-to-text WebSocket connected');
      error.value = null;
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'speech_started':
            isSpeaking.value = true;
            break;
          case 'transcription':
            isSpeaking.value = false;
            transcriptions.value.push({
              text: data.data.text,
              timestamp: new Date(data.timestamp)
            });
            // Auto-scroll to bottom (optional)
            setTimeout(() => {
              window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
            }, 100);
            break;
          case 'error':
            error.value = data.data.error;
            isSpeaking.value = false;
            break;
          case 'pong':
            // Keep-alive response
            break;
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };
    
    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      error.value = 'WebSocket connection error';
    };
    
    ws.onclose = () => {
      console.log('Speech-to-text WebSocket disconnected');
      // Attempt to reconnect if still active
      if (isActive.value) {
        setTimeout(connectWebSocket, 3000);
      }
    };
  } catch (err) {
    console.error('Failed to connect WebSocket:', err);
    error.value = 'Failed to connect to WebSocket';
  }
};

const disconnectWebSocket = () => {
  if (ws) {
    ws.close();
    ws = null;
  }
};

const loadStatus = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/speech-to-text/status`);
    isActive.value = response.data.is_active;
    if (isActive.value) {
      connectWebSocket();
    }
  } catch (err) {
    console.error('Error loading status:', err);
  }
};

const toggleSpeechToText = async () => {
  isLoading.value = true;
  error.value = null;
  successMessage.value = null;
  
  if (successTimeout) {
    clearTimeout(successTimeout);
  }
  
  try {
    if (isActive.value) {
      // Stop
      await axios.post(`${API_BASE_URL}/api/speech-to-text/stop`);
      isActive.value = false;
      disconnectWebSocket();
      successMessage.value = t('communicate.stopped');
    } else {
      // Start
      await axios.post(`${API_BASE_URL}/api/speech-to-text/start`);
      isActive.value = true;
      connectWebSocket();
      successMessage.value = t('communicate.started');
    }
    
    successTimeout = setTimeout(() => {
      successMessage.value = null;
    }, 3000);
  } catch (err) {
    console.error('Error toggling speech-to-text:', err);
    error.value = err.response?.data?.detail || t('communicate.error');
    isActive.value = false;
    disconnectWebSocket();
  } finally {
    isLoading.value = false;
  }
};

const clearTranscriptions = () => {
  transcriptions.value = [];
};

const formatTime = (date) => {
  return new Date(date).toLocaleTimeString();
};

onMounted(() => {
  loadStatus();
});

onBeforeUnmount(() => {
  disconnectWebSocket();
  if (successTimeout) {
    clearTimeout(successTimeout);
  }
});
</script>
