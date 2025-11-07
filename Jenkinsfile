pipeline {
  agent any

  environment {
    VENV = "${WORKSPACE}/.venv"
    PATH = "${VENV}/bin:${PATH}"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Python Dependencies') {
      steps {
        sh 'python3 -m venv ${VENV}'
        sh '. ${VENV}/bin/activate && python -m pip install --upgrade pip'
        sh '. ${VENV}/bin/activate && pip install -r backend/requirements.txt'
      }
    }

    stage('Node Dependencies') {
      steps {
        sh 'npm install --prefix frontend'
      }
    }

    stage('Code Generation') {
      steps {
        sh '. ${VENV}/bin/activate && python scripts/codegen_grpc.py'
      }
    }

    stage('CI Suite') {
      steps {
        sh '. ${VENV}/bin/activate && make ci'
      }
    }
  }
}
