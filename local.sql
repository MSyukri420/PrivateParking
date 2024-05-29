/*
SQLyog Community v13.2.1 (64 bit)
MySQL - 8.0.35 : Database - parking
*********************************************************************
*/

/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

/*Table structure for table `access_logs` */

DROP TABLE IF EXISTS `access_logs`;

CREATE TABLE `access_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `event_type` varchar(50) NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4;

/*Data for the table `access_logs` */

insert  into `access_logs`(`id`,`user_id`,`event_type`,`timestamp`) values 
(1,1,'enter','2024-05-24 03:20:37'),
(2,1,'enter','2024-05-24 03:35:24'),
(3,1,'enter','2024-05-24 03:36:43'),
(4,1,'enter','2024-05-24 03:38:24'),
(5,1,'enter','2024-05-24 03:40:29'),
(6,1,'enter','2024-05-24 03:45:49'),
(7,1,'enter','2024-05-24 03:47:18'),
(8,1,'enter','2024-05-24 03:50:07'),
(9,1,'enter','2024-05-24 03:52:55'),
(10,1,'enter','2024-05-24 04:02:18'),
(11,1,'enter','2024-05-24 04:06:05'),
(12,1,'enter','2024-05-24 04:07:58'),
(13,1,'enter','2024-05-24 04:10:02'),
(14,1,'enter','2024-05-24 04:13:47'),
(15,1,'enter','2024-05-29 01:01:23'),
(16,1,'enter','2024-05-29 01:56:17'),
(17,1,'enter','2024-05-29 01:57:36'),
(18,1,'enter','2024-05-29 15:53:04'),
(19,1,'enter','2024-05-29 17:08:00');

/*Table structure for table `accounts` */

DROP TABLE IF EXISTS `accounts`;

CREATE TABLE `accounts` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(20) DEFAULT NULL,
  `password` varchar(20) DEFAULT NULL,
  `email` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;

/*Data for the table `accounts` */

insert  into `accounts`(`id`,`username`,`password`,`email`) values 
(1,'admin','admin123','admin@gmail.com');

/*Table structure for table `car_entry_exit_log` */

DROP TABLE IF EXISTS `car_entry_exit_log`;

CREATE TABLE `car_entry_exit_log` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `enter_at` datetime DEFAULT NULL,
  `exit_at` datetime DEFAULT NULL,
  `carplate` varchar(10) DEFAULT NULL,
  `duration` decimal(10,0) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

/*Data for the table `car_entry_exit_log` */

/*Table structure for table `parking_sessions` */

DROP TABLE IF EXISTS `parking_sessions`;

CREATE TABLE `parking_sessions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `slot_id` int NOT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;

/*Data for the table `parking_sessions` */

insert  into `parking_sessions`(`id`,`slot_id`,`start_time`,`end_time`,`status`) values 
(1,1,'2024-05-29 21:43:28','2024-05-29 21:43:54','completed');

/*Table structure for table `private_carpark_slot` */

DROP TABLE IF EXISTS `private_carpark_slot`;

CREATE TABLE `private_carpark_slot` (
  `id` int DEFAULT NULL,
  `status` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

/*Data for the table `private_carpark_slot` */

insert  into `private_carpark_slot`(`id`,`status`) values 
(1,0),
(2,0),
(3,0),
(4,0),
(5,0),
(6,0),
(7,0),
(8,0),
(9,0),
(10,0);

/*Table structure for table `public_carpark_slot` */

DROP TABLE IF EXISTS `public_carpark_slot`;

CREATE TABLE `public_carpark_slot` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `status` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4;

/*Data for the table `public_carpark_slot` */

insert  into `public_carpark_slot`(`id`,`status`) values 
(1,0),
(2,2),
(3,0),
(4,1),
(5,1),
(6,1),
(7,1),
(8,1),
(9,1),
(10,1);

/*Table structure for table `system_alarms` */

DROP TABLE IF EXISTS `system_alarms`;

CREATE TABLE `system_alarms` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(255) NOT NULL,
  `description` text,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4;

/*Data for the table `system_alarms` */

insert  into `system_alarms`(`id`,`type`,`description`,`timestamp`) values 
(1,'enter','error at private gate','2024-05-28 14:06:28'),
(2,'enter','error at private gate','2024-05-29 00:58:35'),
(3,'enter','error at private gate','2024-05-29 01:00:15'),
(4,'enter','error at private gate','2024-05-29 01:00:34'),
(5,'Error at parking slot','Parking sensor error detected','2024-05-29 21:43:18');

/*Table structure for table `users` */

DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `rfid_tag` varchar(255) NOT NULL,
  `email` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `rfid_tag` (`rfid_tag`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;

/*Data for the table `users` */

insert  into `users`(`id`,`username`,`rfid_tag`,`email`,`created_at`,`updated_at`) values 
(1,'syukri','13851605','m.syukri420@gmail.com','2024-05-23 15:24:53','2024-05-23 15:25:00');

/*Table structure for table `variables` */

DROP TABLE IF EXISTS `variables`;

CREATE TABLE `variables` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8mb4 DEFAULT NULL,
  `value` bigint DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4;

/*Data for the table `variables` */

insert  into `variables`(`id`,`name`,`value`) values 
(1,'public_max_car_number',86),
(2,'public_current_car_number',20),
(4,'public_switch_on_light',0),
(5,'public_switch_off_light',0),
(6,'public_automation_light',0),
(7,'public_manual',0),
(8,'public_always_open_gate',1),
(9,'public_always_close_gate',0),
(10,'public_manual_light',0),
(11,'public_automation_light_status',0),
(12,'private_always_open_gate',0),
(13,'private_always_close_gate',0),
(14,'private_current_car_number',20),
(15,'private_max_car_number',50),
(16,'private_switch_on_light',0),
(17,'private_switch_off_light',0);

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
