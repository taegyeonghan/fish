import axios from 'axios'
import i18n from '../i18n'

function createApiError(message, errorCode = 'api_error', status = null, payload = null) {
  const err = new Error(message || 'Error')
  err.errorCode = errorCode
  err.status = status
  err.payload = payload
  return err
}

// axios
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001',
  timeout: 300000, // 5(설명 생략)
  headers: {
    'Content-Type': 'application/json'
  }
})

service.interceptors.request.use(
  config => {
    config.headers['Accept-Language'] = i18n.global.locale.value
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// (설명 생략)
service.interceptors.response.use(
  response => {
    const res = response.data
    
    // success，
    if (!res.success && res.success !== undefined) {
      const message = res.error || res.message || 'Unknown error'
      const errorCode = res.error_code || 'api_error'
      console.error('API Error:', message, errorCode)
      return Promise.reject(
        createApiError(message, errorCode, response?.status || null, res)
      )
    }
    
    return res
  },
  error => {
    console.error('Response error:', error)
    const status = error?.response?.status || null
    const payload = error?.response?.data || null
    const payloadCode = payload?.error_code
    
    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      console.error('Request timeout')
    }
    
    if (error.message === 'Network Error') {
      console.error('Network error - please check your connection')
      return Promise.reject(createApiError(error.message, 'network_error', status, payload))
    }

    if (payloadCode || payload?.error || payload?.message) {
      return Promise.reject(
        createApiError(
          payload?.error || payload?.message || error.message,
          payloadCode || 'api_error',
          status,
          payload
        )
      )
    }

    if (error.code === 'ECONNABORTED') {
      return Promise.reject(createApiError(error.message, 'timeout', status, payload))
    }

    return Promise.reject(createApiError(error.message, 'request_failed', status, payload))
  }
)

export const requestWithRetry = async (requestFn, maxRetries = 3, delay = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn()
    } catch (error) {
      if (i === maxRetries - 1) throw error
      
      console.warn(`Request failed, retrying (${i + 1}/${maxRetries})...`)
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)))
    }
  }
}

export default service