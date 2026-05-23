import {
  createItineraryFromAiOption,
  createItineraryFromAiSelection
} from "../../services/itineraries.service.js";

export async function createFromOption(req, res) {
  try {
    const { title, startDate, endDate, days } = req.body;

    if (!title || !startDate || !endDate) {
      return res.status(400).json({
        success: false,
        message: "Thiếu tên lịch trình hoặc ngày đi/ngày về",
        data: null
      });
    }

    if (!Array.isArray(days) || days.length === 0) {
      return res.status(400).json({
        success: false,
        message: "Tour chưa có danh sách ngày/địa điểm",
        data: null
      });
    }

    const result = await createItineraryFromAiOption({
      userId: req.user.userId,
      payload: req.body
    });

    if (!result.ok && result.reason === "no_mapped_destinations") {
      return res.status(400).json({
        success: false,
        message: "Không map được địa điểm nào sang app_places.id",
        data: {
          optionId: result.optionId ?? null,
          unresolved: result.unresolved
        }
      });
    }

    if (!result.ok && result.reason === "invalid_dates") {
      return res.status(400).json({
        success: false,
        message: "Ngày đi/ngày về không hợp lệ",
        data: null
      });
    }

    return res.json({
      success: true,
      message: "Tạo lịch trình từ tour AI thành công",
      data: result.data
    });
  } catch (error) {
    console.error("[CREATE_FROM_OPTION_ERROR]", error);

    return res.status(500).json({
      success: false,
      message: "Lỗi tạo lịch trình từ tour AI: " + error.message,
      data: null
    });
  }
}

export async function createFromSelection(req, res) {
  try {
    const { title, startDate, endDate } = req.body;

    if (!title || !startDate || !endDate) {
      return res.status(400).json({
        success: false,
        message: "Thiếu tên lịch trình hoặc ngày đi/ngày về",
        data: null
      });
    }

    const result = await createItineraryFromAiSelection({
      userId: req.user.userId,
      payload: req.body
    });

    if (!result.ok && result.reason === "no_mapped_destinations") {
      return res.status(400).json({
        success: false,
        message: "Không map được địa điểm nào sang app_places.id",
        data: {
          receivedSelectedDestinations: result.receivedSelectedDestinations ?? null,
          receivedSelectedDestinationIds: result.receivedSelectedDestinationIds ?? null,
          unresolved: result.unresolved
        }
      });
    }

    if (!result.ok && result.reason === "invalid_dates") {
      return res.status(400).json({
        success: false,
        message: "Ngày đi/ngày về không hợp lệ",
        data: null
      });
    }

    return res.json({
      success: true,
      message: "Tạo lịch trình từ AI gợi ý thành công",
      data: result.data
    });
  } catch (error) {
    console.error("[CREATE_FROM_SELECTION_ERROR]", error);

    return res.status(500).json({
      success: false,
      message: "Lỗi tạo lịch trình từ lựa chọn: " + error.message,
      data: null
    });
  }
}
