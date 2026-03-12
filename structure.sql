SET NAMES utf8mb4;

DROP TABLE IF EXISTS `assignment_profile`;
CREATE TABLE `assignment_profile` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `type` varchar(60) NOT NULL,
  `options` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;


DROP TABLE IF EXISTS `subjects`;
CREATE TABLE `subjects` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
    `shortcut` varchar(20) NOT NULL,
    `name` varchar(255) NOT NULL,
    `year` int(11) NOT NULL,
    `semester` enum('S','W') NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;

DROP TABLE IF EXISTS `scheduled_events`;
CREATE TABLE `scheduled_events` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
    `subject_id` bigint(20) unsigned NOT NULL,
    `day` tinyint(4) NOT NULL,
    `time_from` time NOT NULL,
    `time_to` time NOT NULL,
    `exam` tinyint(4) NOT NULL DEFAULT 0,
    `exam_date` datetime DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `subject_id` (`subject_id`),
    CONSTRAINT `scheduled_events_ibfk_1` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;

CREATE TABLE IF NOT EXISTS `checks_config` (
  `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `subject_id` BIGINT(20) UNSIGNED NOT NULL,
  `config_json` LONGTEXT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_checks_config_subject` (`subject_id`),
  CONSTRAINT `checks_config_fk_subject`
    FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;


DROP TABLE IF EXISTS `students`;
CREATE TABLE `students` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
    `student_number` varchar(15) NOT NULL,
    `scheduled_event_id` bigint(20) unsigned NOT NULL,
    `orion` varchar(15) NOT NULL,
    `name` varchar(255) NOT NULL,
    `surname` varchar(255) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `student_number_event_id` (`student_number`,`scheduled_event_id`),
    UNIQUE KEY `orion_event_id` (`orion`,`scheduled_event_id`),
    KEY `scheduled_event_id` (`scheduled_event_id`),
    CONSTRAINT `scheduled_events_ibfk_2` FOREIGN KEY (`scheduled_event_id`) REFERENCES `scheduled_events` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;

DROP TABLE IF EXISTS `assignments`;
CREATE TABLE `assignments` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
    `assignment_profile_id` bigint(20) unsigned NOT NULL,
    `date_from` datetime NOT NULL,
    `date_to` datetime NOT NULL,
    `scheduled_event_id` bigint(20) unsigned NOT NULL,
    `name` varchar(255) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `assignment_profile_id` (`assignment_profile_id`),
    KEY `scheduled_event_id` (`scheduled_event_id`),
    CONSTRAINT `assignments_ibfk_2` FOREIGN KEY (`assignment_profile_id`) REFERENCES `assignment_profile` (`id`),
    CONSTRAINT `assignments_ibfk_3` FOREIGN KEY (`scheduled_event_id`) REFERENCES `scheduled_events` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;

DROP TABLE IF EXISTS `assignment_students`;
CREATE TABLE `assignment_students` (
   `assignment_id` bigint(20) unsigned NOT NULL,
   `student_id`    bigint(20) unsigned NOT NULL,
   `generated` tinyint(4) NOT NULL DEFAULT 0,
   `state` tinyint(4) NOT NULL DEFAULT 0,
   `result` text NOT NULL,
   PRIMARY KEY (`assignment_id`, `student_id`),
   KEY `student_id` (`student_id`),
   CONSTRAINT `assignment_students_ibfk_1` FOREIGN KEY (`assignment_id`) REFERENCES `assignments` (`id`),
   CONSTRAINT `assignment_students_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

DROP TABLE IF EXISTS `assignment_files`;
CREATE TABLE `assignment_files` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
    `assignment_id` bigint(20) unsigned NOT NULL,
    `student_id` bigint(20) unsigned NOT NULL,
    `filename` varchar(255) NOT NULL,
    `filetype` tinyint(4) NOT NULL,
    `location` varchar(255) NOT NULL,
    `time` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    PRIMARY KEY (`id`),
    KEY `assignment_id` (`assignment_id`),
    KEY `student_id` (`student_id`),
    CONSTRAINT `assignment_files_ibfk_1` FOREIGN KEY (`assignment_id`) REFERENCES `assignments` (`id`),
    CONSTRAINT `assignment_files_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
 `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
 `username` varchar(255) NOT NULL,
 `name` varchar(255) NOT NULL,
 `surname` varchar(255) NOT NULL,
 `password` varchar(255) NOT NULL,
 `admin` tinyint(4) NOT NULL DEFAULT 0,
 PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;

DROP TABLE IF EXISTS `logs`;
CREATE TABLE `logs` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
    `time` datetime NOT NULL,
    `user_id` bigint(20) unsigned DEFAULT NULL,
    `student_id` bigint(20) unsigned DEFAULT NULL,
    `message` text NOT NULL,
    `log_type` int(11) NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    KEY `user_id` (`user_id`),
    KEY `student_id` (`student_id`),
    CONSTRAINT `logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
    CONSTRAINT `logs_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;


DROP TABLE IF EXISTS `options`;
CREATE TABLE `options` (
   `option` varchar(255) NOT NULL,
   `value` varchar(255) NOT NULL,
   PRIMARY KEY (`option`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;


DROP TABLE IF EXISTS `teachers`;
CREATE TABLE `teachers` (
    `user_id` bigint(20) unsigned NOT NULL,
    `scheduled_event_id` bigint(20) unsigned NOT NULL,
    PRIMARY KEY (`user_id`,`scheduled_event_id`),
    KEY `scheduled_event_id` (`scheduled_event_id`),
    CONSTRAINT `teachers_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
    CONSTRAINT `teachers_ibfk_2` FOREIGN KEY (`scheduled_event_id`) REFERENCES `scheduled_events` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;

DROP TABLE IF EXISTS `students_on_exam`;
CREATE TABLE `students_on_exam` (
    `scheduled_event_id` bigint(20) unsigned NOT NULL,
    `student_id` bigint(20) unsigned NOT NULL,
    UNIQUE KEY `scheduled_event_id_student_id` (`scheduled_event_id`,`student_id`),
    KEY `student_id` (`student_id`),
    CONSTRAINT `students_on_exam_ibfk_1` FOREIGN KEY (`scheduled_event_id`) REFERENCES `scheduled_events` (`id`),
    CONSTRAINT `students_on_exam_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;