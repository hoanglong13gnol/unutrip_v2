package com.unutrip.data.api

import com.unutrip.utils.SessionManager
import okhttp3.Interceptor
import okhttp3.Response

/**
 * Attaches Bearer token from [SessionManager] and clears session on 401.
 */
class AuthInterceptor(
    private val sessionManager: SessionManager
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val original = chain.request()
        val rawToken = sessionManager.getToken()?.trim().orEmpty()
        val request = if (rawToken.isNotEmpty()) {
            original.newBuilder()
                .header("Authorization", "Bearer $rawToken")
                .build()
        } else {
            original
        }

        val response = chain.proceed(request)
        if (response.code == 401 && rawToken.isNotEmpty()) {
            sessionManager.clearSession()
        }
        return response
    }
}
