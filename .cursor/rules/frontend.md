---
description: Rules for frontend code (Vue.js, Tailwind CSS, Headless UI, Electron renderer)
globs: frontend/**/*.{vue,ts,js,css}
alwaysApply: false
---

# Frontend — Vue.js Eyetracking App (Electron Renderer)

## Stack
- **Framework**: Vue 3 (Composition API only)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS 3
- **UI Components**: Headless UI for Vue
- **State Management**: Pinia
- **Real-time**: WebSockets — eye-tracking events (~30Hz from Tobii/Electron), STT events (from FastAPI backend)
- **Build**: Vite
- **Runtime**: Electron renderer process
- **Communication**: IPC via preload bridge to Electron main process

## Project Structure

```
frontend/
├── src/
│   ├── main.ts                  # App entry, plugin registration
│   ├── App.vue                  # Root component
│   ├── components/              # Reusable UI components
│   │   ├── common/              # Generic (buttons, inputs, modals, loaders)
│   │   ├── tracking/            # Eye-tracking specific (gaze overlay, calibration)
│   │   ├── communication/       # AAC board, word prediction, message composer
│   │   └── settings/            # Configuration panels
│   ├── views/                   # Page-level components (one per route)
│   │   ├── HomeView.vue
│   │   ├── TrackingView.vue
│   │   ├── SettingsView.vue
│   │   └── ...
│   ├── composables/             # Shared logic (useGaze, useSpeech, useApi...)
│   │   ├── useGaze.ts           # Gaze data from eye-tracker WS (~30Hz), smoothing, fixation
│   │   ├── useWebSocket.ts      # Generic WS connection with auto-reconnect
│   │   ├── useSTTEvents.ts      # Subscribe to STT event stream from backend WS
│   │   ├── useSpeech.ts
│   │   ├── useApi.ts
│   │   ├── useDwell.ts          # Dwell-click timing logic
│   │   └── ...
│   ├── stores/                  # Pinia stores
│   │   ├── tracking.ts
│   │   ├── user.ts
│   │   ├── settings.ts
│   │   └── ...
│   ├── services/                # API client layer (calls to FastAPI backend)
│   │   ├── api.ts               # Axios/fetch instance, interceptors
│   │   ├── ws.ts                # WebSocket client, reconnect logic, message typing
│   │   ├── tracking.ts
│   │   ├── tts.ts
│   │   ├── stt.ts
│   │   └── ...
│   ├── types/                   # TypeScript type definitions
│   │   ├── tracking.ts
│   │   ├── api.ts
│   │   ├── ws.ts                # WebSocket message types (mirrors backend schemas)
│   │   ├── electron.d.ts        # Preload API types
│   │   └── ...
│   ├── utils/                   # Helpers, constants, enums
│   │   ├── constants.ts
│   │   └── ...
│   ├── assets/                  # Static assets (icons, images, sounds)
│   ├── styles/                  # Global Tailwind config and base styles
│   │   └── main.css             # @tailwind directives, custom utilities
│   └── router/
│       └── index.ts             # Vue Router config
├── index.html
├── tailwind.config.ts
├── tsconfig.json
└── vite.config.ts
```

## Architecture Rules

### Component Architecture
- **Views** → page-level, correspond 1:1 with routes. Compose layout from smaller components. Minimal logic.
- **Components** → reusable, single-responsibility UI pieces. Accept props, emit events. No direct API calls.
- **Composables** → shared reactive logic. Encapsulate state + behavior. Return refs and functions.
- **Stores** → global application state (Pinia). Cross-component shared state only.
- **Services** → API client functions. Handle HTTP calls and response mapping. No Vue reactivity.

### Data Flow
```
REST API (FastAPI)           ←→  Services  ←→  Stores  ←→  Components  ←→  User
WS: Eye tracker (~30Hz)      →  useGaze composable       →  Components
WS: STT events (FastAPI)     →  useSTTEvents composable   →  Components / Stores
Electron IPC                 ←→  Composables              →  Components
```
- Components never call services or WebSocket directly — go through stores or composables.
- Stores call services for REST data fetching and mutations.
- Two separate WebSocket connections with different sources:
  - **Gaze WS**: eye-tracker data at ~30Hz via Tobii SDK / Electron native layer. Flows through `useGaze` composable. Not routed through the backend.
  - **STT WS**: speech-to-text events pushed by the FastAPI backend (`/ws/stt`). Flows through `useSTTEvents` composable.
- Composables use stores when they need shared state, or services for scoped data.

## Coding Standards

### Vue Components
- **Always** use `<script setup lang="ts">` syntax. No Options API. No `defineComponent()`.
- **Always** use `<template>` → `<script setup>` → `<style>` order in SFCs.
- Use `defineProps<T>()` and `defineEmits<T>()` with TypeScript type declarations (no runtime props).
- Use `defineModel()` for v-model bindings.
- Default slot content is fine. Use named slots for complex layouts.
- One component per file. File name = component name in PascalCase.

```vue
<template>
  <div class="flex items-center gap-2">
    <span class="text-sm text-gray-600">{{ label }}</span>
    <slot />
  </div>
</template>

<script setup lang="ts">
interface Props {
  label: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
})

const emit = defineEmits<{
  click: [id: string]
}>()
</script>
```

### TypeScript
- Strict mode enabled (`strict: true` in tsconfig).
- No `any` — use `unknown` and narrow with type guards when type is truly unknown.
- Define explicit interfaces for all props, emits, API responses, and store state.
- Use discriminated unions for state machines (tracking status, connection state, etc.).
- Prefer `interface` for object shapes, `type` for unions and utility types.
- Export types from `types/` directory, co-locate private types in their module.

```typescript
// Discriminated union for tracking state
type TrackingState =
  | { status: 'idle' }
  | { status: 'calibrating'; progress: number }
  | { status: 'active'; gazePoint: GazePoint }
  | { status: 'error'; message: string }
```

### Tailwind CSS
- **All styling via Tailwind utility classes.** No `<style scoped>` blocks unless absolutely necessary.
- No inline `style=""` attributes.
- Use `@apply` sparingly and only in `styles/main.css` for truly global base styles.
- Use Tailwind config for custom theme values (colors, spacing, fonts) — not arbitrary values like `w-[347px]`.
- Group utilities logically: layout → sizing → spacing → typography → colors → effects.
- Use `class` binding with arrays or objects for conditional styles, not string concatenation.

```vue
<!-- Good: logical grouping -->
<div class="flex items-center justify-between w-full px-4 py-2 text-sm text-gray-700 bg-white rounded-lg shadow-sm">

<!-- Good: conditional classes -->
<button
  :class="[
    'px-4 py-2 rounded-lg font-medium transition-colors',
    active ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
    disabled && 'opacity-50 cursor-not-allowed',
  ]"
>
```

### Headless UI
- Use Headless UI for all interactive patterns: `Dialog`, `Menu`, `Listbox`, `Combobox`, `Switch`, `RadioGroup`, `Popover`, `Disclosure`, `Tab`.
- Never build custom modals, dropdowns, or listboxes from scratch — use Headless UI.
- Always pair with Tailwind for styling. Headless UI provides behavior + accessibility, Tailwind provides visuals.
- Use the `as` prop to control rendered element when needed.
- Always handle keyboard navigation — Headless UI does this automatically, don't override it.

```vue
<template>
  <Listbox v-model="selectedOption">
    <ListboxButton class="w-full px-3 py-2 text-left bg-white border rounded-lg">
      {{ selectedOption.label }}
    </ListboxButton>
    <ListboxOptions class="absolute mt-1 w-full bg-white border rounded-lg shadow-lg">
      <ListboxOption
        v-for="option in options"
        :key="option.id"
        :value="option"
        v-slot="{ active, selected }"
        class="px-3 py-2 cursor-pointer"
        :class="{ 'bg-blue-50': active }"
      >
        {{ option.label }}
      </ListboxOption>
    </ListboxOptions>
  </Listbox>
</template>
```

### Composables
- Name: `use<Feature>.ts` (e.g., `useGaze.ts`, `useDwell.ts`, `useSpeech.ts`).
- Return an object with named refs and functions — never return a raw ref.
- Handle cleanup: use `onUnmounted` or return a `stop()`/`dispose()` method for subscriptions.
- Composables that depend on the component lifecycle must only be called inside `setup()`.
- Keep composables focused — one responsibility per composable.

```typescript
// composables/useDwell.ts
export function useDwell(options: DwellOptions = {}) {
  const dwellTime = ref(options.dwellMs ?? 800)
  const isHovering = ref(false)
  const progress = ref(0)

  let timer: ReturnType<typeof setTimeout> | null = null

  function startDwell(targetId: string) { /* ... */ }
  function cancelDwell() { /* ... */ }

  onUnmounted(() => {
    if (timer) clearTimeout(timer)
  })

  return {
    dwellTime: readonly(dwellTime),
    isHovering: readonly(isHovering),
    progress: readonly(progress),
    startDwell,
    cancelDwell,
  }
}
```

### Pinia Stores
- One store per domain: `useTrackingStore`, `useSettingsStore`, `useUserStore`.
- Use Setup Store syntax (Composition API style) for consistency.
- Keep stores lean — complex derived data goes in composables that consume the store.
- Actions that call services must handle errors and update loading/error state.
- Use `readonly()` or getters for data that should not be mutated from outside.

```typescript
// stores/tracking.ts
export const useTrackingStore = defineStore('tracking', () => {
  const state = ref<TrackingState>({ status: 'idle' })
  const sessions = ref<TrackingSession[]>([])
  const isLoading = ref(false)

  const isActive = computed(() => state.value.status === 'active')

  async function fetchSessions() {
    isLoading.value = true
    try {
      sessions.value = await trackingService.getSessions()
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
    } finally {
      isLoading.value = false
    }
  }

  return {
    state: readonly(state),
    sessions: readonly(sessions),
    isLoading: readonly(isLoading),
    isActive,
    fetchSessions,
  }
})
```

### API Services Layer
- Central API client in `services/api.ts` with base URL, interceptors, error handling.
- One service file per backend domain matching backend router structure.
- All functions are async, return typed data (not raw Response).
- Handle API errors consistently — map to user-friendly messages.
- Never import Vue reactivity (`ref`, `computed`) in services — they are plain TypeScript.

```typescript
// services/tracking.ts
import { api } from './api'
import type { TrackingSession, SessionCreate } from '@/types/tracking'

export const trackingService = {
  async getSessions(): Promise<TrackingSession[]> {
    const { data } = await api.get<TrackingSession[]>('/api/v1/tracking/sessions')
    return data
  },

  async createSession(payload: SessionCreate): Promise<TrackingSession> {
    const { data } = await api.post<TrackingSession>('/api/v1/tracking/sessions', payload)
    return data
  },
}
```

### WebSocket Communication

The frontend consumes two separate WebSocket streams:
1. **Eye-tracker WS** (~30Hz) — gaze coordinates from the Tobii SDK via Electron native layer. Not routed through the FastAPI backend.
2. **STT WS** (`/ws/stt`) — speech-to-text events pushed by the FastAPI backend (partial transcripts, final results, status changes).

#### Generic WebSocket Client (`services/ws.ts`)
- Reusable WebSocket client with automatic reconnect (exponential backoff).
- Used by both gaze and STT composables with different URLs.
- Parse incoming messages and dispatch to a handler callback.
- Never use raw `WebSocket` directly in components — always go through the service/composables.

```typescript
// services/ws.ts
export type WSConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting'

export interface WSClientOptions {
  url: string
  reconnectIntervalMs?: number
  maxReconnectAttempts?: number
  onMessage: (data: unknown) => void
  onStatusChange?: (status: WSConnectionStatus) => void
}

export function createWSClient(options: WSClientOptions) {
  let ws: WebSocket | null = null
  let reconnectAttempts = 0

  function connect() { /* ... */ }
  function disconnect() { /* ... */ }
  function send(message: object) {
    ws?.send(JSON.stringify(message))
  }

  return { connect, disconnect, send }
}
```

#### Message Types (`types/ws.ts`)
- Separate type definitions for gaze messages and STT messages.
- STT types mirror the backend Pydantic schemas exactly.
- Use discriminated unions with `type` field for type-safe handling.

```typescript
// types/ws.ts

// --- Eye tracker messages (from Tobii/Electron WS) ---
interface GazeDataMessage {
  type: 'gaze_data'
  x: number
  y: number
  fixation: boolean
  timestamp: number
}

// --- STT messages (from FastAPI backend WS) ---
interface STTPartialResult {
  type: 'stt_partial'
  text: string
  language: string
  timestamp: number
}

interface STTFinalResult {
  type: 'stt_final'
  text: string
  language: string
  confidence: number
  timestamp: number
}

interface STTStatusChange {
  type: 'stt_started' | 'stt_stopped' | 'stt_error'
  detail: string | null
  timestamp: number
}

type STTEvent = STTPartialResult | STTFinalResult | STTStatusChange
```

#### Gaze Composable (`composables/useGaze.ts`)
- Receives eye-tracking data via WebSocket at ~30Hz from the Tobii SDK / Electron native layer.
- At 30Hz, Vue reactivity can handle updates directly — no need for a `requestAnimationFrame` buffer. Use `shallowRef` to avoid deep reactivity overhead.
- Apply smoothing (exponential moving average) before exposing to components.
- Detect fixations vs. saccades and expose as reactive state.

```typescript
// composables/useGaze.ts
export function useGaze() {
  const gazePoint = shallowRef<GazePoint | null>(null)
  const isFixating = ref(false)
  const connectionStatus = ref<WSConnectionStatus>('disconnected')

  const wsClient = createWSClient({
    url: GAZE_WS_URL,  // e.g., ws://localhost:PORT from Electron
    onMessage: (data) => {
      const msg = data as GazeDataMessage
      gazePoint.value = applySmoothing(msg)
      isFixating.value = detectFixation(msg)
    },
    onStatusChange: (status) => {
      connectionStatus.value = status
    },
  })

  onMounted(() => wsClient.connect())
  onUnmounted(() => wsClient.disconnect())

  return {
    gazePoint: readonly(gazePoint),
    isFixating: readonly(isFixating),
    connectionStatus: readonly(connectionStatus),
  }
}
```

#### STT Events Composable (`composables/useSTTEvents.ts`)
- Subscribes to the FastAPI backend WebSocket (`/ws/stt`).
- Dispatches STT events to registered handlers by `type`.
- Exposes current transcript state (partial + final) as reactive refs.

```typescript
// composables/useSTTEvents.ts
export function useSTTEvents() {
  const connectionStatus = ref<WSConnectionStatus>('disconnected')
  const partialText = ref('')
  const finalText = ref('')
  const isListening = ref(false)

  const handlers = new Map<string, Set<(event: STTEvent) => void>>()

  function on<T extends STTEvent['type']>(
    type: T,
    handler: (event: Extract<STTEvent, { type: T }>) => void,
  ) {
    if (!handlers.has(type)) handlers.set(type, new Set())
    handlers.get(type)!.add(handler as any)
    return () => handlers.get(type)?.delete(handler as any)
  }

  const wsClient = createWSClient({
    url: `${API_BASE_WS}/ws/stt`,
    onMessage: (data) => {
      const event = data as STTEvent
      // Update internal state
      if (event.type === 'stt_partial') partialText.value = event.text
      if (event.type === 'stt_final') {
        finalText.value = event.text
        partialText.value = ''
      }
      if (event.type === 'stt_started') isListening.value = true
      if (event.type === 'stt_stopped') isListening.value = false
      // Dispatch to registered handlers
      handlers.get(event.type)?.forEach(fn => fn(event))
    },
    onStatusChange: (status) => {
      connectionStatus.value = status
    },
  })

  // Send commands to backend (start/stop listening)
  function sendCommand(command: STTCommand) {
    wsClient.send(command)
  }

  onMounted(() => wsClient.connect())
  onUnmounted(() => wsClient.disconnect())

  return {
    connectionStatus: readonly(connectionStatus),
    partialText: readonly(partialText),
    finalText: readonly(finalText),
    isListening: readonly(isListening),
    on,
    sendCommand,
  }
}
```

#### WebSocket Rules
- **Auto-reconnect** with exponential backoff on both WS connections. Critical for the assistive use case.
- **Connection status indicators** — always show WS connection state for both gaze and STT in the UI. The user must know if their input methods are working.
- **Graceful degradation** — if gaze WS disconnects, show a clear message and enable keyboard/mouse fallback. If STT WS disconnects, disable voice input UI and show status.
- **`shallowRef` for gaze data** — at 30Hz, Vue reactivity is fine but avoid deep reactive objects. Use `shallowRef` for the gaze point to minimize overhead.
- **Message validation** — validate incoming WS messages before processing. Discard unknown `type` values with a warning log, don't crash.
- **Cleanup** — always close WS connections in `onUnmounted`.
- **Single connection per source** — never open multiple WS connections to the same endpoint. Use a shared composable instance (provide/inject at app root or singleton pattern).
- **Separate concerns** — gaze and STT are independent streams. Never mix them into a single WebSocket connection or composable.

### Electron IPC Communication
- All IPC calls go through the preload bridge — never use `ipcRenderer` directly in renderer.
- Type the preload API in `types/electron.d.ts` and expose via `window.electronAPI`.
- Wrap IPC calls in composables or services for clean component code.
- Handle IPC errors gracefully — the main process may not respond.

```typescript
// types/electron.d.ts
interface ElectronAPI {
  getGazeData: () => Promise<GazePoint>
  onGazeUpdate: (callback: (point: GazePoint) => void) => void
  speak: (text: string, options?: TTSOptions) => Promise<void>
}

declare global {
  interface Window {
    electronAPI: ElectronAPI
  }
}
```

## Accessibility — Critical for Assistive App

- **This is an assistive communication app — accessibility is not optional, it is the core feature.**
- All interactive elements must be keyboard-navigable and screen-reader friendly.
- Use semantic HTML (`<button>`, `<nav>`, `<main>`, `<header>`) — not `<div>` with click handlers.
- All images and icons must have `alt` text or `aria-label`.
- Use `aria-live="polite"` regions for dynamic content updates (gaze predictions, TTS feedback).
- Focus management: always manage focus explicitly after navigation, modal open/close, dynamic content.
- Color contrast must meet WCAG AA minimum (4.5:1 for text, 3:1 for large text).
- Gaze-interactive elements must have generous hit targets (minimum 48×48px, prefer larger for eye tracking).
- Dwell-click feedback must be visible and clear (progress indicator on target).
- Provide alternative input methods: gaze, keyboard, switch, mouse — never assume one.
- Test with screen readers (NVDA on Windows).

## Performance — Real-Time Constraints

- Gaze data arrives at ~30Hz. At this rate, Vue reactivity with `shallowRef` handles updates fine — no `requestAnimationFrame` buffer needed.
- Still use `shallowRef` (not `ref`) for gaze point to avoid deep reactivity overhead on frequent updates.
- Debounce or throttle expensive computations triggered by gaze (predictions, UI highlights) if they can't keep up with 30fps.
- Use `v-memo` or `v-once` for static content that doesn't change.
- Lazy-load views and heavy components with `defineAsyncComponent`.
- Keep the main reactive graph shallow — deeply nested reactive objects cause performance issues.
- Use `shallowRef` for large data structures that are replaced, not mutated.
- Profile with Vue DevTools and Chrome Performance tab if UI feels sluggish.

## Naming Conventions
- Files: `PascalCase.vue` for components, `camelCase.ts` for everything else.
- Components: `PascalCase` in template and file name (`GazeOverlay.vue`, `<GazeOverlay />`).
- Composables: `use<Name>.ts` → `useDwell.ts`, `useGaze.ts`.
- Stores: `use<Name>Store` → `useTrackingStore`.
- Services: `<domain>Service` → `trackingService`.
- Types/Interfaces: `PascalCase` → `GazePoint`, `TrackingSession`.
- Constants: `UPPER_SNAKE_CASE` → `DEFAULT_DWELL_TIME_MS`.
- CSS: Tailwind utilities only, no custom class names.

## Things to NEVER Do
- Never use Options API or `defineComponent()`.
- Never use `<style scoped>` for layout/spacing — use Tailwind classes.
- Never use `any` — use `unknown` with type narrowing.
- Never call `window.electronAPI` or services directly from components — go through composables or stores.
- Never use `v-html` — XSS risk.
- Never use `setTimeout` / `setInterval` without cleanup in `onUnmounted`.
- Never use `@click` on `<div>` or `<span>` — use `<button>` or Headless UI components.
- Never hardcode strings shown to user — prepare for i18n from the start with a constants file or Vue I18n.
- Never block the main thread with heavy computation — offload to Web Workers or the backend.
- Never ignore error states in UI — always show feedback (loading, error, empty states).