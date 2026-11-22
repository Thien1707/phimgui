-- PHIMHAY-GUI — Khởi tạo schema MySQL (chưa tự chạy; dùng qua MySQL Workbench)
-- Charset: utf8mb4

CREATE DATABASE IF NOT EXISTS phimhay_gui
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE phimhay_gui;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  display_name VARCHAR(100) NOT NULL,
  phone_number VARCHAR(32) NOT NULL DEFAULT '',
  date_of_birth DATE NULL,
  gender VARCHAR(32) NOT NULL DEFAULT '',
  role ENUM('user','moderator','admin') NOT NULL DEFAULT 'user',
  is_vip TINYINT(1) NOT NULL DEFAULT 0,
  vip_expires_at DATETIME NULL,
  is_unlimited_vip TINYINT(1) NOT NULL DEFAULT 0,
  banned TINYINT(1) NOT NULL DEFAULT 0,
  last_login DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email),
  UNIQUE KEY uq_users_display_name (display_name),
  KEY idx_users_role (role),
  KEY idx_users_banned (banned)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS movies (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  slug VARCHAR(255) NOT NULL,
  title VARCHAR(512) NOT NULL,
  origin_name VARCHAR(512) NOT NULL DEFAULT '',
  poster_url TEXT,
  thumb_url TEXT,
  year SMALLINT NULL,
  type VARCHAR(64) NOT NULL DEFAULT '',
  content MEDIUMTEXT,
  country VARCHAR(255) NOT NULL DEFAULT '',
  series_id BIGINT UNSIGNED NULL,
  part_number INT NULL,
  view_status TINYINT NOT NULL DEFAULT 0,
  comment_rating_policy ENUM('public','members') NOT NULL DEFAULT 'public',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  external_id VARCHAR(64) NOT NULL DEFAULT '',
  view_count INT UNSIGNED NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_movies_slug (slug),
  KEY idx_movies_active_updated (is_active, updated_at),
  KEY idx_movies_series (series_id),
  CONSTRAINT fk_movies_series FOREIGN KEY (series_id) REFERENCES movies(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS categories (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  display_name VARCHAR(150) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_categories_name (name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS movie_categories (
  movie_id BIGINT UNSIGNED NOT NULL,
  category_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (movie_id, category_id),
  CONSTRAINT fk_mc_movie FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
  CONSTRAINT fk_mc_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS comments (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  movie_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  body VARCHAR(2000) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_comments_movie_created (movie_id, created_at),
  CONSTRAINT fk_comments_movie FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
  CONSTRAINT fk_comments_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ratings (
  movie_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  stars TINYINT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (movie_id, user_id),
  CONSTRAINT chk_ratings_stars CHECK (stars BETWEEN 1 AND 5),
  CONSTRAINT fk_ratings_movie FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
  CONSTRAINT fk_ratings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS watch_history (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  movie_id BIGINT UNSIGNED NOT NULL,
  episode INT NOT NULL DEFAULT 1,
  current_time_sec INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_history_user_movie_ep (user_id, movie_id, episode),
  KEY idx_history_user_updated (user_id, updated_at),
  CONSTRAINT fk_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_history_movie FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS payments (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  txn_ref VARCHAR(64) NOT NULL,
  amount INT NOT NULL,
  status ENUM('pending','success','failed') NOT NULL DEFAULT 'pending',
  vnp_response JSON NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_payments_txn (txn_ref),
  CONSTRAINT fk_payments_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS movie_views (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NULL,
  movie_id BIGINT UNSIGNED NOT NULL,
  ip_address VARCHAR(45) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_views_movie_created (movie_id, created_at),
  KEY idx_views_created (created_at),
  CONSTRAINT fk_views_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT fk_views_movie FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS activity_logs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  actor_id BIGINT UNSIGNED NULL,
  actor_role VARCHAR(32) NOT NULL DEFAULT 'guest',
  action VARCHAR(64) NOT NULL,
  target_type VARCHAR(32) NOT NULL DEFAULT '',
  target_id VARCHAR(64) NOT NULL DEFAULT '',
  metadata JSON NULL,
  ip_address VARCHAR(45) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_logs_action_created (action, created_at),
  KEY idx_logs_created (created_at),
  CONSTRAINT fk_logs_actor FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS system_settings (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  setting_key VARCHAR(32) NOT NULL DEFAULT 'global',
  site_name VARCHAR(128) NOT NULL DEFAULT 'PHIMHAY',
  logo TEXT,
  banner_images JSON NULL,
  maintenance_mode TINYINT(1) NOT NULL DEFAULT 0,
  registration_enabled TINYINT(1) NOT NULL DEFAULT 1,
  comments_enabled TINYINT(1) NOT NULL DEFAULT 1,
  email_config JSON NULL,
  third_party_api_keys JSON NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_settings_key (setting_key)
) ENGINE=InnoDB;

INSERT INTO system_settings (setting_key, site_name)
VALUES ('global', 'PHIMHAY-GUI')
ON DUPLICATE KEY UPDATE site_name = site_name;

INSERT INTO categories (name, display_name) VALUES
  ('hoathinh', 'Hoạt Hình'),
  ('series', 'Phim bộ'),
  ('single', 'Phim lẻ')
ON DUPLICATE KEY UPDATE display_name = VALUES(display_name);

-- Admin mẫu: email admin@local.test / display_name admin
-- Mật khẩu plaintext mục tiêu: Admin@123 — THAY hash bằng bcrypt thật khi seed từ Flask
-- Hash dưới đây là placeholder; chạy script seed trong Phase 4
-- INSERT INTO users (...) VALUES (...);
