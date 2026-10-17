-- ==========================================================
-- SUPABASE POSTGRESQL SCHEMA & INITIAL DATA
-- HOU-S-RIMS Management System
-- Hướng dẫn: Copy toàn bộ nội dung file này và paste vào
-- Supabase Dashboard -> SQL Editor -> Nhấn 'Run'
-- ==========================================================

-- 1. XÓA CÁC BẢNG CŨ (NẾU CÓ)
DROP TABLE IF EXISTS "experiences" CASCADE;
DROP TABLE IF EXISTS "achievements" CASCADE;
DROP TABLE IF EXISTS "skills" CASCADE;
DROP TABLE IF EXISTS "evaluations" CASCADE;
DROP TABLE IF EXISTS "rubrics" CASCADE;
DROP TABLE IF EXISTS "documents" CASCADE;
DROP TABLE IF EXISTS "notifications" CASCADE;
DROP TABLE IF EXISTS "messages" CASCADE;
DROP TABLE IF EXISTS "meetings" CASCADE;
DROP TABLE IF EXISTS "submissions" CASCADE;
DROP TABLE IF EXISTS "progresses" CASCADE;
DROP TABLE IF EXISTS "milestones" CASCADE;
DROP TABLE IF EXISTS "topic_registrations" CASCADE;
DROP TABLE IF EXISTS "topics" CASCADE;
DROP TABLE IF EXISTS "group_members" CASCADE;
DROP TABLE IF EXISTS "groups" CASCADE;
DROP TABLE IF EXISTS "council_members" CASCADE;
DROP TABLE IF EXISTS "councils" CASCADE;
DROP TABLE IF EXISTS "batches" CASCADE;
DROP TABLE IF EXISTS "users" CASCADE;

CREATE TABLE users (
	id SERIAL NOT NULL, 
	username VARCHAR(50) NOT NULL, 
	password_hash TEXT NOT NULL, 
	full_name VARCHAR(100) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	phone VARCHAR(20), 
	bio TEXT, 
	role VARCHAR(20) NOT NULL, 
	student_id VARCHAR(20), 
	faculty VARCHAR(100), 
	PRIMARY KEY (id), 
	UNIQUE (username), 
	UNIQUE (email)
);

CREATE TABLE batches (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	type VARCHAR(50), 
	start_date TIMESTAMP WITHOUT TIME ZONE, 
	end_date TIMESTAMP WITHOUT TIME ZONE, 
	submission_deadline TIMESTAMP WITHOUT TIME ZONE, 
	status VARCHAR(20), 
	academic_year VARCHAR(20), 
	guidance_doc VARCHAR(255), 
	description TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE TABLE councils (
	id SERIAL NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	decision_number VARCHAR(100), 
	meeting_date DATE, 
	meeting_time TIME WITHOUT TIME ZONE, 
	location VARCHAR(255), 
	decision_file_url TEXT, 
	batch_id INTEGER NOT NULL, 
	established_date TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(batch_id) REFERENCES batches (id)
);

CREATE TABLE council_members (
	id SERIAL NOT NULL, 
	council_id INTEGER NOT NULL, 
	mentor_id INTEGER NOT NULL, 
	role VARCHAR(50), 
	PRIMARY KEY (id), 
	FOREIGN KEY(council_id) REFERENCES councils (id), 
	FOREIGN KEY(mentor_id) REFERENCES users (id)
);

CREATE TABLE groups (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	batch_id INTEGER, 
	leader_id INTEGER NOT NULL, 
	mentor_id INTEGER, 
	status VARCHAR(20), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(batch_id) REFERENCES batches (id), 
	FOREIGN KEY(leader_id) REFERENCES users (id), 
	FOREIGN KEY(mentor_id) REFERENCES users (id)
);

CREATE TABLE group_members (
	id SERIAL NOT NULL, 
	group_id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	status VARCHAR(20), 
	PRIMARY KEY (id), 
	FOREIGN KEY(group_id) REFERENCES groups (id), 
	FOREIGN KEY(student_id) REFERENCES users (id)
);

CREATE TABLE topics (
	id SERIAL NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	description TEXT, 
	batch_id INTEGER, 
	mentor_id INTEGER, 
	group_id INTEGER, 
	council_id INTEGER, 
	presentation_time VARCHAR(20), 
	status VARCHAR(20), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(batch_id) REFERENCES batches (id), 
	FOREIGN KEY(mentor_id) REFERENCES users (id), 
	FOREIGN KEY(group_id) REFERENCES groups (id), 
	FOREIGN KEY(council_id) REFERENCES councils (id)
);

CREATE TABLE topic_registrations (
	id SERIAL NOT NULL, 
	topic_id INTEGER NOT NULL, 
	group_id INTEGER NOT NULL, 
	mentor_id INTEGER NOT NULL, 
	status VARCHAR(20), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(topic_id) REFERENCES topics (id), 
	FOREIGN KEY(group_id) REFERENCES groups (id), 
	FOREIGN KEY(mentor_id) REFERENCES users (id)
);

CREATE TABLE milestones (
	id SERIAL NOT NULL, 
	topic_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	deadline TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	description TEXT, 
	status VARCHAR(20), 
	PRIMARY KEY (id), 
	FOREIGN KEY(topic_id) REFERENCES topics (id)
);

CREATE TABLE progresses (
	id SERIAL NOT NULL, 
	milestone_id INTEGER NOT NULL, 
	percentage INTEGER, 
	notes TEXT, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(milestone_id) REFERENCES milestones (id)
);

CREATE TABLE submissions (
	id SERIAL NOT NULL, 
	topic_id INTEGER NOT NULL, 
	milestone_id INTEGER, 
	uploader_id INTEGER NOT NULL, 
	file_url VARCHAR(255) NOT NULL, 
	type VARCHAR(50) NOT NULL, 
	submitted_at TIMESTAMP WITHOUT TIME ZONE, 
	feedback TEXT, 
	feedback_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(topic_id) REFERENCES topics (id), 
	FOREIGN KEY(milestone_id) REFERENCES milestones (id), 
	FOREIGN KEY(uploader_id) REFERENCES users (id)
);

CREATE TABLE meetings (
	id SERIAL NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	description TEXT, 
	start_time TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	end_time TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	organizer_id INTEGER NOT NULL, 
	topic_id INTEGER, 
	status VARCHAR(20), 
	PRIMARY KEY (id), 
	FOREIGN KEY(organizer_id) REFERENCES users (id), 
	FOREIGN KEY(topic_id) REFERENCES topics (id)
);

CREATE TABLE messages (
	id SERIAL NOT NULL, 
	sender_id INTEGER NOT NULL, 
	receiver_id INTEGER, 
	group_id INTEGER, 
	content TEXT NOT NULL, 
	message_type VARCHAR(20), 
	file_url VARCHAR(255), 
	file_name VARCHAR(255), 
	meta_data VARCHAR(500), 
	is_read BOOLEAN, 
	read_at TIMESTAMP WITHOUT TIME ZONE, 
	timestamp TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(sender_id) REFERENCES users (id), 
	FOREIGN KEY(receiver_id) REFERENCES users (id), 
	FOREIGN KEY(group_id) REFERENCES groups (id)
);

CREATE TABLE notifications (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	content TEXT NOT NULL, 
	is_read BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE documents (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	file_url VARCHAR(255) NOT NULL, 
	type VARCHAR(50), 
	PRIMARY KEY (id)
);

CREATE TABLE rubrics (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	criteria_json TEXT NOT NULL, 
	total_score FLOAT NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE evaluations (
	id SERIAL NOT NULL, 
	council_id INTEGER NOT NULL, 
	topic_id INTEGER NOT NULL, 
	rubric_id INTEGER NOT NULL, 
	score FLOAT NOT NULL, 
	comments TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(council_id) REFERENCES councils (id), 
	FOREIGN KEY(topic_id) REFERENCES topics (id), 
	FOREIGN KEY(rubric_id) REFERENCES rubrics (id)
);

CREATE TABLE skills (
	id SERIAL NOT NULL, 
	student_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES users (id)
);

CREATE TABLE achievements (
	id SERIAL NOT NULL, 
	student_id INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	year VARCHAR(20), 
	description TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES users (id)
);

CREATE TABLE experiences (
	id SERIAL NOT NULL, 
	student_id INTEGER NOT NULL, 
	project_name VARCHAR(200) NOT NULL, 
	role VARCHAR(100), 
	duration VARCHAR(100), 
	description TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES users (id)
);



-- 2. INSERT DỮ LIỆU BAN ĐẦU

-- Dữ liệu bảng users (8 dòng)
INSERT INTO "users" ("id", "username", "password_hash", "full_name", "email", "phone", "bio", "role", "student_id", "faculty") VALUES (1, 'admin', 'scrypt:32768:8:1$jWMtvzx7D3bryYrM$343f83706c193febaaed591f83571e9756b64f339978147afb858a76222e05cd4a58513abdcca60327f876ad19b9462a4f61e9c46f99f7901867df7bd8b4203e', 'Admin Truong HOU', 'admin@hou.edu.vn', NULL, NULL, 'admin', NULL, 'Phong Quan ly NCKH');
INSERT INTO "users" ("id", "username", "password_hash", "full_name", "email", "phone", "bio", "role", "student_id", "faculty") VALUES (2, 'faculty1', 'scrypt:32768:8:1$NZcMmur13pqgkGSQ$59320e782f221e25cf5c7bd5faa5a6989ad5b493a3af7966190ab46507f3ba3a5bb7823afd74b1a398803def2a09b761578bca1ff144bce08e0b59d80bae0483', 'PGS.TS Khoa CNTT', 'faculty@hou.edu.vn', NULL, NULL, 'faculty', NULL, 'Khoa CNTT');
INSERT INTO "users" ("id", "username", "password_hash", "full_name", "email", "phone", "bio", "role", "student_id", "faculty") VALUES (3, 'lecturer1', 'scrypt:32768:8:1$qh9rUzY4POgF8Ofz$09053eaa6c8e13be29f332615c7bb3d9993f5eeab1e0bfd23e65732c80d11237e0cbf71cbf5725b5d0882b3e5e964ae3a5d683da44eea7a7c56cc00ea036a9ec', 'TS. Nguyen Van A', 'nva@hou.edu.vn', NULL, NULL, 'Lecturer', NULL, 'Khoa CNTT');
INSERT INTO "users" ("id", "username", "password_hash", "full_name", "email", "phone", "bio", "role", "student_id", "faculty") VALUES (4, 'lecturer2', 'scrypt:32768:8:1$bdyi79gYAVSBX2ez$7b6d07bf4fa889af45262a5b17d5ce8cb9262bfd3ad2e36c64ed98653b6524c0dbc4fc8a6c15e677de750cc0764a61848d13c9428daf81d6edd448407d52d864', 'ThS. Le Thi B', 'ltb@hou.edu.vn', NULL, NULL, 'Lecturer', NULL, 'Khoa Luat');
INSERT INTO "users" ("id", "username", "password_hash", "full_name", "email", "phone", "bio", "role", "student_id", "faculty") VALUES (5, 'student1', 'scrypt:32768:8:1$1bNp43h9Hf7CxgaU$b711678bdf0856fae60e57285c41211154abe0b319f89458baf09a42348580e0caaee9f6d27f34af80782dcc14ed16e4e9042e740b1ed4f9c32d6c8816a915b7', 'Nguyễn Hà Phương', 'kaz442197@gmail.com', 'None', 'None', 'student', '24A1001D0341', 'Khoa CNTT');
INSERT INTO "users" ("id", "username", "password_hash", "full_name", "email", "phone", "bio", "role", "student_id", "faculty") VALUES (6, 'student2', 'scrypt:32768:8:1$y3gohMeMwpoCa7u8$ea91530f2711a915c8a0b90d916d18b2ce780b600554e693621799458d64b6a877191a53b5aed22a685b892e2b9de4967221dc2c0d231235c27b81854cfce743', 'Nguyen Van Hoc', 'nvh@hou.edu.vn', NULL, NULL, 'student', '24A1001D0342', 'Khoa CNTT');
INSERT INTO "users" ("id", "username", "password_hash", "full_name", "email", "phone", "bio", "role", "student_id", "faculty") VALUES (7, 'student3', 'scrypt:32768:8:1$TN4sQmw3LhGPnUDy$6930c3e7b9c34fe66d2b56582467b08d5ad43b317a25fc583cd1fad79231f635bbd194a7687d8d10275187e515cf534b204ab2a974a7ea52cb04aa1a638d69c9', 'Le Thi Lan', 'ltlan@hou.edu.vn', NULL, NULL, 'student', '24A1001D0343', 'Khoa CNTT');
INSERT INTO "users" ("id", "username", "password_hash", "full_name", "email", "phone", "bio", "role", "student_id", "faculty") VALUES (8, 'lecturer3', 'mock_hash', 'Giảng viên 3', 'lecturer3@hou.edu.vn', NULL, NULL, 'Lecturer', NULL, 'CNTT');
SELECT setval(pg_get_serial_sequence('"users"', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM "users";

-- Dữ liệu bảng batches (2 dòng)
INSERT INTO "batches" ("id", "name", "type", "start_date", "end_date", "submission_deadline", "status", "created_at", "academic_year", "guidance_doc", "description") VALUES (3, 'NCKH 11', 'NCKH Standard', '2026-10-01 00:00:00.000000', NULL, '2026-10-02 00:00:00.000000', 'hidden', '2026-10-01 01:41:47.029997', '2025-2026', 'E-Menu Project.pdf', 'ff');
INSERT INTO "batches" ("id", "name", "type", "start_date", "end_date", "submission_deadline", "status", "created_at", "academic_year", "guidance_doc", "description") VALUES (10, 'gagagaga', 'NCKH Standard', '2026-10-08 00:00:00.000000', '2026-10-10 00:00:00.000000', '2026-10-09 00:00:00.000000', 'active', '2026-10-08 02:05:26.851079', '2025-2026', 'GiuaKy-DamBaoCLPM_1.pdf|BTL_-_AN_NINH_BAO_MAT_DU_LIEU_4.docx|downloads_PhanCongBTL_KiemSoatTruyCap_TMDT_1.xlsx', '<p>kk<strong>kkkkk</strong>	<strong><em>kkk<u>kk</u></em></strong>		vg<s>ggggg</s></p><p><s>ggg</s>						ggggggggg<em>ggggg</em></p>');
SELECT setval(pg_get_serial_sequence('"batches"', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM "batches";

-- Dữ liệu bảng groups (4 dòng)
INSERT INTO "groups" ("id", "name", "batch_id", "leader_id", "mentor_id", "status", "created_at") VALUES (1, 'Nhóm của Tran Minh Tuan', NULL, 5, NULL, 'draft', NULL);
INSERT INTO "groups" ("id", "name", "batch_id", "leader_id", "mentor_id", "status", "created_at") VALUES (2, 'Nhóm ID: 7', 3, 7, NULL, 'draft', NULL);
INSERT INTO "groups" ("id", "name", "batch_id", "leader_id", "mentor_id", "status", "created_at") VALUES (3, 'Nhóm ID: 5', 10, 5, NULL, 'draft', NULL);
INSERT INTO "groups" ("id", "name", "batch_id", "leader_id", "mentor_id", "status", "created_at") VALUES (4, 'Nhóm Thử Nghiệm NCKH AI', 10, 5, 3, 'pending_mentor', '2026-10-14 11:44:52.322899');
SELECT setval(pg_get_serial_sequence('"groups"', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM "groups";

-- Dữ liệu bảng group_members (8 dòng)
INSERT INTO "group_members" ("id", "group_id", "student_id", "status") VALUES (1, 1, 5, 'accepted');
INSERT INTO "group_members" ("id", "group_id", "student_id", "status") VALUES (2, 2, 7, 'accepted');
INSERT INTO "group_members" ("id", "group_id", "student_id", "status") VALUES (3, 2, 5, 'accepted');
INSERT INTO "group_members" ("id", "group_id", "student_id", "status") VALUES (4, 3, 5, 'accepted');
INSERT INTO "group_members" ("id", "group_id", "student_id", "status") VALUES (5, 3, 6, 'accepted');
INSERT INTO "group_members" ("id", "group_id", "student_id", "status") VALUES (6, 3, 7, 'accepted');
INSERT INTO "group_members" ("id", "group_id", "student_id", "status") VALUES (7, 4, 5, 'joined');
INSERT INTO "group_members" ("id", "group_id", "student_id", "status") VALUES (8, 4, 6, 'invited');
SELECT setval(pg_get_serial_sequence('"group_members"', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM "group_members";

-- Dữ liệu bảng topics (3 dòng)
INSERT INTO "topics" ("id", "title", "description", "batch_id", "mentor_id", "group_id", "status", "created_at", "council_id", "presentation_time") VALUES (1, 'ee', 'hhh', 3, 3, 1, 'approved', '2026-10-01 04:33:58.024511', NULL, NULL);
INSERT INTO "topics" ("id", "title", "description", "batch_id", "mentor_id", "group_id", "status", "created_at", "council_id", "presentation_time") VALUES (2, 'ưtgagag', 'agagag', 3, 3, 2, 'approved', '2026-10-01 05:21:24.146029', NULL, NULL);
INSERT INTO "topics" ("id", "title", "description", "batch_id", "mentor_id", "group_id", "status", "created_at", "council_id", "presentation_time") VALUES (3, 'ggg', 'gggg', 10, 3, 3, 'approved', '2026-10-08 02:19:19.614644', NULL, NULL);
SELECT setval(pg_get_serial_sequence('"topics"', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM "topics";

-- Dữ liệu bảng topic_registrations (3 dòng)
INSERT INTO "topic_registrations" ("id", "topic_id", "group_id", "mentor_id", "status", "created_at") VALUES (1, 1, 1, 3, 'pending', '2026-10-01 04:33:58.027343');
INSERT INTO "topic_registrations" ("id", "topic_id", "group_id", "mentor_id", "status", "created_at") VALUES (2, 2, 2, 3, 'pending', '2026-10-01 05:21:24.147260');
INSERT INTO "topic_registrations" ("id", "topic_id", "group_id", "mentor_id", "status", "created_at") VALUES (3, 3, 3, 3, 'pending', '2026-10-08 02:19:19.615893');
SELECT setval(pg_get_serial_sequence('"topic_registrations"', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM "topic_registrations";

-- Dữ liệu bảng milestones (3 dòng)
INSERT INTO "milestones" ("id", "topic_id", "name", "deadline", "description", "status") VALUES (1, 2, 'fafa', '2026-10-01 00:00:00.000000', '', 'pending');
INSERT INTO "milestones" ("id", "topic_id", "name", "deadline", "description", "status") VALUES (2, 3, 'gg', '2026-10-09 00:00:00.000000', '', 'pending');
INSERT INTO "milestones" ("id", "topic_id", "name", "deadline", "description", "status") VALUES (3, 3, 'ff', '2026-10-10 00:00:00.000000', '', 'pending');
SELECT setval(pg_get_serial_sequence('"milestones"', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM "milestones";

-- Dữ liệu bảng progresses (3 dòng)
INSERT INTO "progresses" ("id", "milestone_id", "percentage", "notes", "updated_at") VALUES (1, 1, 30, '', '2026-10-01 05:25:13.734817');
INSERT INTO "progresses" ("id", "milestone_id", "percentage", "notes", "updated_at") VALUES (2, 2, 100, '', '2026-10-08 03:36:54.727261');
INSERT INTO "progresses" ("id", "milestone_id", "percentage", "notes", "updated_at") VALUES (3, 3, 80, '', '2026-10-08 03:36:59.818325');
SELECT setval(pg_get_serial_sequence('"progresses"', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM "progresses";

-- Dữ liệu bảng submissions (6 dòng)
INSERT INTO "submissions" ("id", "topic_id", "uploader_id", "file_url", "type", "submitted_at", "milestone_id", "feedback", "feedback_at") VALUES (1, 1, 5, 'D:\HOU-S-RIMS\uploads\BT3_1.pdf', 'report', '2026-09-24 03:01:35.648692', NULL, NULL, NULL);
INSERT INTO "submissions" ("id", "topic_id", "uploader_id", "file_url", "type", "submitted_at", "milestone_id", "feedback", "feedback_at") VALUES (2, 1, 5, 'D:\HOU-S-RIMS\uploads\BT3_1.pdf', 'report', '2026-09-24 03:58:10.071929', 1, NULL, NULL);
INSERT INTO "submissions" ("id", "topic_id", "uploader_id", "file_url", "type", "submitted_at", "milestone_id", "feedback", "feedback_at") VALUES (3, 2, 7, 'D:\HOU-S-RIMS\uploads\partial_clean_049.csv', 'report', '2026-10-01 05:25:00.979551', 1, NULL, NULL);
INSERT INTO "submissions" ("id", "topic_id", "uploader_id", "file_url", "type", "submitted_at", "milestone_id", "feedback", "feedback_at") VALUES (4, 3, 5, 'D:\HOU-S-RIMS\uploads\partial_clean_049.csv', 'report', '2026-10-08 03:36:28.936652', 2, 'cần sửaf

--- 11:05:28 8/10/2026 ---
ff

--- 11:10:56 08/10/2026 ---
g

--- 11:11:00 08/10/2026 ---
g', '2026-10-08 04:11:00.508320');
INSERT INTO "submissions" ("id", "topic_id", "uploader_id", "file_url", "type", "submitted_at", "milestone_id", "feedback", "feedback_at") VALUES (5, 3, 5, 'D:\HOU-S-RIMS\uploads\partial_clean_052.csv', 'report', '2026-10-08 03:36:35.426417', 3, NULL, NULL);
INSERT INTO "submissions" ("id", "topic_id", "uploader_id", "file_url", "type", "submitted_at", "milestone_id", "feedback", "feedback_at") VALUES (6, 3, 5, 'D:\HOU-S-RIMS\uploads\partial_gold_057.csv', 'report', '2026-10-08 04:11:31.084436', 2, NULL, NULL);
SELECT setval(pg_get_serial_sequence('"submissions"', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM "submissions";

-- Dữ liệu bảng meetings (1 dòng)
INSERT INTO "meetings" ("id", "title", "description", "start_time", "end_time", "organizer_id", "topic_id", "status") VALUES (1, 'fff', '', '2026-10-09 11:13:00.000000', '2026-10-09 11:13:00.000000', 5, NULL, 'pending');
SELECT setval(pg_get_serial_sequence('"meetings"', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM "meetings";

-- Dữ liệu bảng messages (29 dòng)
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (27, 5, 3, NULL, 'd', '2026-09-17 03:49:42.922943', 'text', NULL, NULL, NULL, TRUE, '2026-10-01 04:57:34.364649');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (28, 5, 3, NULL, 'f', '2026-09-17 03:54:18.164294', 'text', NULL, NULL, NULL, TRUE, '2026-10-01 04:57:34.364661');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (31, 5, 6, NULL, 'yo', '2026-10-01 03:43:21.541325', 'text', NULL, NULL, NULL, TRUE, '2026-10-01 04:56:13.199952');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (33, 6, 5, NULL, 'hi', '2026-10-01 04:39:40.985155', 'text', NULL, NULL, NULL, TRUE, '2026-10-01 04:56:26.962548');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (34, 7, 5, NULL, '📩 Mời bạn tham gia nhóm NCKH cho đề tài **ggafafa**. Nhấn Đồng ý để xác nhận.', '2026-10-01 04:56:48.301787', 'invitation', NULL, NULL, '{"invite_group_id": 2, "topic_name": "ggafafa"}', TRUE, '2026-10-01 04:57:19.715416');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (35, 7, 6, NULL, '📩 Mời bạn tham gia nhóm NCKH cho đề tài **ggafafa**. Nhấn Đồng ý để xác nhận.', '2026-10-01 04:56:48.301794', 'invitation', NULL, NULL, '{"invite_group_id": 2, "topic_name": "ggafafa", "invite_status": "accepted"}', TRUE, '2026-10-01 04:57:47.760209');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (36, 7, 5, NULL, '📩 Mời bạn tham gia nhóm NCKH cho đề tài **dbsbsb**. Nhấn Đồng ý để xác nhận.', '2026-10-01 05:16:38.890133', 'invitation', NULL, NULL, '{"invite_group_id": 2, "topic_name": "dbsbsb", "invite_status": "rejected"}', TRUE, '2026-10-01 05:17:13.206507');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (37, 7, 6, NULL, '📩 Mời bạn tham gia nhóm NCKH cho đề tài **dbsbsb**. Nhấn Đồng ý để xác nhận.', '2026-10-01 05:16:38.890140', 'invitation', NULL, NULL, '{"invite_group_id": 2, "topic_name": "dbsbsb", "invite_status": "accepted"}', TRUE, '2026-10-01 05:16:51.726148');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (38, 7, 5, NULL, '📩 Mời bạn tham gia nhóm NCKH cho đề tài **ưtgagag**. Nhấn Đồng ý để xác nhận.', '2026-10-01 05:21:24.143343', 'invitation', NULL, NULL, '{"invite_group_id": 2, "topic_name": "\u01b0tgagag", "invite_status": "accepted"}', TRUE, '2026-10-01 05:21:25.195986');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (39, 3, NULL, 1, 'hhii', '2026-10-01 05:22:09.693464', 'text', NULL, NULL, NULL, FALSE, NULL);
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (40, 3, NULL, 2, 'h', '2026-10-01 05:23:44.473401', 'text', NULL, NULL, NULL, FALSE, NULL);
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (41, 5, 6, NULL, '📩 Mời bạn tham gia nhóm NCKH cho đề tài **ggg**. Nhấn Đồng ý để xác nhận.', '2026-10-08 02:19:19.611141', 'invitation', NULL, NULL, '{"invite_group_id": 3, "topic_name": "ggg", "invite_status": "accepted"}', TRUE, '2026-10-08 02:19:56.879820');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (42, 5, 7, NULL, '📩 Mời bạn tham gia nhóm NCKH cho đề tài **ggg**. Nhấn Đồng ý để xác nhận.', '2026-10-08 02:19:19.611147', 'invitation', NULL, NULL, '{"invite_group_id": 3, "topic_name": "ggg"}', FALSE, NULL);
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (43, 3, NULL, 3, 'hi', '2026-10-08 02:41:43.745030', 'text', NULL, NULL, NULL, FALSE, NULL);
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (44, 5, 3, NULL, 'hi', '2026-10-08 02:42:00.556654', 'text', NULL, NULL, NULL, TRUE, '2026-10-08 02:42:05.863197');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (45, 3, NULL, 3, 'l', '2026-10-08 03:22:20.627144', 'text', NULL, NULL, NULL, FALSE, NULL);
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (46, 3, NULL, 3, '❤️', '2026-10-08 03:35:57.614195', 'text', NULL, NULL, NULL, FALSE, NULL);
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (47, 5, NULL, 3, 'xin chào ạ', '2026-10-14 11:58:15.124165', 'text', NULL, NULL, NULL, FALSE, NULL);
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (48, 5, NULL, 3, 'hi mọi người', '2026-10-14 12:14:12.141616', 'text', NULL, NULL, NULL, FALSE, NULL);
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (49, 5, NULL, 3, '', '2026-10-14 12:14:27.645499', 'image', '/static/uploads/chat/1791964332563_132649162534217894_6841956120511550338_3f742cca8439e343ae121ddc6faf35ab.jpg', '1791964332563_132649162534217894_6841956120511550338_3f742cca8439e343ae121ddc6faf35ab.jpg', NULL, FALSE, NULL);
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (50, 5, NULL, 3, '', '2026-10-14 12:14:36.322752', 'file', '/static/uploads/chat/Huong_dan_game_Bug_Hunter_Android_Java_don_gian.docx', 'Huong_dan_game_Bug_Hunter_Android_Java_don_gian.docx', NULL, FALSE, NULL);
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (51, 5, 3, NULL, 'em chào thầy', '2026-10-14 12:16:32.504017', 'text', NULL, NULL, NULL, TRUE, '2026-10-14 12:17:04.186178');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (52, 3, 5, NULL, 'ừ chào em', '2026-10-14 12:17:10.836936', 'text', NULL, NULL, NULL, TRUE, '2026-10-14 12:18:03.186973');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (53, 3, 5, NULL, 'em gửi thầy các bài khác nhé', '2026-10-14 12:17:34.354509', 'text', NULL, NULL, NULL, TRUE, '2026-10-14 12:18:03.187005');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (54, 5, 3, NULL, 'dạ vâng ạ', '2026-10-14 12:18:09.072155', 'text', NULL, NULL, NULL, TRUE, '2026-10-14 12:19:31.927790');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (55, 5, 3, NULL, 'thầy ơi các bạn không làm tập ạ', '2026-10-14 12:19:46.499846', 'text', NULL, NULL, NULL, TRUE, '2026-10-14 12:19:47.614661');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (56, 5, 3, NULL, '', '2026-10-14 12:21:00.884621', 'file', '/static/uploads/chat/Phan_cong_nhiem_vu_8-10.xlsx', 'Phan_cong_nhiem_vu_8-10.xlsx', NULL, TRUE, '2026-10-14 12:21:02.614354');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (57, 3, 5, NULL, 'gửi thầy tài liệu buổi trước nhé', '2026-10-14 12:26:50.446467', 'text', NULL, NULL, NULL, TRUE, '2026-10-14 12:26:50.612407');
INSERT INTO "messages" ("id", "sender_id", "receiver_id", "group_id", "content", "timestamp", "message_type", "file_url", "file_name", "meta_data", "is_read", "read_at") VALUES (58, 5, 3, NULL, 'dạ vâng', '2026-10-14 12:40:59.313239', 'text', NULL, NULL, NULL, TRUE, '2026-10-14 12:41:02.153714');
SELECT setval(pg_get_serial_sequence('"messages"', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM "messages";

-- Dữ liệu bảng notifications (60 dòng)
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (3, 6, 'Khoa vừa mở đợt test_batch_123.', FALSE, '2026-10-08 01:47:49.145583');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (4, 7, 'Khoa vừa mở đợt test_batch_123.', FALSE, '2026-10-08 01:47:49.145586');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (6, 6, 'Khoa vừa mở đợt gagagaga.|||GiuaKy-DamBaoCLPM_1.pdf|||BTL_-_AN_NINH_BAO_MAT_DU_LIEU_4.docx', FALSE, '2026-10-08 01:49:20.072694');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (7, 7, 'Khoa vừa mở đợt gagagaga.|||GiuaKy-DamBaoCLPM_1.pdf|||BTL_-_AN_NINH_BAO_MAT_DU_LIEU_4.docx', FALSE, '2026-10-08 01:49:20.072697');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (9, 6, '
        <h4 style=''color: #4f46e5; margin-bottom: 15px;''>Chi tiết Đợt: gagagaga</h4>
        <div style=''background: #f8f9fa; padding: 15px; border-radius: 8px;''>
            <p><strong>Năm học áp dụng:</strong> 2025-2026</p>
            <p><strong>Loại hình:</strong> NCKH Standard</p>
            <p><strong>Ngày bắt đầu:</strong> 08/10/2026</p>
            <p><strong>Hạn nộp đề tài:</strong> <span style=''color: #dc3545; font-weight: bold;''>08/10/2026</span></p>
            <p><strong>Ngày kết thúc:</strong> 09/10/2026</p>
        </div>
        <div style=''margin-top: 15px;''><strong>Mô tả chi tiết:</strong><br><p>fffffffffffffffffffffffff<strong>ffffffffffffffffffffffffffffffffffffffffffffffffff<u>ffffffffffff</u><em><u>ffffffffffffffffffffffffffffffff</u></em></strong></p><p><strong><em><u>faf</u></em></strong>			</p><p>			fafaf</p><p>		faaf</p></div>|||GiuaKy-DamBaoCLPM_1.pdf|||BTL_-_AN_NINH_BAO_MAT_DU_LIEU_4.docx|||downloads_TongHopTaiLieuThamKhao_BTL_1.xlsx', FALSE, '2026-10-08 02:00:37.418509');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (10, 7, '
        <h4 style=''color: #4f46e5; margin-bottom: 15px;''>Chi tiết Đợt: gagagaga</h4>
        <div style=''background: #f8f9fa; padding: 15px; border-radius: 8px;''>
            <p><strong>Năm học áp dụng:</strong> 2025-2026</p>
            <p><strong>Loại hình:</strong> NCKH Standard</p>
            <p><strong>Ngày bắt đầu:</strong> 08/10/2026</p>
            <p><strong>Hạn nộp đề tài:</strong> <span style=''color: #dc3545; font-weight: bold;''>08/10/2026</span></p>
            <p><strong>Ngày kết thúc:</strong> 09/10/2026</p>
        </div>
        <div style=''margin-top: 15px;''><strong>Mô tả chi tiết:</strong><br><p>fffffffffffffffffffffffff<strong>ffffffffffffffffffffffffffffffffffffffffffffffffff<u>ffffffffffff</u><em><u>ffffffffffffffffffffffffffffffff</u></em></strong></p><p><strong><em><u>faf</u></em></strong>			</p><p>			fafaf</p><p>		faaf</p></div>|||GiuaKy-DamBaoCLPM_1.pdf|||BTL_-_AN_NINH_BAO_MAT_DU_LIEU_4.docx|||downloads_TongHopTaiLieuThamKhao_BTL_1.xlsx', FALSE, '2026-10-08 02:00:37.418514');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (12, 6, '
        <h5 style=''color: #4f46e5; margin-bottom: 8px;''>Đợt NCKH: gagagaga</h5>
        <div style=''background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 13px;''>
            <strong>Loại:</strong> NCKH Standard | 
            <strong>Năm:</strong> 2025-2026 | 
            <strong>Bắt đầu:</strong> 08/10/2026 | 
            <strong>Deadline:</strong> <span style=''color: #dc3545;''>09/10/2026</span>
        </div>
        <div style=''margin-top: 15px;''><strong>Mô tả chi tiết:</strong><br><p>kk<strong>kkkkk</strong>	<strong><em>kkk<u>kk</u></em></strong>		vg<s>ggggg</s></p><p><s>ggg</s>						ggggggggg<em>ggggg</em></p></div>|||GiuaKy-DamBaoCLPM_1.pdf|||BTL_-_AN_NINH_BAO_MAT_DU_LIEU_4.docx|||downloads_PhanCongBTL_KiemSoatTruyCap_TMDT_1.xlsx', FALSE, '2026-10-08 02:05:26.885176');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (13, 7, '
        <h5 style=''color: #4f46e5; margin-bottom: 8px;''>Đợt NCKH: gagagaga</h5>
        <div style=''background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 13px;''>
            <strong>Loại:</strong> NCKH Standard | 
            <strong>Năm:</strong> 2025-2026 | 
            <strong>Bắt đầu:</strong> 08/10/2026 | 
            <strong>Deadline:</strong> <span style=''color: #dc3545;''>09/10/2026</span>
        </div>
        <div style=''margin-top: 15px;''><strong>Mô tả chi tiết:</strong><br><p>kk<strong>kkkkk</strong>	<strong><em>kkk<u>kk</u></em></strong>		vg<s>ggggg</s></p><p><s>ggg</s>						ggggggggg<em>ggggg</em></p></div>|||GiuaKy-DamBaoCLPM_1.pdf|||BTL_-_AN_NINH_BAO_MAT_DU_LIEU_4.docx|||downloads_PhanCongBTL_KiemSoatTruyCap_TMDT_1.xlsx', FALSE, '2026-10-08 02:05:26.885179');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (14, 3, '
            <p>Xin chào <strong>TS. Nguyen Van A</strong>,</p>
            <p>Đề tài NCKH <strong>ggg</strong> do bạn hướng dẫn đã được Khoa chính thức phê duyệt.</p>
            <a href=''/lecturer/progress'' class=''btn btn-success rounded-pill btn-sm mt-2''>Xem Tiến độ</a>
            ', TRUE, '2026-10-08 03:11:31.867567');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (15, 5, '
                <p>Xin chào <strong>Nguyễn Hà Phương</strong>,</p>
                <p>Đề tài NCKH <strong>ggg</strong> của nhóm bạn đã được Khoa chính thức phê duyệt.</p>
                <a href=''/student/progress'' class=''btn btn-success rounded-pill btn-sm mt-2''>Xem Tiến độ</a>
                ', TRUE, '2026-10-08 03:11:31.873266');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (16, 6, '
                <p>Xin chào <strong>Nguyen Van Hoc</strong>,</p>
                <p>Đề tài NCKH <strong>ggg</strong> của nhóm bạn đã được Khoa chính thức phê duyệt.</p>
                <a href=''/student/progress'' class=''btn btn-success rounded-pill btn-sm mt-2''>Xem Tiến độ</a>
                ', FALSE, '2026-10-08 03:11:31.874937');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (17, 7, '
                <p>Xin chào <strong>Le Thi Lan</strong>,</p>
                <p>Đề tài NCKH <strong>ggg</strong> của nhóm bạn đã được Khoa chính thức phê duyệt.</p>
                <a href=''/student/progress'' class=''btn btn-success rounded-pill btn-sm mt-2''>Xem Tiến độ</a>
                ', FALSE, '2026-10-08 03:11:31.876157');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (18, 5, '📝 TS. Nguyen Van A đã ghi chú cho bài nộp của bạn trong đề tài ''ggg'': cần sửa', TRUE, '2026-10-08 03:48:29.026259');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (19, 5, '📝 TS. Nguyen Van A đã ghi chú cho bài nộp của bạn trong đề tài ''ggg'': cần sửaf', FALSE, '2026-10-08 04:01:29.631017');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (20, 5, '📝 TS. Nguyen Van A đã ghi chú cho bài nộp của bạn trong đề tài ''ggg'': cần sửaf', FALSE, '2026-10-08 04:01:30.751611');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (21, 5, '📝 TS. Nguyen Van A đã ghi chú cho bài nộp của bạn trong đề tài ''ggg'': cần sửaf', FALSE, '2026-10-08 04:01:32.250348');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (22, 5, '📝 TS. Nguyen Van A đã ghi chú cho bài nộp của bạn trong đề tài ''ggg'': cần sửaf', FALSE, '2026-10-08 04:01:32.406757');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (23, 5, '📝 TS. Nguyen Van A đã ghi chú cho bài nộp của bạn trong đề tài ''ggg'': cần sửaf', FALSE, '2026-10-08 04:01:32.591231');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (24, 5, '📝 TS. Nguyen Van A đã ghi chú cho bài nộp của bạn trong đề tài ''ggg'': cần sửaf

--- 11:05:25 8/10/2026 ---
ff', FALSE, '2026-10-08 04:05:25.515957');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (25, 5, '📝 TS. Nguyen Van A đã ghi chú cho bài nộp của bạn trong đề tài ''ggg'': cần sửaf

--- 11:05:28 8/10/2026 ---
ff', FALSE, '2026-10-08 04:05:28.839419');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (26, 5, '📝 TS. Nguyen Van A đã ghi chú cho bài nộp của bạn trong đề tài ''ggg'': g', FALSE, '2026-10-08 04:10:56.085043');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (27, 5, '📝 TS. Nguyen Van A đã ghi chú cho bài nộp của bạn trong đề tài ''ggg'': g', TRUE, '2026-10-08 04:11:00.521416');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (28, 8, 'Bạn đã được thêm vào dddddddddddd. Thời gian: 04:44 ngày 09/10/2026, Địa điểm: hhhh', FALSE, '2026-10-08 04:51:28.597336');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (29, 3, 'Bạn đã được thêm vào dddddddddddd. Thời gian: 04:44 ngày 09/10/2026, Địa điểm: hhhh', TRUE, '2026-10-08 04:51:32.536416');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (30, 4, 'Bạn đã được thêm vào dddddddddddd. Thời gian: 04:44 ngày 09/10/2026, Địa điểm: hhhh', FALSE, '2026-10-08 04:51:37.591665');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (31, 5, 'Nhóm của bạn đã được sắp xếp báo cáo trước dddddddddddd. Thời gian: 04:44 ngày 09/10/2026, Địa điểm: hhhh', FALSE, '2026-10-08 04:51:41.459355');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (32, 6, 'Nhóm của bạn đã được sắp xếp báo cáo trước dddddddddddd. Thời gian: 04:44 ngày 09/10/2026, Địa điểm: hhhh', FALSE, '2026-10-08 04:51:45.502738');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (33, 7, 'Nhóm của bạn đã được sắp xếp báo cáo trước dddddddddddd. Thời gian: 04:44 ngày 09/10/2026, Địa điểm: hhhh', FALSE, '2026-10-08 04:51:49.402832');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (34, 3, 'Hội đồng ''dddddddddddd'' đã bị hủy bỏ.', FALSE, '2026-10-08 05:43:19.879860');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (35, 4, 'Hội đồng ''dddddddddddd'' đã bị hủy bỏ.', FALSE, '2026-10-08 05:43:23.982533');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (36, 8, 'Hội đồng ''dddddddddddd'' đã bị hủy bỏ.', FALSE, '2026-10-08 05:43:28.695796');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (37, 3, 'Hội đồng ''dddddddddddd'' đã bị hủy bỏ.', FALSE, '2026-10-08 05:43:32.630587');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (38, 4, 'Hội đồng ''dddddddddddd'' đã bị hủy bỏ.', FALSE, '2026-10-08 05:43:37.723214');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (39, 3, 'Bạn đã được thêm vào ggggggggggggggggggggg. Thời gian: 13:46 ngày 10/10/2026, Địa điểm: gggggggga', FALSE, '2026-10-08 05:47:10.603935');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (40, 5, 'Nhóm của bạn đã được sắp xếp báo cáo trước ggggggggggggggggggggg. Thời gian: 13:46 ngày 10/10/2026, Địa điểm: gggggggga', TRUE, '2026-10-08 05:47:15.116157');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (41, 3, 'Hội đồng ''ggggggggggggggggggggg'' đã bị hủy bỏ.', FALSE, '2026-10-08 05:51:01.330171');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (42, 3, 'Hội đồng ''ggggggggggggggggggggg'' đã bị hủy bỏ.', FALSE, '2026-10-08 05:51:01.330177');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (43, 3, 'Hội đồng ''ggggggggggggggggggggg'' đã bị hủy bỏ.', FALSE, '2026-10-08 05:51:01.330180');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (44, 3, 'Bạn đã được thêm vào fffffff. Thời gian: 13:58 ngày 08/10/2026, Địa điểm: fff', FALSE, '2026-10-08 05:58:02.956726');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (45, 5, 'Nhóm của bạn đã được sắp xếp báo cáo trước fffffff. Thời gian: 13:58 ngày 08/10/2026, Địa điểm: fff', FALSE, '2026-10-08 05:58:07.786744');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (46, 6, 'Nhóm của bạn đã được sắp xếp báo cáo trước fffffff. Thời gian: 13:58 ngày 08/10/2026, Địa điểm: fff', FALSE, '2026-10-08 05:58:12.073528');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (47, 7, 'Nhóm của bạn đã được sắp xếp báo cáo trước fffffff. Thời gian: 13:58 ngày 08/10/2026, Địa điểm: fff', FALSE, '2026-10-08 05:58:16.440056');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (48, 3, 'Hội đồng ''fffffff'' đã bị hủy bỏ.', FALSE, '2026-10-08 05:59:27.598235');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (49, 3, 'Hội đồng ''fffffff'' đã bị hủy bỏ.', FALSE, '2026-10-08 05:59:27.598241');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (50, 3, 'Hội đồng ''fffffff'' đã bị hủy bỏ.', FALSE, '2026-10-08 05:59:27.598244');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (51, 6, 'Sinh viên Nguyễn Hà Phương đã mời bạn tham gia nhóm NCKH: Nhóm Thử Nghiệm NCKH AI.', FALSE, '2026-10-14 11:44:52.342239');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (52, 3, 'Nhóm NCKH của sinh viên Nguyễn Hà Phương (24A1001D0341) đã gửi lời mời bạn làm Giảng viên Hướng dẫn.', FALSE, '2026-10-14 11:44:52.354258');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (53, 3, 'Nhóm NCKH của sinh viên Nguyễn Hà Phương (24A1001D0341) đã gửi lời mời bạn làm Giảng viên Hướng dẫn.', TRUE, '2026-10-14 12:01:06.006719');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (54, 5, '
        <h5 style=''color: #4f46e5; margin-bottom: 8px;''>Đợt NCKH: Đợt Test JSON 2026</h5>
        <div style=''background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 13px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;''>
            <span class=''badge bg-primary''>NCKH Standard</span>
            <span class=''badge bg-secondary''>2025-2026</span>
            <span class=''text-muted''><i class=''fa-regular fa-calendar me-1''></i>01/06/2026</span>
            <span class=''text-muted''><i class=''fa-solid fa-arrow-right''></i></span>
            <span class=''text-danger fw-bold''><i class=''fa-regular fa-calendar-xmark me-1''></i>01/04/2027</span>
        </div>
        ', FALSE, '2026-10-14 12:44:58.163250');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (55, 6, '
        <h5 style=''color: #4f46e5; margin-bottom: 8px;''>Đợt NCKH: Đợt Test JSON 2026</h5>
        <div style=''background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 13px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;''>
            <span class=''badge bg-primary''>NCKH Standard</span>
            <span class=''badge bg-secondary''>2025-2026</span>
            <span class=''text-muted''><i class=''fa-regular fa-calendar me-1''></i>01/06/2026</span>
            <span class=''text-muted''><i class=''fa-solid fa-arrow-right''></i></span>
            <span class=''text-danger fw-bold''><i class=''fa-regular fa-calendar-xmark me-1''></i>01/04/2027</span>
        </div>
        ', FALSE, '2026-10-14 12:44:58.163255');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (56, 7, '
        <h5 style=''color: #4f46e5; margin-bottom: 8px;''>Đợt NCKH: Đợt Test JSON 2026</h5>
        <div style=''background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 13px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;''>
            <span class=''badge bg-primary''>NCKH Standard</span>
            <span class=''badge bg-secondary''>2025-2026</span>
            <span class=''text-muted''><i class=''fa-regular fa-calendar me-1''></i>01/06/2026</span>
            <span class=''text-muted''><i class=''fa-solid fa-arrow-right''></i></span>
            <span class=''text-danger fw-bold''><i class=''fa-regular fa-calendar-xmark me-1''></i>01/04/2027</span>
        </div>
        ', FALSE, '2026-10-14 12:44:58.163257');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (57, 5, '
        <h5 style=''color: #4f46e5; margin-bottom: 8px;''>Đợt NCKH: Đợt Test Form 2026</h5>
        <div style=''background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 13px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;''>
            <span class=''badge bg-primary''>NCKH Standard</span>
            <span class=''badge bg-secondary''>2025-2026</span>
            <span class=''text-muted''><i class=''fa-regular fa-calendar me-1''></i>01/06/2026</span>
            <span class=''text-muted''><i class=''fa-solid fa-arrow-right''></i></span>
            <span class=''text-danger fw-bold''><i class=''fa-regular fa-calendar-xmark me-1''></i>01/04/2027</span>
        </div>
        ', FALSE, '2026-10-14 12:44:58.176452');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (58, 6, '
        <h5 style=''color: #4f46e5; margin-bottom: 8px;''>Đợt NCKH: Đợt Test Form 2026</h5>
        <div style=''background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 13px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;''>
            <span class=''badge bg-primary''>NCKH Standard</span>
            <span class=''badge bg-secondary''>2025-2026</span>
            <span class=''text-muted''><i class=''fa-regular fa-calendar me-1''></i>01/06/2026</span>
            <span class=''text-muted''><i class=''fa-solid fa-arrow-right''></i></span>
            <span class=''text-danger fw-bold''><i class=''fa-regular fa-calendar-xmark me-1''></i>01/04/2027</span>
        </div>
        ', FALSE, '2026-10-14 12:44:58.176457');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (59, 7, '
        <h5 style=''color: #4f46e5; margin-bottom: 8px;''>Đợt NCKH: Đợt Test Form 2026</h5>
        <div style=''background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 13px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;''>
            <span class=''badge bg-primary''>NCKH Standard</span>
            <span class=''badge bg-secondary''>2025-2026</span>
            <span class=''text-muted''><i class=''fa-regular fa-calendar me-1''></i>01/06/2026</span>
            <span class=''text-muted''><i class=''fa-solid fa-arrow-right''></i></span>
            <span class=''text-danger fw-bold''><i class=''fa-regular fa-calendar-xmark me-1''></i>01/04/2027</span>
        </div>
        ', FALSE, '2026-10-14 12:44:58.176459');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (60, 5, '
        <h5 style=''color: #4f46e5; margin-bottom: 8px;''>Đợt NCKH: cádf</h5>
        <div style=''background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 13px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;''>
            <span class=''badge bg-primary''>NCKH Standard</span>
            <span class=''badge bg-secondary''>2026-2027</span>
            <span class=''text-muted''><i class=''fa-regular fa-calendar me-1''></i>03/03/2026</span>
            <span class=''text-muted''><i class=''fa-solid fa-arrow-right''></i></span>
            <span class=''text-danger fw-bold''><i class=''fa-regular fa-calendar-xmark me-1''></i>03/04/2027</span>
        </div>
        <div style=''margin-top: 15px;''><strong>Mô tả chi tiết:</strong><br>gsfs</div>|||Phan_cong_nhiem_vu_8-10.xlsx', FALSE, '2026-10-14 13:00:19.647485');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (61, 6, '
        <h5 style=''color: #4f46e5; margin-bottom: 8px;''>Đợt NCKH: cádf</h5>
        <div style=''background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 13px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;''>
            <span class=''badge bg-primary''>NCKH Standard</span>
            <span class=''badge bg-secondary''>2026-2027</span>
            <span class=''text-muted''><i class=''fa-regular fa-calendar me-1''></i>03/03/2026</span>
            <span class=''text-muted''><i class=''fa-solid fa-arrow-right''></i></span>
            <span class=''text-danger fw-bold''><i class=''fa-regular fa-calendar-xmark me-1''></i>03/04/2027</span>
        </div>
        <div style=''margin-top: 15px;''><strong>Mô tả chi tiết:</strong><br>gsfs</div>|||Phan_cong_nhiem_vu_8-10.xlsx', FALSE, '2026-10-14 13:00:19.647493');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (62, 7, '
        <h5 style=''color: #4f46e5; margin-bottom: 8px;''>Đợt NCKH: cádf</h5>
        <div style=''background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 13px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;''>
            <span class=''badge bg-primary''>NCKH Standard</span>
            <span class=''badge bg-secondary''>2026-2027</span>
            <span class=''text-muted''><i class=''fa-regular fa-calendar me-1''></i>03/03/2026</span>
            <span class=''text-muted''><i class=''fa-solid fa-arrow-right''></i></span>
            <span class=''text-danger fw-bold''><i class=''fa-regular fa-calendar-xmark me-1''></i>03/04/2027</span>
        </div>
        <div style=''margin-top: 15px;''><strong>Mô tả chi tiết:</strong><br>gsfs</div>|||Phan_cong_nhiem_vu_8-10.xlsx', FALSE, '2026-10-14 13:00:19.647497');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (63, 5, '
        <h5 style=''color: #4f46e5; margin-bottom: 8px;''>Đợt NCKH: NCKH sinh viên 2028</h5>
        <div style=''background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 13px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;''>
            <span class=''badge bg-primary''>NCKH Standard</span>
            <span class=''badge bg-secondary''>2027-2028</span>
            <span class=''text-muted''><i class=''fa-regular fa-calendar me-1''></i>04/05/2027</span>
            <span class=''text-muted''><i class=''fa-solid fa-arrow-right''></i></span>
            <span class=''text-danger fw-bold''><i class=''fa-regular fa-calendar-xmark me-1''></i>05/07/2028</span>
        </div>
        <div style=''margin-top: 15px;''><strong>Mô tả chi tiết:</strong><br>rewr</div>|||Phan_cong_nhiem_vu_8-10_1.xlsx', FALSE, '2026-10-14 13:11:32.931502');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (64, 6, '
        <h5 style=''color: #4f46e5; margin-bottom: 8px;''>Đợt NCKH: NCKH sinh viên 2028</h5>
        <div style=''background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 13px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;''>
            <span class=''badge bg-primary''>NCKH Standard</span>
            <span class=''badge bg-secondary''>2027-2028</span>
            <span class=''text-muted''><i class=''fa-regular fa-calendar me-1''></i>04/05/2027</span>
            <span class=''text-muted''><i class=''fa-solid fa-arrow-right''></i></span>
            <span class=''text-danger fw-bold''><i class=''fa-regular fa-calendar-xmark me-1''></i>05/07/2028</span>
        </div>
        <div style=''margin-top: 15px;''><strong>Mô tả chi tiết:</strong><br>rewr</div>|||Phan_cong_nhiem_vu_8-10_1.xlsx', FALSE, '2026-10-14 13:11:32.931509');
INSERT INTO "notifications" ("id", "user_id", "content", "is_read", "created_at") VALUES (65, 7, '
        <h5 style=''color: #4f46e5; margin-bottom: 8px;''>Đợt NCKH: NCKH sinh viên 2028</h5>
        <div style=''background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 13px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;''>
            <span class=''badge bg-primary''>NCKH Standard</span>
            <span class=''badge bg-secondary''>2027-2028</span>
            <span class=''text-muted''><i class=''fa-regular fa-calendar me-1''></i>04/05/2027</span>
            <span class=''text-muted''><i class=''fa-solid fa-arrow-right''></i></span>
            <span class=''text-danger fw-bold''><i class=''fa-regular fa-calendar-xmark me-1''></i>05/07/2028</span>
        </div>
        <div style=''margin-top: 15px;''><strong>Mô tả chi tiết:</strong><br>rewr</div>|||Phan_cong_nhiem_vu_8-10_1.xlsx', FALSE, '2026-10-14 13:11:32.931514');
SELECT setval(pg_get_serial_sequence('"notifications"', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM "notifications";


-- ==========================================================
-- HOÀN TẤT TẠO BẢNG VÀ NẠP DỮ LIỆU LÊN SUPABASE
-- ==========================================================
