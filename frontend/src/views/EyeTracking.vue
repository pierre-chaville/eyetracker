<template>
  <div class="min-h-screen bg-gray-900 relative overflow-hidden">
    <!-- Header -->
    <header ref="headerElement" class="bg-gray-800 shadow-lg z-10 relative">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <router-link to="/" class="flex items-center space-x-3 hover:opacity-80 transition-opacity">
              <div class="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                <EyeIcon class="w-6 h-6 text-white" />
              </div>
              <h1 class="text-2xl font-bold text-white">Eye Tracker</h1>
            </router-link>
          </div>
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <div :class="[
                'w-3 h-3 rounded-full',
                isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
              ]"></div>
              <span class="text-sm font-medium text-gray-300">
                {{ isConnected ? 'Connected' : 'Disconnected' }}
              </span>
            </div>
            <button
              @click="toggleConnection"
              :class="[
                'px-4 py-2 rounded-lg font-medium transition-colors',
                isConnected
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              ]"
            >
              {{ isConnected ? 'Disconnect' : 'Connect' }}
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Eye Tracking Canvas Area -->
    <div 
      class="relative w-full h-[calc(100vh-80px)] cursor-pointer" 
      ref="trackingArea"
      @click="toggleFreeze"
    >
      <!-- Freeze indicator -->
      <div v-if="isFrozen" class="absolute top-4 left-1/2 -translate-x-1/2 z-50 bg-yellow-500/90 backdrop-blur-sm text-black text-sm font-bold px-4 py-2 rounded-lg shadow-lg border-2 border-yellow-400">
        ⏸ FROZEN - Click to resume
      </div>

      <!-- Gaze Point Circle with Coordinates (use frozen data if frozen) -->
      <div
        v-if="(isFrozen ? frozenGazePoint : gazePoint) && isConnected && (isFrozen ? frozenTrackingData : trackingData)?.valid"
        :style="{
          left: `${(isFrozen ? frozenGazePoint : gazePoint).x}px`,
          top: `${(isFrozen ? frozenGazePoint : gazePoint).y}px`,
        }"
        class="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-none transition-all duration-75 ease-linear"
        :class="{ 'transition-none': isFrozen }"
      >
        <!-- Coordinate Label -->
        <div class="absolute top-10 left-1/2 -translate-x-1/2 whitespace-nowrap bg-gray-900/90 backdrop-blur-sm text-white text-xs font-mono px-2 py-1 rounded shadow-lg border border-gray-700">
          <div class="text-center">
            <div v-if="isFrozen" class="text-yellow-400 text-[10px] mb-1">FROZEN</div>
            <div>X: {{ (isFrozen ? frozenGazePoint : gazePoint).x.toFixed(1) }}px</div>
            <div>Y: {{ (isFrozen ? frozenGazePoint : gazePoint).y.toFixed(1) }}px</div>
            <div v-if="(isFrozen ? frozenTrackingData : trackingData)" class="text-gray-400 text-[10px] mt-1 pt-1 border-t border-gray-700">
              <div>Screen: {{ ((isFrozen ? frozenTrackingData : trackingData).pixelX?.toFixed(0) || '--') }}, {{ ((isFrozen ? frozenTrackingData : trackingData).pixelY?.toFixed(0) || '--') }}</div>
              <div>Norm: {{ (((isFrozen ? frozenTrackingData : trackingData).x * 100).toFixed(1)) }}%, {{ (((isFrozen ? frozenTrackingData : trackingData).y * 100).toFixed(1)) }}%</div>
            </div>
          </div>
        </div>
        <!-- Circle -->
        <div class="w-8 h-8" :class="{ 'animate-pulse': !isFrozen }">
          <div class="w-full h-full rounded-full bg-primary-500 border-4 border-primary-300 shadow-lg shadow-primary-500/50" :class="{ 'animate-pulse': !isFrozen }"></div>
          <div v-if="!isFrozen" class="absolute inset-0 rounded-full bg-primary-400 opacity-50 animate-ping"></div>
        </div>
      </div>

      <!-- Invalid gaze indicator with coordinates -->
      <div
        v-if="(isFrozen ? frozenGazePoint : gazePoint) && isConnected && (isFrozen ? frozenTrackingData : trackingData) && !(isFrozen ? frozenTrackingData : trackingData).valid"
        :style="{
          left: `${(isFrozen ? frozenGazePoint : gazePoint).x}px`,
          top: `${(isFrozen ? frozenGazePoint : gazePoint).y}px`,
        }"
        class="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-none transition-all duration-75 ease-linear"
        :class="{ 'transition-none': isFrozen }"
      >
        <!-- Coordinate Label -->
        <div class="absolute top-8 left-1/2 -translate-x-1/2 whitespace-nowrap bg-red-900/90 backdrop-blur-sm text-white text-xs font-mono px-2 py-1 rounded shadow-lg border border-red-700">
          <div class="text-center">
            <div class="text-red-300">INVALID</div>
            <div v-if="isFrozen" class="text-yellow-400 text-[10px]">FROZEN</div>
            <div>X: {{ (isFrozen ? frozenGazePoint : gazePoint).x.toFixed(1) }}px</div>
            <div>Y: {{ (isFrozen ? frozenGazePoint : gazePoint).y.toFixed(1) }}px</div>
          </div>
        </div>
        <!-- Circle -->
        <div class="w-6 h-6">
          <div class="w-full h-full rounded-full bg-red-500 border-2 border-red-300 opacity-50"></div>
        </div>
      </div>

      <!-- Crosshair at center (for reference) -->
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none opacity-20">
        <div class="w-px h-20 bg-white"></div>
        <div class="w-20 h-px bg-white -mt-px -ml-10"></div>
      </div>

      <!-- Status Overlay -->
      <div v-if="!isConnected" class="absolute inset-0 flex items-center justify-center">
        <div class="text-center">
          <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-800 flex items-center justify-center">
            <EyeIcon class="w-8 h-8 text-gray-500" />
          </div>
          <h2 class="text-2xl font-semibold text-gray-300 mb-2">Not Connected</h2>
          <p class="text-gray-400 mb-6">Click "Connect" to start receiving eye tracking data</p>
          <button
            @click="toggleConnection"
            class="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors"
          >
            Connect to WebSocket
          </button>
        </div>
      </div>
    </div>

    <!-- Info Panel -->
    <div class="absolute bottom-4 left-4 bg-gray-800/90 backdrop-blur-sm rounded-lg p-4 shadow-xl max-w-xs">
      <h3 class="text-sm font-semibold text-gray-300 mb-2">Eye Tracking Data</h3>
      <div class="space-y-1 text-xs font-mono">
        <div class="text-gray-400">
          <span class="text-gray-500">Status:</span>
          <span :class="[
            'ml-2 font-semibold',
            trackingData?.valid ? 'text-green-400' : 'text-red-400'
          ]">
            {{ trackingData?.valid ? 'Valid' : 'Invalid' }}
          </span>
        </div>
        <div class="text-gray-400">
          <span class="text-gray-500">X:</span>
          <span class="text-white ml-2">{{ gazePoint ? gazePoint.x.toFixed(1) : '--' }}px</span>
          <span v-if="trackingData" class="text-gray-500 ml-1">
            ({{ (trackingData.x * 100).toFixed(1) }}%)
          </span>
        </div>
        <div v-if="trackingData?.pixelX !== undefined" class="text-gray-400 text-[10px]">
          <span class="text-gray-500">Screen X:</span>
          <span class="text-white ml-2">{{ trackingData.pixelX.toFixed(1) }}px</span>
        </div>
        <div class="text-gray-400">
          <span class="text-gray-500">Y:</span>
          <span class="text-white ml-2">{{ gazePoint ? gazePoint.y.toFixed(1) : '--' }}px</span>
          <span v-if="trackingData" class="text-gray-500 ml-1">
            ({{ (trackingData.y * 100).toFixed(1) }}%)
          </span>
        </div>
        <div v-if="trackingData?.pixelY !== undefined" class="text-gray-400 text-[10px]">
          <span class="text-gray-500">Screen Y:</span>
          <span class="text-white ml-2">{{ trackingData.pixelY.toFixed(1) }}px</span>
        </div>
        <div v-if="trackingData" class="text-gray-400">
          <span class="text-gray-500">Screen:</span>
          <span class="text-white ml-2">{{ trackingData.screenWidth }}×{{ trackingData.screenHeight }}</span>
        </div>
        <div class="text-gray-400">
          <span class="text-gray-500">FPS:</span>
          <span class="text-white ml-2">{{ fps.toFixed(1) }}</span>
        </div>
        <div class="text-gray-400">
          <span class="text-gray-500">Messages:</span>
          <span class="text-white ml-2">{{ messageCount }}</span>
        </div>
        <div class="text-gray-400 pt-2 border-t border-gray-700 mt-2">
          <span class="text-gray-500">Window Offset:</span>
          <span class="text-white ml-2">{{ windowOffset.x }}, {{ windowOffset.y }}</span>
        </div>
        <div v-if="manualOffset.x !== 0 || manualOffset.y !== 0" class="text-gray-400">
          <span class="text-gray-500">Manual Offset:</span>
          <span class="text-yellow-400 ml-2">{{ manualOffset.x }}, {{ manualOffset.y }}</span>
        </div>
        <div class="text-gray-400">
          <span class="text-gray-500">Scale Factor:</span>
          <span class="text-white ml-2">{{ scaleFactor.toFixed(2) }}x</span>
        </div>
        <div class="text-gray-400">
          <span class="text-gray-500">Scale Applied:</span>
          <span :class="[
            'ml-2 font-semibold',
            applyScaling ? 'text-green-400' : 'text-gray-500'
          ]">
            {{ applyScaling ? scaleMode : 'None' }}
          </span>
        </div>
        <div class="text-gray-400">
          <span class="text-gray-500">Header Height:</span>
          <span class="text-white ml-2">
            {{ (manualHeaderHeight !== null && manualHeaderHeight > 0 ? manualHeaderHeight : headerHeight).toFixed(0) }}px
          </span>
          <span v-if="manualHeaderHeight !== null && manualHeaderHeight > 0" class="text-yellow-400 text-[10px] ml-1">(manual)</span>
        </div>
      </div>
    </div>

    <!-- Connection Settings -->
    <div class="absolute bottom-4 right-4 bg-gray-800/90 backdrop-blur-sm rounded-lg p-4 shadow-xl max-w-xs">
      <h3 class="text-sm font-semibold text-gray-300 mb-2">Connection Settings</h3>
      <div class="space-y-2">
        <div>
          <label class="block text-xs text-gray-400 mb-1">WebSocket URL</label>
          <input
            v-model="wsUrl"
            type="text"
            :disabled="isConnected"
            class="w-full px-3 py-2 bg-gray-700 text-white rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
            placeholder="ws://127.0.0.1:8765"
          />
        </div>
        <div class="pt-2 border-t border-gray-700">
          <label class="block text-xs text-gray-400 mb-1">Manual Offset (X, Y)</label>
          <div class="flex gap-2">
            <input
              v-model.number="manualOffset.x"
              type="number"
              step="1"
              class="w-full px-2 py-1 bg-gray-700 text-white rounded text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="X"
            />
            <input
              v-model.number="manualOffset.y"
              type="number"
              step="1"
              class="w-full px-2 py-1 bg-gray-700 text-white rounded text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Y"
            />
          </div>
          <button
            @click="updateWindowPosition"
            class="mt-2 w-full px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-xs transition-colors"
          >
            Refresh Position
          </button>
          <label class="flex items-center mt-2 cursor-pointer">
            <input
              v-model="invertY"
              type="checkbox"
              class="mr-2"
            />
            <span class="text-xs text-gray-400">Invert Y Axis</span>
          </label>
          <label class="flex items-center mt-2 cursor-pointer">
            <input
              v-model="applyScaling"
              type="checkbox"
              class="mr-2"
            />
            <span class="text-xs text-gray-400">Apply Scale Correction</span>
          </label>
          <div v-if="applyScaling" class="mt-2 space-y-2">
            <div>
              <label class="block text-xs text-gray-400 mb-1">Scale Mode</label>
              <select
                v-model="scaleMode"
                class="w-full px-2 py-1 bg-gray-700 text-white rounded text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="none">None (use directly)</option>
                <option value="divide">Divide by scale</option>
                <option value="multiply">Multiply by scale</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-gray-400 mb-1">Scale Factor (override detected: {{ scaleFactor.toFixed(2) }})</label>
              <input
                v-model.number="manualScaleFactor"
                type="number"
                step="0.1"
                min="0.5"
                max="3.0"
                class="w-full px-2 py-1 bg-gray-700 text-white rounded text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Auto"
              />
            </div>
            <div>
              <label class="block text-xs text-gray-400 mb-1">Header Height (measured: {{ headerHeight.toFixed(0) }}px)</label>
              <input
                v-model.number="manualHeaderHeight"
                type="number"
                step="1"
                min="0"
                max="200"
                class="w-full px-2 py-1 bg-gray-700 text-white rounded text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Auto"
              />
            </div>
          </div>
        </div>
        <div v-if="error" class="mt-2 p-2 bg-red-900/50 border border-red-700 rounded text-xs text-red-300">
          {{ error }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { EyeIcon } from '@heroicons/vue/24/outline';

const wsUrl = ref('ws://127.0.0.1:8765');
const isConnected = ref(false);
const gazePoint = ref(null);
const trackingData = ref(null);
const messageCount = ref(0);
const error = ref(null);
const ws = ref(null);
const trackingArea = ref(null);
const fps = ref(0);
const windowOffset = ref({ x: 0, y: 0 });
const manualOffset = ref({ x: 0, y: 0 });
const invertY = ref(false); // Option to invert Y axis if coordinate system is flipped
const scaleFactor = ref(1.0); // Display scale factor (e.g., 1.5 for 150% scaling)
const manualScaleFactor = ref(null); // Manual override for scale factor
const applyScaling = ref(true); // Toggle to apply/remove scaling correction (default true since divide works)
const scaleMode = ref('divide'); // 'divide', 'multiply', or 'none'
const headerHeight = ref(80); // Height of the header in pixels (will be measured dynamically)
const manualHeaderHeight = ref(null); // Manual override for header height adjustment
const isFrozen = ref(false); // Freeze the display to read coordinates
const frozenGazePoint = ref(null); // Store frozen position
const frozenTrackingData = ref(null); // Store frozen tracking data
const headerElement = ref(null); // Reference to header element
let positionInterval = null;
let resizeObserver = null;
let resizeHandler = null;

// FPS calculation
const frameTimes = ref([]);
const updateFPS = () => {
  const now = performance.now();
  frameTimes.value.push(now);
  if (frameTimes.value.length > 60) {
    frameTimes.value.shift();
  }
  if (frameTimes.value.length > 1) {
    const elapsed = frameTimes.value[frameTimes.value.length - 1] - frameTimes.value[0];
    fps.value = ((frameTimes.value.length - 1) / elapsed) * 1000;
  }
};

const connectWebSocket = () => {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    return;
  }

  try {
    error.value = null;
    ws.value = new WebSocket(wsUrl.value);

    ws.value.onopen = () => {
      isConnected.value = true;
      error.value = null;
      console.log('WebSocket connected');
    };

    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Store the full tracking data (only update if not frozen)
        if (!isFrozen.value) {
          trackingData.value = data;
        }
        
        // Handle the coordinate data - prefer pixelX/pixelY if available, otherwise use normalized coordinates
        let screenX, screenY;
        
        if (data.pixelX !== undefined && data.pixelY !== undefined) {
          // Use pixel coordinates directly (these are physical pixels from eye tracker)
          screenX = data.pixelX;
          screenY = data.pixelY;
        } else if (data.x !== undefined && data.y !== undefined && data.screenWidth && data.screenHeight) {
          // Convert normalized coordinates (0-1) to screen pixels
          screenX = data.x * data.screenWidth;
          screenY = data.y * data.screenHeight;
        } else {
          // Invalid data format
          return;
        }
        
        // Convert screen coordinates to window coordinates
        // Screen coordinates are absolute to the entire screen
        // Window coordinates are relative to the window
        // Note: Electron window positions are in logical pixels (already scaled)
        
        // Apply scaling correction if enabled
        // The eye tracker might send physical pixels that need conversion to logical pixels
        let logicalX = screenX;
        let logicalY = screenY;
        
        // Apply scaling if checkbox is checked (apply regardless of scaleFactor value to allow testing)
        if (applyScaling.value) {
          // Use manual scale factor if provided, otherwise use detected scale factor
          const effectiveScaleFactor = manualScaleFactor.value !== null && manualScaleFactor.value > 0
            ? manualScaleFactor.value
            : scaleFactor.value;
          
          if (scaleMode.value === 'divide') {
            // Convert physical pixels to logical pixels by dividing by scale factor
            logicalX = screenX / effectiveScaleFactor;
            logicalY = screenY / effectiveScaleFactor;
          } else if (scaleMode.value === 'multiply') {
            // Try multiplying instead (if tracker sends logical and we need physical)
            logicalX = screenX * effectiveScaleFactor;
            logicalY = screenY * effectiveScaleFactor;
          }
          // 'none' means use coordinates directly (no change)
        }
        
        // Apply both detected window offset and manual offset adjustment
        // Window offsets from Electron are already in logical pixels
        // Only scale manual offset if scaling is enabled
        let totalOffsetX = windowOffset.value.x + manualOffset.value.x;
        let totalOffsetY = windowOffset.value.y + manualOffset.value.y;
        
        if (applyScaling.value && scaleFactor.value !== 1.0) {
          // If we scaled the coordinates, we might need to scale offsets too
          // But Electron positions are already logical, so don't scale windowOffset
          // Only scale manual offset if user entered it in physical pixels
        }
        
        // Handle Y axis inversion if needed (some coordinate systems have Y=0 at bottom)
        let adjustedLogicalY = logicalY;
        if (invertY.value && data.screenHeight) {
          // Use screenHeight directly if not scaling, otherwise adjust for scale
          const screenHeightLogical = applyScaling.value && scaleFactor.value !== 1.0 
            ? data.screenHeight / scaleFactor.value 
            : data.screenHeight;
          adjustedLogicalY = screenHeightLogical - logicalY;
        }
        
        // Calculate effective header height
        // When scaling is applied (divide mode), the header height measurement might need adjustment
        // because the measurement is in logical pixels but the coordinate conversion might affect it
        let effectiveHeaderHeight = manualHeaderHeight.value !== null && manualHeaderHeight.value > 0
          ? manualHeaderHeight.value
          : headerHeight.value;
        
        // If scaling is applied in divide mode, we might need to scale the header height
        // The user found that measured 72px needs to be ~150px (about 2x) when scale factor is 1.5
        // This suggests the header height should be multiplied by scale factor when dividing coordinates
        if (applyScaling.value && scaleMode.value === 'divide') {
          const effectiveScaleFactor = manualScaleFactor.value !== null && manualScaleFactor.value > 0
            ? manualScaleFactor.value
            : scaleFactor.value;
          
          // Only auto-adjust if manual header height is not set
          if (manualHeaderHeight.value === null || manualHeaderHeight.value === 0) {
            // User testing showed: 72px measured → 150px needed (≈2.08x) with scale factor 1.5
            // Using scaleFactor^2 gives: 72 * 2.25 = 162px (close approximation)
            // This accounts for the coordinate conversion affecting header height calculation
            effectiveHeaderHeight = headerHeight.value * effectiveScaleFactor * effectiveScaleFactor;
          }
        }
        
        // If we're applying scaling and converting from physical to logical,
        // the header height measurement (from getBoundingClientRect) is already in logical pixels,
        // so we use it directly. But we might need a small adjustment.
        // Note: getBoundingClientRect() returns CSS pixels (logical), so no conversion needed
        
        const windowX = logicalX - totalOffsetX;
        const windowY = adjustedLogicalY - totalOffsetY - effectiveHeaderHeight;
        
        // Ensure coordinates are within bounds
        const x = Math.max(0, Math.min(window.innerWidth, windowX));
        const y = Math.max(0, Math.min(window.innerHeight - effectiveHeaderHeight, windowY));
        
        // Debug logging to help diagnose the issue
        if (messageCount.value % 60 === 0) { // Log every 60th message to avoid spam
          console.log('Coordinate calculation:', {
            screenX, screenY,
            logicalX, logicalY,
            totalOffsetX, totalOffsetY,
            windowX, windowY,
            finalX: x, finalY: y,
            scaleFactor: scaleFactor.value,
            manualScaleFactor: manualScaleFactor.value,
            effectiveScaleFactor: manualScaleFactor.value !== null && manualScaleFactor.value > 0
              ? manualScaleFactor.value
              : scaleFactor.value,
            applyScaling: applyScaling.value,
            scaleMode: scaleMode.value,
            headerHeight: headerHeight.value,
            effectiveHeaderHeight: manualHeaderHeight.value !== null && manualHeaderHeight.value > 0
              ? manualHeaderHeight.value
              : headerHeight.value
          });
        }
        
        // Only update gaze point if not frozen
        if (!isFrozen.value) {
          gazePoint.value = { x, y };
        }
        messageCount.value++;
        updateFPS();
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
        error.value = 'Invalid message format';
      }
    };

    ws.value.onerror = (err) => {
      console.error('WebSocket error:', err);
      error.value = 'Connection error. Make sure the C# app is running.';
      isConnected.value = false;
    };

    ws.value.onclose = () => {
      isConnected.value = false;
      gazePoint.value = null;
      console.log('WebSocket disconnected');
    };
  } catch (err) {
    error.value = 'Failed to connect. Check the WebSocket URL.';
    console.error('WebSocket connection error:', err);
  }
};

const disconnectWebSocket = () => {
  if (ws.value) {
    ws.value.close();
    ws.value = null;
  }
  isConnected.value = false;
  gazePoint.value = null;
  trackingData.value = null;
};

const toggleConnection = () => {
  if (isConnected.value) {
    disconnectWebSocket();
  } else {
    connectWebSocket();
  }
};

const toggleFreeze = () => {
  if (isFrozen.value) {
    // Unfreeze - resume tracking
    isFrozen.value = false;
    frozenGazePoint.value = null;
    frozenTrackingData.value = null;
  } else {
    // Freeze - capture current position
    if (gazePoint.value && trackingData.value) {
      frozenGazePoint.value = { ...gazePoint.value };
      frozenTrackingData.value = { ...trackingData.value };
      isFrozen.value = true;
    }
  }
};

const updateWindowPosition = async () => {
  if (window.electronAPI) {
    try {
      const position = await window.electronAPI.getWindowPosition();
      windowOffset.value = { x: position.x, y: position.y };
      console.log('Window position from Electron:', position);
      console.log('Window offset set to:', windowOffset.value);
      
      // Get display scale factor
      try {
        const scale = await window.electronAPI.getDisplayScaleFactor();
        scaleFactor.value = scale;
        console.log('Display scale factor from Electron:', scaleFactor.value);
        
        // If scale factor is 1.0, try devicePixelRatio as fallback
        if (scaleFactor.value === 1.0 && window.devicePixelRatio && window.devicePixelRatio !== 1.0) {
          console.log('Scale factor was 1.0, trying devicePixelRatio:', window.devicePixelRatio);
          scaleFactor.value = window.devicePixelRatio;
        }
      } catch (err) {
        console.error('Error getting scale factor:', err);
        // Fallback to devicePixelRatio
        scaleFactor.value = window.devicePixelRatio || 1.0;
        console.log('Using devicePixelRatio fallback:', scaleFactor.value);
      }
    } catch (err) {
      console.error('Error getting window position:', err);
      // Keep existing offset or use 0,0
    }
  } else {
    // Fallback for browser/development: try to use window.screenX/screenY
    if (window.screenX !== undefined && window.screenY !== undefined) {
      windowOffset.value = { x: window.screenX, y: window.screenY };
      console.log('Using browser window position:', windowOffset.value);
    } else {
      windowOffset.value = { x: 0, y: 0 };
      console.log('No window position available, using 0,0');
    }
    // Use devicePixelRatio as scale factor fallback
    scaleFactor.value = window.devicePixelRatio || 1.0;
    console.log('Using devicePixelRatio as scale factor:', scaleFactor.value);
  }
};

const updateHeaderHeight = () => {
  if (headerElement.value) {
    const rect = headerElement.value.getBoundingClientRect();
    headerHeight.value = rect.height;
    console.log('Header height measured:', headerHeight.value);
  }
};

onMounted(() => {
  // Wait for next tick to ensure header element is rendered
  setTimeout(() => {
    // Measure header height
    updateHeaderHeight();
    
    // Use ResizeObserver to watch for header size changes
    if (headerElement.value && window.ResizeObserver) {
      resizeObserver = new ResizeObserver(() => {
        updateHeaderHeight();
      });
      resizeObserver.observe(headerElement.value);
    }
  }, 0);
  
  // Get initial window position
  updateWindowPosition();
  
  // Update window position periodically (in case window is moved)
  positionInterval = setInterval(() => {
    updateWindowPosition();
    updateHeaderHeight(); // Also update header height in case it changes
  }, 1000);
  
  // Also update on window resize/move events
  resizeHandler = () => {
    updateWindowPosition();
    updateHeaderHeight();
  };
  window.addEventListener('resize', resizeHandler);
});

onBeforeUnmount(() => {
  disconnectWebSocket();
  if (positionInterval) {
    clearInterval(positionInterval);
  }
  if (resizeObserver && headerElement.value) {
    resizeObserver.unobserve(headerElement.value);
    resizeObserver.disconnect();
  }
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler);
  }
});
</script>

<style scoped>
/* Smooth transitions for the gaze point */
</style>

