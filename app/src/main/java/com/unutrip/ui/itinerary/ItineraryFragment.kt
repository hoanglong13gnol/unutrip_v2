package com.unutrip.ui.itinerary

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import androidx.navigation.fragment.findNavController
import com.unutrip.R
import com.unutrip.data.api.RetrofitClient
import com.unutrip.data.repository.DestinationRepository
import com.unutrip.data.repository.ItineraryRepository
import com.unutrip.databinding.FragmentItineraryBinding
import com.unutrip.utils.Resource
import com.unutrip.utils.SessionManager
import com.unutrip.viewmodel.ItineraryViewModel
import com.unutrip.viewmodel.ItineraryViewModelFactory

class ItineraryFragment : Fragment() {

    private var _binding: FragmentItineraryBinding? = null
    private val binding get() = _binding!!
    private lateinit var viewModel: ItineraryViewModel
    private lateinit var sessionManager: SessionManager
    private lateinit var adapter: ItineraryListAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentItineraryBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        sessionManager = SessionManager.getInstance(requireContext())
        val itinRepo = ItineraryRepository(RetrofitClient.apiService)
        val destRepo = DestinationRepository(RetrofitClient.apiService)
        viewModel = ViewModelProvider(this, ItineraryViewModelFactory(itinRepo, destRepo))[ItineraryViewModel::class.java]
        viewModel.init(sessionManager.getBearerToken())

        setupAdapter()
        setupButtons()
        observeViewModel()

        if (findNavController().currentDestination?.id == R.id.profileItineraryListFragment) {
            binding.btnBack.visibility = View.VISIBLE
            binding.btnBack.setOnClickListener { findNavController().popBackStack() }
        }

        viewModel.loadItineraries()
    }

    private fun setupAdapter() {
        adapter = ItineraryListAdapter(
            onClick = { itinerary ->
                val bundle = Bundle().apply { putInt("itineraryId", itinerary.id) }
                val actionId = if (findNavController().currentDestination?.id == R.id.profileItineraryListFragment) {
                    R.id.action_profileItineraryListFragment_to_itineraryDetailFragment
                } else {
                    R.id.action_itineraryFragment_to_itineraryDetailFragment
                }
                findNavController().navigate(actionId, bundle)
            },
            onDelete = { itinerary -> viewModel.deleteItinerary(itinerary.id) }
        )
        binding.rvItineraries.adapter = adapter
    }

    private fun setupButtons() {
        binding.btnCreate.setOnClickListener { showCreateDialog() }
        binding.btnAISuggest.setOnClickListener {
            findNavController().navigate(R.id.action_itineraryFragment_to_aiItineraryRequestFragment)
        }
    }

    private fun showCreateDialog() {
        CreateItineraryDialog { title, desc, startDate, endDate ->
            viewModel.createItinerary(title, desc, startDate, endDate)
        }.show(parentFragmentManager, "create_itinerary")
    }

    private fun observeViewModel() {
        viewModel.itineraries.observe(viewLifecycleOwner) { result ->
            when (result) {
                is Resource.Loading -> binding.progressBar.visibility = View.VISIBLE
                is Resource.Success -> {
                    binding.progressBar.visibility = View.GONE
                    adapter.submitList(result.data.toList())
                    binding.tvCount.text = "${result.data.size} lịch trình"
                    binding.layoutEmpty.visibility = if (result.data.isEmpty()) View.VISIBLE else View.GONE
                    binding.rvItineraries.visibility = if (result.data.isNotEmpty()) View.VISIBLE else View.GONE
                }
                is Resource.Error -> {
                    binding.progressBar.visibility = View.GONE
                    Toast.makeText(context, result.message, Toast.LENGTH_SHORT).show()
                }
            }
        }

        viewModel.messages.observe(viewLifecycleOwner) { msg ->
            msg?.let {
                Toast.makeText(context, it, Toast.LENGTH_SHORT).show()
                viewModel.clearMessage()
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
