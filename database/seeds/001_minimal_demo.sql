-- Minimal demo places when legacy bootstrap did not populate app_places.
-- Safe to re-run: INSERT IGNORE + only used when app_places is empty (see run_migrations.sh).
--
-- Demo credentials: use any user from legacy `users` table after DATABASE_BOOTSTRAP_LEGACY,
-- or register via POST /api/auth/register on a fresh stack.

SET NAMES utf8mb4;

INSERT IGNORE INTO `app_places` (
  `id`,
  `place_key`,
  `name`,
  `description`,
  `city`,
  `province`,
  `latitude`,
  `longitude`,
  `category`,
  `tags_json`,
  `rating`,
  `review_count`,
  `is_active`
) VALUES
  (9001, 'DEMO_9001', 'Bãi Dài Cam Ranh (demo)', 'Bãi biển demo cho Compose stack.', 'Cam Ranh', 'Khánh Hòa', 12.0616, 109.2052, 'beach', '["biển","demo"]', 4.50, 10, 1),
  (9002, 'DEMO_9002', 'Tháp Bà Ponagar (demo)', 'Di tích Chăm demo.', 'Nha Trang', 'Khánh Hòa', 12.26528, 109.1953, 'heritage', '["văn hóa","demo"]', 4.20, 5, 1),
  (9003, 'DEMO_9003', 'Suối Ba Hồ (demo)', 'Suối núi demo.', 'Nha Trang', 'Khánh Hòa', 12.3725, 109.1218, 'nature', '["suối","demo"]', 4.00, 3, 1),
  (9004, 'DEMO_9004', 'Chợ đêm Nha Trang (demo)', 'Ẩm thực đêm demo.', 'Nha Trang', 'Khánh Hòa', 12.2388, 109.1967, 'food', '["ăn uống","demo"]', 4.30, 8, 1),
  (9005, 'DEMO_9005', 'VinWonders (demo)', 'Công viên giải trí demo.', 'Nha Trang', 'Khánh Hòa', 12.21673, 109.23996, 'checkin', '["vui chơi","demo"]', 4.60, 12, 1);
