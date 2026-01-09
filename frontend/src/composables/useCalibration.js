import { ref, watch } from 'vue';
import { usersAPI } from '../services/api';
import { parseCalibrationData } from '../utils/calibration';

/**
 * Composable for managing calibration data for the selected user
 * Provides calibration coefficients that can be used with useEyeTracking
 */
export function useCalibration() {
  const selectedUserId = ref(null);
  const calibrationCoefficients = ref(null);
  const loading = ref(false);
  const error = ref(null);

  const loadCalibration = async (userId) => {
    if (!userId) {
      calibrationCoefficients.value = null;
      return;
    }

    try {
      loading.value = true;
      error.value = null;
      const user = await usersAPI.get(userId);
      calibrationCoefficients.value = parseCalibrationData(user);
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || 'Failed to load calibration';
      console.error('Error loading calibration:', err);
      calibrationCoefficients.value = null;
    } finally {
      loading.value = false;
    }
  };

  // Watch for selected user ID changes
  watch(() => {
    const savedUserId = localStorage.getItem('selectedUserId');
    return savedUserId ? parseInt(savedUserId) : null;
  }, (newUserId) => {
    selectedUserId.value = newUserId;
    if (newUserId) {
      loadCalibration(newUserId);
    } else {
      calibrationCoefficients.value = null;
    }
  }, { immediate: true });

  // Also listen for storage events (when user changes in another tab/component)
  if (typeof window !== 'undefined') {
    window.addEventListener('storage', (e) => {
      if (e.key === 'selectedUserId') {
        const userId = e.newValue ? parseInt(e.newValue) : null;
        selectedUserId.value = userId;
        if (userId) {
          loadCalibration(userId);
        } else {
          calibrationCoefficients.value = null;
        }
      }
    });
  }

  return {
    selectedUserId,
    calibrationCoefficients,
    loading,
    error,
    loadCalibration,
  };
}

