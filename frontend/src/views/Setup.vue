<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
          {{ $t('setup.title') }}
        </h1>
        <button
          v-if="!isEditMode"
          @click="enterEditMode"
          class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors flex items-center space-x-2"
        >
          <PencilIcon class="w-5 h-5" />
          <span>{{ $t('setup.edit') }}</span>
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
        <p class="text-red-800 dark:text-red-200">{{ error }}</p>
      </div>

      <!-- Success Message -->
      <div
        v-if="successMessage"
        class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-6"
      >
        <p class="text-green-800 dark:text-green-200">{{ successMessage }}</p>
      </div>

      <!-- Configuration Form -->
      <form v-else @submit.prevent="saveConfig" class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <TabGroup>
          <TabList class="flex items-center gap-2 border-b border-gray-200 dark:border-gray-700">
            <Tab v-slot="{ selected }">
              <button
                type="button"
                :class="[
                  'px-4 py-2 text-sm font-semibold transition-colors border-b-2',
                  selected
                    ? 'border-primary-600 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white',
                ]"
              >
                {{ $t('setup.aiSettings.title') }}
              </button>
            </Tab>
            <Tab v-slot="{ selected }">
              <button
                type="button"
                :class="[
                  'px-4 py-2 text-sm font-semibold transition-colors border-b-2',
                  selected
                    ? 'border-primary-600 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white',
                ]"
              >
                {{ $t('setup.eyeTracking.title') }}
              </button>
            </Tab>
            <Tab v-slot="{ selected }">
              <button
                type="button"
                :class="[
                  'px-4 py-2 text-sm font-semibold transition-colors border-b-2',
                  selected
                    ? 'border-primary-600 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white',
                ]"
              >
                {{ $t('setup.tts.title') }}
              </button>
            </Tab>
            <Tab v-slot="{ selected }">
              <button
                type="button"
                :class="[
                  'px-4 py-2 text-sm font-semibold transition-colors border-b-2',
                  selected
                    ? 'border-primary-600 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white',
                ]"
              >
                {{ $t('setup.keyboards.title') }}
              </button>
            </Tab>
          </TabList>

          <TabPanels class="pt-6 space-y-6">
            <TabPanel>
              <!-- AI Settings Section -->
              <div class="space-y-6">
                <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                  {{ $t('setup.aiSettings.title') }}
                </h2>

          <!-- AI Provider -->
          <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {{ $t('setup.provider') }}
          </label>
          <select
            v-model="config.provider"
            :disabled="!isEditMode"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="google">Google</option>
            <option value="azure">Azure</option>
          </select>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ $t('setup.providerDescription') }}
          </p>
        </div>

        <!-- Model -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {{ $t('setup.model') }}
          </label>
          <input
            v-model="config.model"
            type="text"
            :disabled="!isEditMode"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
            :placeholder="$t('setup.modelPlaceholder')"
          />
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ $t('setup.modelDescription') }}
          </p>
        </div>

        <!-- Temperature -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {{ $t('setup.temperature') }}: {{ config.temperature.toFixed(1) }}
          </label>
          <input
            v-model.number="config.temperature"
            type="range"
            min="0"
            max="2"
            step="0.1"
            :disabled="!isEditMode"
            class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none disabled:cursor-not-allowed"
            :class="isEditMode ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'"
          />
          <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
            <span>0.0</span>
            <span>1.0</span>
            <span>2.0</span>
          </div>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ $t('setup.temperatureDescription') }}
          </p>
        </div>

        <!-- Communicate Prompt -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {{ $t('setup.communicatePrompt') }}
          </label>
          <textarea
            v-model="config.communicate_prompt"
            rows="6"
            :disabled="!isEditMode"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
            :placeholder="$t('setup.communicatePromptPlaceholder')"
          />
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ $t('setup.communicatePromptDescription') }}
          </p>
        </div>

        <!-- Keyboard Prompt -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {{ $t('setup.keyboardPrompt') }}
          </label>
          <textarea
            v-model="config.keyboard_prompt"
            rows="4"
            :disabled="!isEditMode"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
            :placeholder="$t('setup.keyboardPromptPlaceholder')"
          />
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ $t('setup.keyboardPromptDescription') }}
          </p>
        </div>

        <!-- Keyboard Multiple Letters Prompt -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {{ $t('setup.keyboardMultipleLettersPrompt') }}
          </label>
          <textarea
            v-model="config.keyboard_multiple_letters_prompt"
            rows="4"
            :disabled="!isEditMode"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
            :placeholder="$t('setup.keyboardMultipleLettersPromptPlaceholder')"
          />
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ $t('setup.keyboardMultipleLettersPromptDescription') }}
          </p>
          </div>
              </div>
            </TabPanel>

            <TabPanel>
              <!-- Eye Tracking Configuration Section -->
              <div class="space-y-6">
                <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                  {{ $t('setup.eyeTracking.title') }}
                </h2>

          <!-- Eye Used -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('setup.eyeTracking.eyeUsed') }}
            </label>
            <select
              v-model="config.eye_tracking.eye_used"
              :disabled="!isEditMode"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
            >
              <option value="left">{{ $t('setup.eyeTracking.eyeLeft') }}</option>
              <option value="right">{{ $t('setup.eyeTracking.eyeRight') }}</option>
              <option value="both">{{ $t('setup.eyeTracking.eyeBoth') }}</option>
            </select>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {{ $t('setup.eyeTracking.eyeUsedDescription') }}
            </p>
          </div>

          <!-- Dwell Time -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('setup.eyeTracking.dwellTime') }}: {{ config.eye_tracking.dwell_time.toFixed(1) }} {{ $t('setup.eyeTracking.seconds') }}
            </label>
            <input
              v-model.number="config.eye_tracking.dwell_time"
              type="range"
              min="0.5"
              max="10.0"
              step="0.1"
              :disabled="!isEditMode"
              class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none disabled:cursor-not-allowed"
              :class="isEditMode ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'"
            />
            <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>0.5s</span>
              <span>2.0s</span>
              <span>10.0s</span>
            </div>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {{ $t('setup.eyeTracking.dwellTimeDescription') }}
            </p>
          </div>
              </div>
            </TabPanel>

            <TabPanel>
              <!-- TTS Configuration Section -->
              <div class="space-y-6">
                <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                  {{ $t('setup.tts.title') }}
                </h2>

          <!-- TTS Language -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('setup.tts.language') }}
            </label>
            <select
              v-model="config.tts_language"
              :disabled="!isEditMode"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
            >
              <option value="fr">Français (fr-FR)</option>
              <option value="en">English (en-US)</option>
              <option value="es">Español (es-ES)</option>
              <option value="de">Deutsch (de-DE)</option>
              <option value="it">Italiano (it-IT)</option>
            </select>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {{ $t('setup.tts.languageDescription') }}
            </p>
          </div>

          <!-- TTS Voice Name -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('setup.tts.voiceName') }}
            </label>
            <input
              v-model="config.tts_voice_name"
              type="text"
              :disabled="!isEditMode"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
              :placeholder="$t('setup.tts.voiceNamePlaceholder')"
            />
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {{ $t('setup.tts.voiceNameDescription') }}
            </p>
          </div>

          <!-- TTS Pitch -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('setup.tts.pitch') }}: {{ config.tts_pitch.toFixed(1) }} {{ $t('setup.tts.semitones') }}
            </label>
            <input
              v-model.number="config.tts_pitch"
              type="range"
              min="-20"
              max="20"
              step="0.1"
              :disabled="!isEditMode"
              class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none disabled:cursor-not-allowed"
              :class="isEditMode ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'"
            />
            <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>-20.0</span>
              <span>0.0</span>
              <span>20.0</span>
            </div>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {{ $t('setup.tts.pitchDescription') }}
            </p>
          </div>

          <!-- TTS Speaking Rate -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('setup.tts.speakingRate') }}: {{ config.tts_speaking_rate.toFixed(2) }}x
            </label>
            <input
              v-model.number="config.tts_speaking_rate"
              type="range"
              min="0.25"
              max="4.0"
              step="0.05"
              :disabled="!isEditMode"
              class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none disabled:cursor-not-allowed"
              :class="isEditMode ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'"
            />
            <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>0.25x</span>
              <span>1.0x</span>
              <span>4.0x</span>
            </div>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {{ $t('setup.tts.speakingRateDescription') }}
            </p>
          </div>
              </div>
            </TabPanel>
            <TabPanel>
              <div class="space-y-6">
                <div class="flex items-center justify-between">
                  <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                    {{ $t('setup.keyboards.title') }}
                  </h2>
                  <button
                    type="button"
                    :disabled="!isEditMode"
                    @click="resetKeyboardForm"
                    class="px-3 py-2 text-sm font-semibold rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {{ $t('setup.keyboards.new') }}
                  </button>
                </div>

                <div v-if="keyboardError" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                  <p class="text-red-800 dark:text-red-200">{{ keyboardError }}</p>
                </div>
                <div v-if="keyboardSuccess" class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                  <p class="text-green-800 dark:text-green-200">{{ keyboardSuccess }}</p>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">
                      {{ $t('setup.keyboards.list') }}
                    </h3>
                    <div v-if="keyboardLoading" class="text-sm text-gray-500 dark:text-gray-400">
                      {{ $t('setup.keyboards.loading') }}
                    </div>
                    <div v-else class="space-y-2">
                      <button
                        v-for="layout in keyboardLayouts"
                        :key="layout.id"
                        type="button"
                        @click="selectKeyboardLayout(layout)"
                        class="w-full text-left px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
                        :class="selectedKeyboardId === layout.id ? 'bg-primary-50 dark:bg-primary-900/30 border-primary-500' : ''"
                      >
                        <div class="flex items-center justify-between">
                          <div>
                            <p class="text-sm font-semibold text-gray-900 dark:text-white">{{ layout.name }}</p>
                            <p v-if="layout.description" class="text-xs text-gray-500 dark:text-gray-400">{{ layout.description }}</p>
                          </div>
                          <button
                            type="button"
                            :disabled="!isEditMode"
                            @click.stop="deleteKeyboardLayout(layout.id)"
                            class="text-xs text-red-600 hover:text-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {{ $t('setup.keyboards.delete') }}
                          </button>
                        </div>
                      </button>
                      <p v-if="keyboardLayouts.length === 0" class="text-sm text-gray-500 dark:text-gray-400">
                        {{ $t('setup.keyboards.empty') }}
                      </p>
                    </div>
                  </div>

                  <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-4">
                    <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200">
                      {{ selectedKeyboardId ? $t('setup.keyboards.edit') : $t('setup.keyboards.create') }}
                    </h3>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        {{ $t('setup.keyboards.name') }}
                      </label>
                      <input
                        v-model="keyboardForm.name"
                        type="text"
                        :disabled="!isEditMode"
                        class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
                      />
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        {{ $t('setup.keyboards.description') }}
                      </label>
                      <textarea
                        v-model="keyboardForm.description"
                        rows="2"
                        :disabled="!isEditMode"
                        class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
                      />
                    </div>
                    <div class="grid grid-cols-3 gap-3">
                      <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          {{ $t('setup.keyboards.rows') }}
                        </label>
                        <input
                          v-model.number="keyboardForm.rows"
                          type="number"
                          min="1"
                          :disabled="!isEditMode"
                          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
                        />
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          {{ $t('setup.keyboards.columns') }}
                        </label>
                        <input
                          v-model.number="keyboardForm.columns"
                          type="number"
                          min="1"
                          :disabled="!isEditMode"
                          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
                        />
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          {{ $t('setup.keyboards.predictive') }}
                        </label>
                        <input
                          v-model.number="keyboardForm.predictive_cells"
                          type="number"
                          min="0"
                          :disabled="!isEditMode"
                          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
                        />
                      </div>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        {{ $t('setup.keyboards.cells') }}
                      </label>
                      <div class="space-y-2">
                        <div
                          v-for="(row, rowIndex) in cellsMatrix"
                          :key="`row-${rowIndex}`"
                          class="grid gap-2"
                          :style="{ gridTemplateColumns: `repeat(${keyboardForm.columns}, minmax(0, 1fr))` }"
                        >
                          <input
                            v-for="(cell, colIndex) in row"
                            :key="`cell-${rowIndex}-${colIndex}`"
                            v-model="cellsMatrix[rowIndex][colIndex]"
                            type="text"
                            :disabled="!isEditMode"
                            class="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
                          />
                        </div>
                      </div>
                      <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {{ $t('setup.keyboards.cellsHelp') }}
                      </p>
                    </div>
                    <div class="flex items-center gap-3">
                      <button
                        type="button"
                        :disabled="!isEditMode || keyboardSaving"
                        @click="saveKeyboardLayout"
                        class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {{ selectedKeyboardId ? $t('setup.keyboards.update') : $t('setup.keyboards.create') }}
                      </button>
                      <button
                        v-if="selectedKeyboardId"
                        type="button"
                        :disabled="!isEditMode"
                        @click="resetKeyboardForm"
                        class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {{ $t('setup.keyboards.cancel') }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </TabPanel>
          </TabPanels>
        </TabGroup>

        <!-- Action Buttons (only shown in edit mode) -->
        <div v-if="isEditMode" class="flex space-x-3 pt-6 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            @click="cancelEdit"
            class="flex-1 px-6 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors font-medium"
          >
            {{ $t('setup.cancel') }}
          </button>
          <button
            type="submit"
            :disabled="saving"
            class="flex-1 px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50 font-medium"
          >
            {{ saving ? $t('setup.saving') : $t('setup.save') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/vue';
import { PencilIcon } from '@heroicons/vue/24/outline';
import { configAPI, keyboardLayoutsAPI } from '../services/api';
import type { KeyboardLayoutRead } from '../types/api';

const { t } = useI18n();

interface AppConfig {
  provider: string
  model: string
  temperature: number
  communicate_prompt: string
  keyboard_prompt: string
  keyboard_multiple_letters_prompt: string
  tts_language: string
  tts_voice_name: string
  tts_pitch: number
  tts_speaking_rate: number
  eye_tracking: {
    eye_used: string
    dwell_time: number
  }
}

const config = ref<AppConfig>({
  provider: 'openai',
  model: '',
  temperature: 0.7,
  communicate_prompt: '',
  keyboard_prompt: '',
  keyboard_multiple_letters_prompt: '',
  tts_language: 'fr',
  tts_voice_name: '',
  tts_pitch: 0.0,
  tts_speaking_rate: 1.0,
  eye_tracking: {
    eye_used: 'both',
    dwell_time: 2.0,
  },
});

const originalConfig = ref<AppConfig>({ ...config.value });
const isEditMode = ref(false);
const loading = ref(true);
const saving = ref(false);
const error = ref<string | null>(null);
const successMessage = ref<string | null>(null);

const keyboardLayouts = ref<KeyboardLayoutRead[]>([]);
const keyboardLoading = ref(false);
const keyboardSaving = ref(false);
const keyboardError = ref<string | null>(null);
const keyboardSuccess = ref<string | null>(null);
const selectedKeyboardId = ref<number | null>(null);
const keyboardForm = ref({
  name: '',
  description: '',
  rows: 3,
  columns: 3,
  predictive_cells: 0,
});
const cellsMatrix = ref<string[][]>([]);

const loadConfig = async () => {
  try {
    loading.value = true;
    error.value = null;
    successMessage.value = null;
    const data = (await configAPI.get()) as Partial<AppConfig> & {
      prompt?: string
      eye_tracking?: Partial<AppConfig['eye_tracking']>
    };
    const loadedConfig: AppConfig = {
      provider: data.provider || 'openai',
      model: data.model || '',
      temperature: data.temperature ?? 0.7,
      communicate_prompt: data.communicate_prompt || data.prompt || '', // Backward compatibility
      keyboard_prompt: data.keyboard_prompt || '',
      keyboard_multiple_letters_prompt: data.keyboard_multiple_letters_prompt || '',
      tts_language: data.tts_language || 'fr',
      tts_voice_name: data.tts_voice_name || '',
      tts_pitch: data.tts_pitch ?? 0.0,
      tts_speaking_rate: data.tts_speaking_rate ?? 1.0,
      eye_tracking: {
        eye_used: data.eye_tracking?.eye_used || 'both',
        dwell_time: data.eye_tracking?.dwell_time ?? 2.0,
      },
    };
    config.value = loadedConfig;
    originalConfig.value = { ...loadedConfig };
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('setup.loadError');
    console.error('Error loading config:', err);
  } finally {
    loading.value = false;
  }
};

const loadKeyboardLayouts = async () => {
  try {
    keyboardLoading.value = true;
    keyboardError.value = null;
    keyboardLayouts.value = await keyboardLayoutsAPI.list();
  } catch (err) {
    keyboardError.value = err instanceof Error ? err.message : t('setup.keyboards.loadError');
  } finally {
    keyboardLoading.value = false;
  }
};

const resetKeyboardForm = () => {
  selectedKeyboardId.value = null;
  keyboardForm.value = {
    name: '',
    description: '',
    rows: 3,
    columns: 3,
    predictive_cells: 0,
  };
  cellsMatrix.value = buildCellsMatrix(3, 3);
  keyboardError.value = null;
  keyboardSuccess.value = null;
};

const selectKeyboardLayout = (layout: KeyboardLayoutRead) => {
  selectedKeyboardId.value = layout.id;
  keyboardForm.value = {
    name: layout.name,
    description: layout.description || '',
    rows: layout.rows,
    columns: layout.columns,
    predictive_cells: layout.predictive_cells,
  };
  cellsMatrix.value = buildCellsMatrix(layout.rows, layout.columns, layout.cells || undefined);
  keyboardError.value = null;
  keyboardSuccess.value = null;
};

const saveKeyboardLayout = async () => {
  keyboardSaving.value = true;
  keyboardError.value = null;
  keyboardSuccess.value = null;
  try {
    const payload = {
      name: keyboardForm.value.name,
      description: keyboardForm.value.description || null,
      rows: keyboardForm.value.rows,
      columns: keyboardForm.value.columns,
      predictive_cells: keyboardForm.value.predictive_cells,
      cells: cellsMatrix.value,
    };

    if (selectedKeyboardId.value) {
      await keyboardLayoutsAPI.update(selectedKeyboardId.value, payload);
      keyboardSuccess.value = t('setup.keyboards.updated');
    } else {
      const created = await keyboardLayoutsAPI.create(payload);
      selectedKeyboardId.value = created.id;
      keyboardSuccess.value = t('setup.keyboards.created');
    }
    await loadKeyboardLayouts();
  } catch (err) {
    keyboardError.value = err instanceof Error ? err.message : t('setup.keyboards.saveError');
  } finally {
    keyboardSaving.value = false;
  }
};

const deleteKeyboardLayout = async (layoutId: number) => {
  try {
    keyboardError.value = null;
    keyboardSuccess.value = null;
    await keyboardLayoutsAPI.delete(layoutId);
    if (selectedKeyboardId.value === layoutId) {
      resetKeyboardForm();
    }
    await loadKeyboardLayouts();
    keyboardSuccess.value = t('setup.keyboards.deleted');
  } catch (err) {
    keyboardError.value = err instanceof Error ? err.message : t('setup.keyboards.deleteError');
  }
};

const buildCellsMatrix = (
  rows: number,
  columns: number,
  existing?: string[][],
): string[][] => {
  const result: string[][] = [];
  for (let r = 0; r < rows; r += 1) {
    const row: string[] = [];
    for (let c = 0; c < columns; c += 1) {
      row.push(existing?.[r]?.[c] ?? '');
    }
    result.push(row);
  }
  return result;
};

const resizeCellsMatrix = () => {
  const rows = Math.max(1, Number(keyboardForm.value.rows));
  const columns = Math.max(1, Number(keyboardForm.value.columns));
  cellsMatrix.value = buildCellsMatrix(rows, columns, cellsMatrix.value);
};

watch(
  () => [keyboardForm.value.rows, keyboardForm.value.columns],
  () => {
    resizeCellsMatrix();
  },
);

const enterEditMode = () => {
  // Store current config as original before editing
  originalConfig.value = { ...config.value };
  isEditMode.value = true;
};

const cancelEdit = () => {
  // Revert to original config
  config.value = { ...originalConfig.value };
  isEditMode.value = false;
  error.value = null;
  successMessage.value = null;
};

const saveConfig = async () => {
  try {
    saving.value = true;
    error.value = null;
    successMessage.value = null;
    
    // Validate temperature
    if (config.value.temperature < 0 || config.value.temperature > 2) {
      error.value = t('setup.temperatureRangeError');
      return;
    }
    
    // Validate TTS pitch
    if (config.value.tts_pitch < -20 || config.value.tts_pitch > 20) {
      error.value = t('setup.tts.pitchRangeError');
      return;
    }
    
    // Validate TTS speaking rate
    if (config.value.tts_speaking_rate < 0.25 || config.value.tts_speaking_rate > 4.0) {
      error.value = t('setup.tts.speakingRateRangeError');
      return;
    }
    
    // Validate eye tracking dwell time
    if (config.value.eye_tracking.dwell_time < 0.5 || config.value.eye_tracking.dwell_time > 10.0) {
      error.value = t('setup.eyeTracking.dwellTimeRangeError');
      return;
    }
    
    await configAPI.update(config.value);
    // Update original config to match saved config
    originalConfig.value = { ...config.value };
    successMessage.value = t('setup.saveSuccess');
    
    // Exit edit mode after successful save
    isEditMode.value = false;
    
    // Clear success message after 3 seconds
    setTimeout(() => {
      successMessage.value = null;
    }, 3000);
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || t('setup.saveError');
    console.error('Error saving config:', err);
  } finally {
    saving.value = false;
  }
};

onMounted(() => {
  loadConfig();
  loadKeyboardLayouts();
  resizeCellsMatrix();
});
</script>
