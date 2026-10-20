
pipeline {
    agent any

    environment {
        PYTHON_EXE = 'C:\\Users\\KETKI\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'
        CHROME_BIN = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
        APP_PORT = '8082'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out the Driver Shift Roster project'
                checkout scm
            }
        }

        stage('Build and Test') {
            steps {
                bat 'call mvnw.cmd clean verify'
            }
        }

        stage('Package Application') {
            steps {
                archiveArtifacts artifacts: 'target/*.jar',
                                 fingerprint: true
            }
        }

        stage('Prepare Deployment') {
            steps {
                bat '''
                if not exist "D:\\driver-shift-roster-deploy" mkdir "D:\\driver-shift-roster-deploy"
                copy /Y "target\\driver-shift-roster-0.0.1-SNAPSHOT.jar" "D:\\driver-shift-roster-deploy\\driver-shift-roster.jar"
                '''
            }
        }

        stage('Install Selenium Dependencies') {
            steps {
                bat '"%PYTHON_EXE%" -m pip install -r requirements-test.txt'
            }
        }

        stage('Selenium Continuous Tests') {
            steps {
                echo 'Running Selenium browser tests'
                bat '''
                "%PYTHON_EXE%" -c "import selenium; print('Selenium version:', selenium.__version__)"
                "%PYTHON_EXE%" -m unittest selenium-tests\\test_driver_roster.py -v
                '''
            }
        }
    }

    post {
        success {
            echo 'Build, unit tests, packaging, deployment preparation and Selenium tests completed successfully.'
        }
        failure {
            echo 'Pipeline failed. Check the stage logs for details.'
        }
    }
}
