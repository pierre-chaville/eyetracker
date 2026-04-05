<template>
  <aside
    :class="[
      'fixed left-0 top-0 h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 z-40',
      isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
      isExpanded ? 'w-64' : 'w-20'
    ]"
  >
    <!-- Logo/Brand -->
    <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
      <div v-if="isExpanded" class="flex items-center space-x-3">
        <div class="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
          <EyeIcon class="w-6 h-6 text-white" />
        </div>
        <h1 class="text-xl font-bold text-gray-900 dark:text-white">{{ $t('common.appName') }}</h1>
      </div>
      <div v-else class="flex items-center justify-center w-full">
        <div class="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
          <EyeIcon class="w-6 h-6 text-white" />
        </div>
      </div>
      <div class="flex items-center space-x-2">
        <button
          @click="$emit('toggle')"
          class="hidden md:flex p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          :title="isExpanded ? 'Collapse menu' : 'Expand menu'"
        >
          <Bars3Icon v-if="isExpanded" class="w-5 h-5 text-gray-600 dark:text-gray-300" />
          <ChevronRightIcon v-else class="w-5 h-5 text-gray-600 dark:text-gray-300" />
        </button>
        <button
          @click="$emit('close')"
          class="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <XMarkIcon class="w-5 h-5 text-gray-600 dark:text-gray-300" />
        </button>
      </div>
    </div>

    <!-- Navigation Menu -->
    <nav class="p-4 space-y-2">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        @click="$emit('close')"
        :class="[
          'flex items-center rounded-lg transition-colors',
          isExpanded ? 'px-4 py-3 space-x-3' : 'px-3 py-3 justify-center',
          isActive(item.path)
            ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 font-semibold'
            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
        ]"
        :title="!isExpanded ? item.label : ''"
      >
        <component :is="item.icon" class="w-5 h-5 flex-shrink-0" />
        <span v-if="isExpanded" class="truncate">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- Bottom Actions -->
    <div class="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700 space-y-3">
      <div :class="['flex items-center', isExpanded ? 'justify-center space-x-2' : 'justify-center space-x-1']">
        <ThemeSwitcher />
        <LanguageSwitcher />
      </div>
      <button
        @click="exitApp"
        :class="[
          'flex items-center w-full rounded-lg transition-colors text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30',
          isExpanded ? 'px-4 py-2 space-x-3' : 'px-3 py-2 justify-center',
        ]"
        :title="$t('sidebar.exit')"
      >
        <ArrowRightOnRectangleIcon class="w-5 h-5 flex-shrink-0" />
        <span v-if="isExpanded" class="text-sm font-medium">{{ $t('sidebar.exit') }}</span>
      </button>
    </div>
  </aside>

  <!-- Overlay for mobile -->
  <div
    v-if="isOpen"
    @click="$emit('close')"
    class="fixed inset-0 bg-black/50 z-30 md:hidden"
  ></div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import {
  HomeIcon,
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  EyeIcon,
  UserGroupIcon,
  WrenchScrewdriverIcon,
  XMarkIcon,
  Bars3Icon,
  ChevronRightIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/vue/24/outline';
import ThemeSwitcher from './ThemeSwitcher.vue';
import LanguageSwitcher from './LanguageSwitcher.vue';
import { useI18n } from 'vue-i18n';
import { isDocumentElementFullscreen, safeExitFullscreen } from '../utils/fullscreen';
import { isWebView2Host, requestHostClose } from '../utils/hostBridge';

defineProps({
  isOpen: {
    type: Boolean,
    default: true,
  },
  isExpanded: {
    type: Boolean,
    default: true,
  },
});

defineEmits(['close', 'toggle']);

const route = useRoute();
const { t } = useI18n();

const menuItems = computed(() => [
  {
    path: '/',
    label: t('sidebar.home'),
    icon: HomeIcon,
  },
  {
    path: '/communicate',
    label: t('sidebar.communicate'),
    icon: ChatBubbleLeftRightIcon,
  },
  {
    path: '/keyboard',
    label: t('sidebar.keyboard'),
    icon: ChatBubbleLeftRightIcon, // Using chat icon as placeholder, can be changed later
  },
  {
    path: '/communication-sessions',
    label: t('sidebar.communicationSessions'),
    icon: DocumentTextIcon,
  },
  {
    path: '/calibration',
    label: t('sidebar.calibration'),
    icon: Cog6ToothIcon,
  },
  {
    path: '/eye-tracking',
    label: t('sidebar.viewEyeTracking'),
    icon: EyeIcon,
  },
  {
    path: '/users',
    label: t('sidebar.users'),
    icon: UserGroupIcon,
  },
  {
    path: '/caregivers',
    label: t('sidebar.caregivers'),
    icon: UserGroupIcon,
  },
  {
    path: '/setup',
    label: t('sidebar.setup'),
    icon: WrenchScrewdriverIcon,
  },
]);

const isActive = (path) => {
  if (path === '/') {
    return route.path === '/';
  }
  return route.path.startsWith(path);
};

const escapeHtml = (s: string) =>
  s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

/**
 * Leave the Fullscreen API cleanly (all vendor variants). Browsers launched
 * with --app / after requestFullscreen() may not honor window.close() until
 * this completes; do not navigate to about:blank — that destroys the app and
 * leaves a blank page when close() is still blocked.
 */
const ensureDocumentFullscreenExited = (): Promise<void> => {
  if (!isDocumentElementFullscreen()) {
    return Promise.resolve();
  }

  return new Promise((resolve) => {
    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      clearTimeout(safetyTimer);
      document.removeEventListener('fullscreenchange', onFsChange);
      document.removeEventListener('webkitfullscreenchange', onFsChange);
      document.removeEventListener('MSFullscreenChange', onFsChange);
      resolve();
    };

    const onFsChange = () => {
      if (!isDocumentElementFullscreen()) {
        finish();
      }
    };

    document.addEventListener('fullscreenchange', onFsChange);
    document.addEventListener('webkitfullscreenchange', onFsChange);
    document.addEventListener('MSFullscreenChange', onFsChange);

    const safetyTimer = window.setTimeout(finish, 800);

    const runExit = async () => {
      await safeExitFullscreen();
      if (!isDocumentElementFullscreen()) {
        finish();
      }
    };

    void runExit();
  });
};

const exitApp = async () => {
  await ensureDocumentFullscreenExited();
  // Let the compositor finish leaving fullscreen before close (helps Chrome --app).
  await new Promise<void>((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
  });

  // Restore focus to this document (e.g. after DevTools) so close() / fullscreen teardown behave.
  try {
    window.focus();
  } catch {
    /* ignore */
  }

  if (isWebView2Host()) {
    requestHostClose();
    return;
  }

  window.close();

  setTimeout(() => {
    window.close();
  }, 250);

  // If the window is still open (timers only run if the browsing context survives),
  // show a touch-friendly screen: a tap is a user gesture and often allows window.close().
  setTimeout(() => {
    const title = escapeHtml(t('sidebar.exitBlockedTitle'));
    const body = escapeHtml(t('sidebar.exitBlockedBody'));
    const btnLabel = escapeHtml(t('sidebar.exitCloseAgain'));
    document.body.innerHTML = `
      <div style="box-sizing:border-box;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:clamp(1rem,4vw,2.5rem);background:#1e1e2e;color:#cdd6f4;font-family:system-ui,-apple-system,'Segoe UI',sans-serif;text-align:center">
        <h1 style="margin:0 0 1rem;font-size:clamp(1.35rem,4vw,1.85rem);font-weight:700;line-height:1.25">${title}</h1>
        <p style="margin:0 0 2rem;max-width:28rem;font-size:clamp(1.05rem,3vw,1.25rem);line-height:1.5;opacity:.95">${body}</p>
        <button type="button" id="exit-fallback-close" style="touch-action:manipulation;-webkit-tap-highlight-color:transparent;min-height:4rem;min-width:min(100%,18rem);padding:1rem 1.75rem;border:none;border-radius:1rem;background:#89b4fa;color:#11111b;font-size:clamp(1.1rem,3vw,1.35rem);font-weight:700;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.35)">${btnLabel}</button>
      </div>`;
    const tryCloseFromGesture = () => {
      try {
        window.focus();
      } catch {
        /* ignore */
      }
      if (isWebView2Host()) {
        requestHostClose();
        return;
      }
      window.close();
      setTimeout(() => window.close(), 200);
    };
    document.getElementById('exit-fallback-close')?.addEventListener('click', tryCloseFromGesture, {
      passive: true,
    });
  }, 700);
};
</script>

