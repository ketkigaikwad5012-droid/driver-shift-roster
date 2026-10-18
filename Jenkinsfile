
pipeline {
    agent any

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
    }

    post {
        success {
            echo 'Build, tests, packaging and deployment preparation completed successfully.'
        }
        failure {
            echo 'Pipeline failed. Check the stage logs for details.'
        }
    }
}
