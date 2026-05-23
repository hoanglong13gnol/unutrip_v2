package com.unutrip.viewmodel

import androidx.arch.core.executor.testing.InstantTaskExecutorRule
import com.unutrip.data.model.UserStats
import com.unutrip.data.repository.UserRepository
import com.unutrip.utils.Resource
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@OptIn(ExperimentalCoroutinesApi::class)
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34], manifest = Config.NONE)
class ProfileViewModelTest {

    @get:Rule
    val instantTaskExecutorRule = InstantTaskExecutorRule()

    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setup() {
        Dispatchers.setMain(dispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun loadStats_emitsSuccess() = runTest(dispatcher) {
        val repo = mockk<UserRepository>()
        coEvery { repo.getStats("Bearer t") } returns Resource.Success(
            UserStats(itineraryCount = 2, favoriteCount = 3, reviewCount = 1)
        )
        val vm = ProfileViewModel(repo)
        vm.init("Bearer t")
        vm.loadStats()
        advanceUntilIdle()

        val value = vm.stats.value
        assertTrue(value is Resource.Success)
        assertEquals(2, (value as Resource.Success).data.itineraryCount)
        coVerify { repo.getStats("Bearer t") }
    }

    @Test
    fun updateProfile_emitsErrorFromRepository() = runTest(dispatcher) {
        val repo = mockk<UserRepository>()
        coEvery { repo.updateProfile(any(), any()) } returns Resource.Error("fail")
        val vm = ProfileViewModel(repo)
        vm.init("Bearer t")
        vm.updateProfile(
            com.unutrip.data.model.User(1, "A", "a@b.com", null, null, emptyList())
        )
        advanceUntilIdle()
        assertTrue(vm.profileUpdate.value is Resource.Error)
    }
}
