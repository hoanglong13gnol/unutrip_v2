package com.unutrip.utils

import android.content.Context
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import com.unutrip.data.model.User

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], manifest = Config.NONE)
class SessionManagerTest {

    private lateinit var context: Context

    @Before
    fun setUp() {
        resetSingleton()
        context = RuntimeEnvironment.getApplication()
    }

    @After
    fun tearDown() {
        resetSingleton()
    }

    private fun resetSingleton() {
        val field = SessionManager::class.java.getDeclaredField("INSTANCE")
        field.isAccessible = true
        field.set(null, null)
    }

    @Test
    fun saveSession_roundTripsTokenAndUser() {
        val manager = SessionManager.getInstance(context)
        manager.clearSession()

        val user = User(
            id = 1,
            fullName = "Test User",
            email = "test@example.com",
            phone = null,
            avatar = null,
            preferences = emptyList()
        )
        manager.saveSession("jwt-token-123", user)

        assertTrue(manager.isLoggedIn())
        assertEquals("Bearer jwt-token-123", manager.getBearerToken())
        assertEquals(user.email, manager.getUser()?.email)

        manager.clearSession()
        assertFalse(manager.isLoggedIn())
    }
}
