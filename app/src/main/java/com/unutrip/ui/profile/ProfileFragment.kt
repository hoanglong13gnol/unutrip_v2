package com.unutrip.ui.profile

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import androidx.navigation.fragment.findNavController
import com.bumptech.glide.Glide
import com.google.android.material.button.MaterialButton
import com.google.android.material.textfield.TextInputEditText
import com.unutrip.R
import com.unutrip.data.api.RetrofitClient
import com.unutrip.data.repository.UserRepository
import com.unutrip.databinding.FragmentProfileBinding
import com.unutrip.ui.auth.AuthActivity
import com.unutrip.utils.Resource
import com.unutrip.utils.SessionManager
import com.unutrip.viewmodel.ProfileViewModel
import com.unutrip.viewmodel.ProfileViewModelFactory
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import java.io.FileOutputStream

class ProfileFragment : Fragment() {

    private var _binding: FragmentProfileBinding? = null
    private val binding get() = _binding!!
    private lateinit var sessionManager: SessionManager
    private lateinit var viewModel: ProfileViewModel

    private val imagePicker = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { uploadAvatar(it) }
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentProfileBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        sessionManager = SessionManager.getInstance(requireContext())
        viewModel = ViewModelProvider(
            this,
            ProfileViewModelFactory(UserRepository(RetrofitClient.apiService))
        )[ProfileViewModel::class.java]
        viewModel.init(sessionManager.getBearerToken())

        bindUser(sessionManager.getUser())
        setupMenuItems()
        setupLogout()
        observeViewModel()

        binding.btnEditAvatar.setOnClickListener { imagePicker.launch("image/*") }
        viewModel.loadStats()
    }

    private fun bindUser(user: com.unutrip.data.model.User?) {
        user ?: return
        binding.tvName.text = user.fullName
        binding.tvEmail.text = user.email
        if (!user.avatar.isNullOrBlank()) {
            Glide.with(this)
                .load(user.avatar)
                .placeholder(R.drawable.ic_default_avatar)
                .circleCrop()
                .into(binding.ivAvatar)
        }
    }

    private fun observeViewModel() {
        viewModel.stats.observe(viewLifecycleOwner) { result ->
            if (result is Resource.Success) {
                binding.tvItineraryCount.text = result.data.itineraryCount.toString()
                binding.tvFavoriteCount.text = result.data.favoriteCount.toString()
                binding.tvReviewCount.text = result.data.reviewCount.toString()
            }
        }

        viewModel.profileUpdate.observe(viewLifecycleOwner) { result ->
            when (result) {
                is Resource.Success -> {
                    sessionManager.updateUser(result.data)
                    bindUser(result.data)
                    Toast.makeText(requireContext(), "Đã cập nhật thông tin", Toast.LENGTH_SHORT).show()
                }
                is Resource.Error -> Toast.makeText(requireContext(), result.message, Toast.LENGTH_SHORT).show()
                else -> {}
            }
        }

        viewModel.avatarUpdate.observe(viewLifecycleOwner) { result ->
            binding.ivAvatar.alpha = if (result is Resource.Loading) 0.5f else 1.0f
            when (result) {
                is Resource.Success -> {
                    sessionManager.updateUser(result.data)
                    bindUser(result.data)
                    Toast.makeText(requireContext(), "Đã cập nhật ảnh đại diện", Toast.LENGTH_SHORT).show()
                }
                is Resource.Error -> Toast.makeText(requireContext(), result.message, Toast.LENGTH_SHORT).show()
                else -> {}
            }
        }
    }

    private fun setupMenuItems() {
        binding.menuEditProfile.ivIcon.setImageResource(R.drawable.ic_edit)
        binding.menuEditProfile.tvLabel.text = "Chỉnh sửa hồ sơ"
        binding.menuEditProfile.root.setOnClickListener { showEditProfileDialog() }

        binding.menuFavorites.ivIcon.setImageResource(R.drawable.ic_favorite_filled)
        binding.menuFavorites.tvLabel.text = "Danh sách yêu thích"
        binding.menuFavorites.root.setOnClickListener {
            findNavController().navigate(R.id.profileFavoriteListFragment, Bundle().apply {
                putBoolean("isFavoriteOnly", true)
            })
        }

        binding.menuItineraries.ivIcon.setImageResource(R.drawable.ic_nav_itinerary)
        binding.menuItineraries.tvLabel.text = "Lịch trình của tôi"
        binding.menuItineraries.root.setOnClickListener {
            findNavController().navigate(R.id.profileItineraryListFragment)
        }

        binding.menuSettings.ivIcon.setImageResource(R.drawable.ic_more_vertical)
        binding.menuSettings.tvLabel.text = "Cài đặt"
        binding.menuSettings.root.setOnClickListener {
            findNavController().navigate(R.id.action_profileFragment_to_settingsFragment)
        }
    }

    private fun showEditProfileDialog() {
        val user = sessionManager.getUser() ?: return
        val dialogView = layoutInflater.inflate(R.layout.dialog_edit_profile, null)
        val etFullName = dialogView.findViewById<TextInputEditText>(R.id.etFullName)
        val etPhone = dialogView.findViewById<TextInputEditText>(R.id.etPhone)
        val btnCancel = dialogView.findViewById<MaterialButton>(R.id.btnCancel)
        val btnSave = dialogView.findViewById<MaterialButton>(R.id.btnSave)

        etFullName.setText(user.fullName)
        etPhone.setText(user.phone ?: "")

        val dialog = android.app.AlertDialog.Builder(requireContext())
            .setView(dialogView)
            .create()
        dialog.window?.setBackgroundDrawableResource(android.R.color.transparent)

        btnCancel.setOnClickListener { dialog.dismiss() }
        btnSave.setOnClickListener {
            val newName = etFullName.text.toString().trim()
            if (newName.isEmpty()) {
                etFullName.error = "Vui lòng nhập họ tên"
                return@setOnClickListener
            }
            viewModel.updateProfile(user.copy(fullName = newName, phone = etPhone.text.toString().trim()))
            dialog.dismiss()
        }
        dialog.show()
    }

    private fun uploadAvatar(uri: android.net.Uri) {
        try {
            val file = getFileFromUri(uri)
            val requestFile = file.asRequestBody("image/*".toMediaTypeOrNull())
            val body = MultipartBody.Part.createFormData("avatar", file.name, requestFile)
            viewModel.uploadAvatar(body)
        } catch (e: Exception) {
            Toast.makeText(requireContext(), "Lỗi: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }

    private fun getFileFromUri(uri: android.net.Uri): File {
        val inputStream = requireContext().contentResolver.openInputStream(uri)
        val file = File(requireContext().cacheDir, "temp_avatar_${System.currentTimeMillis()}.jpg")
        inputStream?.use { input ->
            FileOutputStream(file).use { output -> input.copyTo(output) }
        }
        return file
    }

    private fun setupLogout() {
        binding.btnLogout.setOnClickListener {
            android.app.AlertDialog.Builder(requireContext())
                .setTitle("Đăng xuất")
                .setMessage("Bạn có chắc muốn đăng xuất không?")
                .setPositiveButton("Đăng xuất") { _, _ ->
                    sessionManager.clearSession()
                    startActivity(Intent(requireContext(), AuthActivity::class.java).apply {
                        flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                    })
                }
                .setNegativeButton("Hủy", null)
                .show()
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
