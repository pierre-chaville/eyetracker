import { ref, watch } from 'vue'

import { usersAPI } from '../services/api'
import { parseCalibrationData } from '../utils/calibration'
import type { CalibrationCoefficients } from '../types/tracking'
import type { UserRead } from '../types/api'

export function useCalibration() {
  const selectedUserId = ref<number | null>(null)
  const calibrationCoefficients = ref<CalibrationCoefficients | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const loadCalibration = async (userId: number | null) => {
    if (!userId) {
      calibrationCoefficients.value = null
      return
    }

    try {
      loading.value = true
      error.value = null
      const user = (await usersAPI.get(userId)) as UserRead
      calibrationCoefficients.value = parseCalibrationData(user)
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load calibration'
      error.value = errorMessage
      console.error('Error loading calibration:', err)
      calibrationCoefficients.value = null
    } finally {
      loading.value = false
    }
  }

  watch(
    () => {
      const savedUserId = localStorage.getItem('selectedUserId')
      return savedUserId ? Number.parseInt(savedUserId, 10) : null
    },
    (newUserId) => {
      selectedUserId.value = newUserId
      loadCalibration(newUserId)
    },
    { immediate: true },
  )

  if (typeof window !== 'undefined') {
    window.addEventListener('storage', (e) => {
      if (e.key === 'selectedUserId') {
        const userId = e.newValue ? Number.parseInt(e.newValue, 10) : null
        selectedUserId.value = userId
        loadCalibration(userId)
      }
    })
  }

  return {
    selectedUserId,
    calibrationCoefficients,
    loading,
    error,
    loadCalibration,
  }
}
