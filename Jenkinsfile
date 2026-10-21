
pipeline {
    agent any

    environment {
        PYTHON_EXE = 'C:\\Users\\KETKI\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'
        CHROME_BIN = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
        APP_PORT = '8083'
        BASE_URL = 'http://localhost:8083'
        DEPLOY_DIR = 'D:\\driver-shift-roster-deploy'
        APP_JAR = 'D:\\driver-shift-roster-deploy\\driver-shift-roster.jar'
        JAVA_EXE = 'C:\\Program Files\\Eclipse Adoptium\\jdk-21.0.12.101-hotspot\\bin\\java.exe'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out the Driver Shift Roster project'
                checkout scm
            }
        }
        
        stage('Check Docker Access') {
            steps {
                bat 'whoami'
                bat 'docker version'
                bat 'docker info'
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
                if not exist "%DEPLOY_DIR%" mkdir "%DEPLOY_DIR%"
                copy /Y "target\\driver-shift-roster-0.0.1-SNAPSHOT.jar" "%APP_JAR%"
                if errorlevel 1 exit /b 1
                '''
            }
        }

        stage('Install Selenium Dependencies') {
            steps {
                bat '"%PYTHON_EXE%" -m pip install -r requirements-test.txt'
            }
        }

        stage('Start Test Application') {
            steps {
                bat '''
                if not defined DB_PASSWORD (
                    echo ERROR: DB_PASSWORD is not configured in Jenkins.
                    exit /b 1
                )

                powershell -NoProfile -ExecutionPolicy Bypass -Command "$pidFile = Join-Path $env:DEPLOY_DIR 'ci-app.pid'; if (Test-Path $pidFile) { Remove-Item $pidFile -Force }; $listener = Get-NetTCPConnection -LocalPort ([int]$env:APP_PORT) -State Listen -ErrorAction SilentlyContinue; if ($listener) { Write-Error 'CI port is already in use. Stop the existing listener before retrying.'; exit 1 }; $p = Start-Process -FilePath $env:JAVA_EXE -ArgumentList @('-jar', $env:APP_JAR, ('--server.port=' + $env:APP_PORT)) -PassThru -RedirectStandardOutput (Join-Path $env:DEPLOY_DIR 'ci-app.log') -RedirectStandardError (Join-Path $env:DEPLOY_DIR 'ci-app-error.log'); Set-Content -Path $pidFile -Value $p.Id; $ready = $false; for ($i = 0; $i -lt 60; $i++) { $p.Refresh(); if ($p.HasExited) { Write-Error 'Application process exited during startup'; Get-Content (Join-Path $env:DEPLOY_DIR 'ci-app.log') -ErrorAction SilentlyContinue; Get-Content (Join-Path $env:DEPLOY_DIR 'ci-app-error.log') -ErrorAction SilentlyContinue; exit 1 }; try { $r = Invoke-WebRequest -Uri ($env:BASE_URL + '/drivers') -UseBasicParsing -TimeoutSec 3; if ($r.StatusCode -eq 200) { $ready = $true; break } } catch {}; Start-Sleep -Seconds 2 }; if (-not $ready) { Write-Error 'Application did not become ready within 120 seconds'; Get-Content (Join-Path $env:DEPLOY_DIR 'ci-app.log') -ErrorAction SilentlyContinue; Get-Content (Join-Path $env:DEPLOY_DIR 'ci-app-error.log') -ErrorAction SilentlyContinue; exit 1 }; Write-Host 'Application is ready for Selenium tests.'"
                '''
            }
        }

        stage('Selenium Continuous Tests') {
            steps {
                echo 'Running Selenium browser tests against the CI application'
                bat '''
                "%PYTHON_EXE%" -c "import selenium; print('Selenium version:', selenium.__version__)"
                "%PYTHON_EXE%" -m unittest selenium-tests\\test_driver_roster.py -v
                '''
            }
        }
    }

    
        stage('Build Docker Image') {
            steps {
                bat '''
                docker build --pull -t driver-shift-roster:%BUILD_NUMBER% .
                if errorlevel 1 exit /b 1
                docker tag driver-shift-roster:%BUILD_NUMBER% driver-shift-roster:latest
                if errorlevel 1 exit /b 1
                docker image inspect driver-shift-roster:%BUILD_NUMBER%
                if errorlevel 1 exit /b 1
                '''
            }
        }

        stage('Deploy Docker Container') {
            steps {
                bat '''
                if not defined DB_PASSWORD (
                    echo ERROR: DB_PASSWORD is not configured in Jenkins.
                    exit /b 1
                )

                docker rm -f driver-shift-roster-jenkins 2>NUL
                docker run -d --name driver-shift-roster-jenkins -p 8085:8081 -e DB_USERNAME=root -e "DB_PASSWORD=%DB_PASSWORD%" -e SPRING_DATASOURCE_URL=jdbc:mysql://host.docker.internal:3306/driver_shift_roster driver-shift-roster:%BUILD_NUMBER%
                if errorlevel 1 exit /b 1

                powershell -NoProfile -ExecutionPolicy Bypass -Command "$ready = $false; for ($i = 0; $i -lt 60; $i++) { try { $r = Invoke-WebRequest -Uri 'http://localhost:8085/drivers' -UseBasicParsing -TimeoutSec 3; if ($r.StatusCode -eq 200) { $ready = $true; break } } catch {}; Start-Sleep -Seconds 2 }; if (-not $ready) { docker logs --tail 80 driver-shift-roster-jenkins; exit 1 }; Write-Host 'Docker deployment health check passed.'"
                if errorlevel 1 exit /b 1
                '''
            }
        }


    post {
        always {
            echo 'Cleaning up the CI test application, if it was started.'
            bat '''
            powershell -NoProfile -ExecutionPolicy Bypass -Command "$pidFile = Join-Path $env:DEPLOY_DIR 'ci-app.pid'; if (Test-Path $pidFile) { $appPid = 0; try { $appPid = [int](Get-Content $pidFile -Raw).Trim() } catch {}; if ($appPid -gt 0) { $p = Get-Process -Id $appPid -ErrorAction SilentlyContinue; if ($p -and $p.ProcessName -eq 'java') { Stop-Process -Id $appPid -Force; Write-Host 'CI application stopped.' } }; Remove-Item $pidFile -Force -ErrorAction SilentlyContinue }"
            '''
        }

        success {
            echo 'Build, Java tests, packaging and Selenium tests completed successfully.'
        }

        failure {
            echo 'Pipeline failed. Check the stage logs and CI application logs.'
        }
    }
}
