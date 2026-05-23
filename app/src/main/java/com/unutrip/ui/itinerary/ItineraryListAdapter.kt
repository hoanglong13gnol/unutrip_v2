package com.unutrip.ui.itinerary

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.PopupMenu
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.unutrip.data.model.Itinerary
import com.unutrip.databinding.ItemItineraryBinding
import java.text.SimpleDateFormat
import java.util.Locale

class ItineraryListAdapter(
    private val onClick: (Itinerary) -> Unit,
    private val onDelete: (Itinerary) -> Unit
) : ListAdapter<Itinerary, ItineraryListAdapter.ViewHolder>(DiffCallback()) {

    inner class ViewHolder(private val binding: ItemItineraryBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(itinerary: Itinerary) {
            binding.tvTitle.text = itinerary.title
            binding.tvDuration.text = "${itinerary.totalDays} ngày"

            try {
                val inputFmt = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
                val outputFmt = SimpleDateFormat("dd/MM", Locale.getDefault())
                val start = inputFmt.parse(itinerary.startDate)
                val end = inputFmt.parse(itinerary.endDate)
                binding.tvDates.text =
                    "${start?.let { outputFmt.format(it) }} - ${end?.let { outputFmt.format(it) }}"
            } catch (_: Exception) {
                binding.tvDates.text = "${itinerary.startDate} - ${itinerary.endDate}"
            }

            itinerary.estimatedBudget?.let { budget ->
                binding.tvBudget.text = "Ngân sách: ${String.format("%,.0f", budget)}đ"
                binding.layoutBudget.visibility = View.VISIBLE
            } ?: run {
                binding.layoutBudget.visibility = View.GONE
            }

            binding.tvStatus.text = when (itinerary.status) {
                "planned" -> "Đã lên kế hoạch"
                "completed" -> "Hoàn thành"
                "cancelled" -> "Đã hủy"
                else -> "Nháp"
            }

            binding.tvAIBadge.visibility = View.GONE
            binding.root.setOnClickListener { onClick(itinerary) }
            binding.btnMore.setOnClickListener { view ->
                PopupMenu(view.context, view).apply {
                    menu.add("Xóa lịch trình")
                    setOnMenuItemClickListener {
                        onDelete(itinerary)
                        true
                    }
                }.show()
            }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemItineraryBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) = holder.bind(getItem(position))

    private class DiffCallback : DiffUtil.ItemCallback<Itinerary>() {
        override fun areItemsTheSame(a: Itinerary, b: Itinerary) = a.id == b.id
        override fun areContentsTheSame(a: Itinerary, b: Itinerary) = a == b
    }
}
