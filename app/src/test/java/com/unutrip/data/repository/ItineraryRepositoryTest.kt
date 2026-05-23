package com.unutrip.data.repository

import com.unutrip.data.api.ApiService
import com.unutrip.data.model.ApiResponse
import com.unutrip.data.model.CreateItineraryRequest
import com.unutrip.data.model.Itinerary
import com.unutrip.utils.Resource
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import retrofit2.Response

class ItineraryRepositoryTest {

    private val api = mockk<ApiService>()
    private val repo = ItineraryRepository(api)

    @Test
    fun createItinerary_success() = runTest {
        val itinerary = sampleItinerary(id = 9)
        coEvery { api.createItinerary("Bearer t", any()) } returns Response.success(
            ApiResponse(success = true, message = "ok", data = itinerary)
        )

        val result = repo.createItinerary(
            "t",
            CreateItineraryRequest(
                title = "Trip",
                description = null,
                startDate = "2026-06-01",
                endDate = "2026-06-03"
            )
        )

        assertTrue(result is Resource.Success)
        assertEquals(9, (result as Resource.Success).data.id)
    }

    @Test
    fun createItinerary_httpError() = runTest {
        coEvery { api.createItinerary(any(), any()) } returns Response.error(
            400,
            """{"message":"Tiêu đề không hợp lệ"}""".toResponseBody(null)
        )

        val result = repo.createItinerary(
            "Bearer t",
            CreateItineraryRequest(
                title = "",
                description = null,
                startDate = "2026-06-01",
                endDate = "2026-06-03"
            )
        )

        assertTrue(result is Resource.Error)
        assertEquals("Không thể tạo lịch trình", (result as Resource.Error).message)
    }

    private fun sampleItinerary(id: Int) = Itinerary(
        id = id,
        userId = 1,
        title = "Trip",
        description = null,
        startDate = "2026-06-01",
        endDate = "2026-06-03",
        totalDays = 3,
        status = "draft",
        days = emptyList(),
        estimatedBudget = null,
        createdAt = "2026-05-01"
    )
}
