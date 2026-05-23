package com.unutrip.data.repository

import com.unutrip.data.api.ApiService
import com.unutrip.data.model.Destination
import com.unutrip.data.model.DestinationResponse
import com.unutrip.utils.Resource
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import retrofit2.Response

class DestinationRepositoryTest {

    private val api = mockk<ApiService>()
    private val repo = DestinationRepository(api)

    @Test
    fun getDestinations_success() = runTest {
        val destination = sampleDestination()
        val payload = DestinationResponse(
            success = true,
            data = listOf(destination),
            total = 1,
            page = 1,
            limit = 10
        )
        coEvery { api.getDestinations("Bearer t", 1, 10, null, null, null) } returns Response.success(payload)

        val result = repo.getDestinations("Bearer t")

        assertTrue(result is Resource.Success)
        assertEquals(1, (result as Resource.Success).data.data.size)
    }

    @Test
    fun getDestinations_httpError() = runTest {
        coEvery { api.getDestinations(any(), any(), any(), any(), any(), any()) } returns Response.error(
            401,
            "".toResponseBody(null)
        )

        val result = repo.getDestinations("Bearer t")

        assertTrue(result is Resource.Error)
        assertEquals("Không thể tải danh sách địa điểm", (result as Resource.Error).message)
    }

    private fun sampleDestination() = Destination(
        id = 1,
        name = "Hue Citadel",
        description = "Heritage",
        address = "Hue",
        city = "Hue",
        province = "Thua Thien Hue",
        latitude = 16.0,
        longitude = 107.0,
        category = "culture",
        images = emptyList(),
        rating = 4.5f,
        reviewCount = 10,
        openTime = null,
        closeTime = null,
        entryFee = null,
        tags = emptyList()
    )
}
