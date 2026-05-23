package com.unutrip.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.unutrip.data.model.User
import com.unutrip.data.model.UserStats
import com.unutrip.data.repository.UserRepository
import com.unutrip.utils.Resource
import kotlinx.coroutines.launch
import okhttp3.MultipartBody

class ProfileViewModel(
    private val userRepository: UserRepository
) : ViewModel() {

    private val _stats = MutableLiveData<Resource<UserStats>>()
    val stats: LiveData<Resource<UserStats>> = _stats

    private val _profileUpdate = MutableLiveData<Resource<User>>()
    val profileUpdate: LiveData<Resource<User>> = _profileUpdate

    private val _avatarUpdate = MutableLiveData<Resource<User>>()
    val avatarUpdate: LiveData<Resource<User>> = _avatarUpdate

    private var token: String = ""

    fun init(bearerToken: String) {
        token = bearerToken
    }

    fun loadStats() {
        viewModelScope.launch {
            _stats.value = Resource.Loading
            _stats.value = userRepository.getStats(token)
        }
    }

    fun updateProfile(user: User) {
        viewModelScope.launch {
            _profileUpdate.value = Resource.Loading
            _profileUpdate.value = userRepository.updateProfile(token, user)
        }
    }

    fun uploadAvatar(part: MultipartBody.Part) {
        viewModelScope.launch {
            _avatarUpdate.value = Resource.Loading
            _avatarUpdate.value = userRepository.uploadAvatar(token, part)
        }
    }
}

class ProfileViewModelFactory(
    private val userRepository: UserRepository
) : androidx.lifecycle.ViewModelProvider.Factory {
    override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
        @Suppress("UNCHECKED_CAST")
        return ProfileViewModel(userRepository) as T
    }
}
