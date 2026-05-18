-- UNUtrip v2 - Migration 011
-- Purpose: Đảm bảo có đủ bảng lịch trình (itineraries / itinerary_days / itinerary_items) trên DB chỉ được nạp
--          một phần (ví dụ có app_places nhưng thiếu itinerary_items → ER_NO_SUCH_TABLE).
-- Prerequisites:
--   - Đã có bảng `users` và `app_places` (id trùng không gian với destinations cũ / quick populate).
-- Safety:
--   - CREATE TABLE IF NOT EXISTS — chạy lại không xóa dữ liệu.
--
-- Ghi chú: `itinerary_items.destination_id` tham chiếu `app_places.id` (Phase 2B Node join app_places).

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `itineraries` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `title` text NOT NULL,
  `description` text DEFAULT NULL,
  `start_date` varchar(50) NOT NULL,
  `end_date` varchar(50) NOT NULL,
  `total_days` int(11) NOT NULL,
  `status` varchar(50) NOT NULL DEFAULT 'planned',
  `estimated_budget` double DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_iti_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `itinerary_days` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `itinerary_id` int(11) NOT NULL,
  `day_number` int(11) NOT NULL,
  `date` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_itinerary_days_itinerary_id` (`itinerary_id`),
  CONSTRAINT `fk_day_iti` FOREIGN KEY (`itinerary_id`) REFERENCES `itineraries` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `itinerary_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `day_id` int(11) NOT NULL,
  `destination_id` int(11) NOT NULL,
  `start_time` varchar(20) NOT NULL,
  `end_time` varchar(20) NOT NULL,
  `note` text DEFAULT NULL,
  `order_index` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_itinerary_items_day_id` (`day_id`),
  KEY `idx_itinerary_items_destination_id` (`destination_id`),
  CONSTRAINT `fk_item_day` FOREIGN KEY (`day_id`) REFERENCES `itinerary_days` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_item_app_place` FOREIGN KEY (`destination_id`) REFERENCES `app_places` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
