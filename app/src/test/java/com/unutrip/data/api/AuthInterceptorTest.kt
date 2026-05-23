package com.unutrip.data.api

import com.unutrip.utils.SessionManager
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34], manifest = Config.NONE)
class AuthInterceptorTest {

    private lateinit var server: MockWebServer
    private lateinit var sessionManager: SessionManager

    @Before
    fun setUp() {
        server = MockWebServer()
        server.start()
        sessionManager = mockk(relaxed = true)
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    @Test
    fun addsAuthorizationHeaderWhenTokenPresent() {
        every { sessionManager.getToken() } returns "test-token"
        server.enqueue(MockResponse().setResponseCode(200))

        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(sessionManager))
            .build()

        val request = Request.Builder().url(server.url("/probe")).build()
        client.newCall(request).execute().close()

        val recorded = server.takeRequest()
        assertEquals("Bearer test-token", recorded.getHeader("Authorization"))
    }

    @Test
    fun clearsSessionOn401() {
        every { sessionManager.getToken() } returns "expired"
        server.enqueue(MockResponse().setResponseCode(401))

        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(sessionManager))
            .build()

        client.newCall(Request.Builder().url(server.url("/probe")).build()).execute().close()

        verify { sessionManager.clearSession() }
    }

    @Test
    fun skipsAuthorizationWhenTokenBlank() {
        every { sessionManager.getToken() } returns null
        server.enqueue(MockResponse().setResponseCode(200))

        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(sessionManager))
            .build()

        client.newCall(Request.Builder().url(server.url("/probe")).build()).execute().close()

        assertTrue(server.takeRequest().getHeader("Authorization") == null)
    }
}
