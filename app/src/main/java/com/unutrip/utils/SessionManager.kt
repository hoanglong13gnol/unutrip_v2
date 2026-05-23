package com.unutrip.utils

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKeys
import com.google.gson.Gson
import com.unutrip.BuildConfig
import com.unutrip.data.model.User

/**
 * Session an toàn hơn: [EncryptedSharedPreferences] (AES-GCM).
 * Dùng [MasterKeys] + overload `create(name, alias, context, …)` (tương thích security-crypto 1.0.x).
 * Tự động chuyển dữ liệu từ prefs legacy (plain hoặc encrypted cũ) một lần.
 */
class SessionManager private constructor(context: Context) {

    private val prefs: SharedPreferences = createEncryptedPrefs(context.applicationContext)
    private val gson = Gson()

    companion object {
        /** Tên prefs cũ (SmartTravel) — chỉ dùng khi migrate, không ghi mới. */
        private val LEGACY_PLAIN_PREF_NAMES = listOf("SmartTravelSession", "UNUtripSession")
        private val LEGACY_ENCRYPTED_PREF_NAMES = listOf("SmartTravelSession_secure", "UNUtripSession_secure")
        private const val ENCRYPTED_PREF_NAME = "UNUtripSession_secure"
        private const val DEBUG_PLAIN_PREF_NAME = "UNUtripSession_debug_plain"
        private const val TAG = "SessionManager"
        private const val KEY_TOKEN = "auth_token"
        private const val KEY_USER = "user_data"
        private const val KEY_IS_LOGGED_IN = "is_logged_in"

        private val lock = Any()

        @Volatile
        private var INSTANCE: SessionManager? = null

        fun getInstance(context: Context): SessionManager {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: SessionManager(context.applicationContext).also { INSTANCE = it }
            }
        }
    }

    private fun createEncryptedPrefs(context: Context): SharedPreferences {
        synchronized(lock) {
            return try {
                val masterKeyAlias = MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC)

                val encrypted = EncryptedSharedPreferences.create(
                    ENCRYPTED_PREF_NAME,
                    masterKeyAlias,
                    context,
                    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
                )

                migrateLegacyIfNeeded(context, encrypted)
                encrypted
            } catch (e: Exception) {
                if (BuildConfig.DEBUG) {
                    Log.w(TAG, "Encrypted prefs unavailable; using debug plain prefs", e)
                    context.getSharedPreferences(DEBUG_PLAIN_PREF_NAME, Context.MODE_PRIVATE)
                } else {
                    throw e
                }
            }
        }
    }

    private fun migrateLegacyIfNeeded(context: Context, encrypted: SharedPreferences) {
        if (encrypted.all.isNotEmpty()) return

        for (legacyName in LEGACY_ENCRYPTED_PREF_NAMES) {
            if (legacyName == ENCRYPTED_PREF_NAME) continue
            val migrated = migrateFromEncryptedLegacy(context, encrypted, legacyName)
            if (migrated) return
        }

        for (legacyName in LEGACY_PLAIN_PREF_NAMES) {
            val legacy = context.getSharedPreferences(legacyName, Context.MODE_PRIVATE)
            if (legacy.all.isEmpty()) continue

            val token = legacy.getString(KEY_TOKEN, null)
            val userJson = legacy.getString(KEY_USER, null)
            val loggedIn = legacy.getBoolean(KEY_IS_LOGGED_IN, false)

            encrypted.edit().apply {
                if (!token.isNullOrBlank()) putString(KEY_TOKEN, token)
                if (!userJson.isNullOrBlank()) putString(KEY_USER, userJson)
                putBoolean(KEY_IS_LOGGED_IN, loggedIn)
                apply()
            }
            legacy.edit().clear().apply()
            return
        }
    }

    private fun migrateFromEncryptedLegacy(
        context: Context,
        target: SharedPreferences,
        legacyName: String,
    ): Boolean {
        return try {
            val masterKeyAlias = MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC)
            val legacyEncrypted = EncryptedSharedPreferences.create(
                legacyName,
                masterKeyAlias,
                context,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
            )
            if (legacyEncrypted.all.isEmpty()) return false

            val token = legacyEncrypted.getString(KEY_TOKEN, null)
            val userJson = legacyEncrypted.getString(KEY_USER, null)
            val loggedIn = legacyEncrypted.getBoolean(KEY_IS_LOGGED_IN, false)

            target.edit().apply {
                if (!token.isNullOrBlank()) putString(KEY_TOKEN, token)
                if (!userJson.isNullOrBlank()) putString(KEY_USER, userJson)
                putBoolean(KEY_IS_LOGGED_IN, loggedIn)
                apply()
            }
            legacyEncrypted.edit().clear().apply()
            true
        } catch (_: Exception) {
            false
        }
    }

    fun saveSession(token: String, user: User) {
        prefs.edit().apply {
            putString(KEY_TOKEN, token)
            putString(KEY_USER, gson.toJson(user))
            putBoolean(KEY_IS_LOGGED_IN, true)
            apply()
        }
    }

    fun getToken(): String? = prefs.getString(KEY_TOKEN, null)

    fun getBearerToken(): String = "Bearer ${getToken() ?: ""}"

    fun getUser(): User? {
        val json = prefs.getString(KEY_USER, null) ?: return null
        return gson.fromJson(json, User::class.java)
    }

    fun isLoggedIn(): Boolean = prefs.getBoolean(KEY_IS_LOGGED_IN, false)

    fun clearSession() {
        prefs.edit().clear().apply()
    }

    fun updateUser(user: User) {
        prefs.edit().putString(KEY_USER, gson.toJson(user)).apply()
    }
}
