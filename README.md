# Driver Shift Roster System

A Spring Boot web application for managing drivers and scheduling shifts.

## Features

- Driver registration
- Driver availability management
- Shift scheduling
- Validation for invalid and overlapping shifts

## Technology Stack

- Java 21
- Spring Boot
- Maven
- MySQL
- Thymeleaf
- Jenkins
- Git and GitHub

## Continuous Integration

Jenkins builds the project using the Maven Wrapper and runs automated tests.

## Run Locally

Set the `DB_PASSWORD` environment variable, then run:

```powershell
.\mvnw.cmd spring-boot:run
```
