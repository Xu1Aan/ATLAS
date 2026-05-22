@Library('jenkins-shared-lib') _

pipeline {
    agent any

    environment {
        PROJECT_NAME = 'dwg2mvt'
        PROJECT_VERSION = 'v1'

        APP_ENV = 'dev'
        APP_VERSION = '1.0.0'
        APP_REPLICAS = '1'
        K8S_ENV = 'sw-dev'

        GIT_REPO = 'http://10.20.124.70/digital-design/dwg2mvt.git'
        GIT_BRANCH = 'dev'

        HARBOR_REGISTRY = '10.20.124.50:5000'
        HARBOR_PROJECT = 'swhi'
        HARBOR_CREDENTIALS_ID = '69737d03-6882-4c4a-8c4d-7bb5c8da07c1'

        HELM_CHART_BASE = '/root/app/helm/app'
        SSH_KEY_PATH = '/var/jenkins_home/.ssh/id_rsa'
        REMOTE_USER = 'root'
        REMOTE_HOST = '10.20.124.50'

        BACKEND_IMAGE_NAME = 'sw-dwg2mvt-backend-v1'
        BACKEND_K8S_NAME = 'sw-dwg2mvt-backend-v1'
        BACKEND_HELM_RELEASE = 'dwg2mvt-backend'
        BACKEND_APP_PORT = '8000'

        PYTHON_BASE_IMAGE = 'docker.m.daocloud.io/library/python:3.11-slim-bookworm'
        NODE_BASE_IMAGE = 'docker.m.daocloud.io/library/node:20-alpine'
        APT_MIRROR = 'mirrors.aliyun.com'
        PIP_INDEX_URL = 'https://pypi.tuna.tsinghua.edu.cn/simple'
        NPM_REGISTRY = 'https://registry.npmmirror.com'
        GNU_MIRROR = 'https://mirrors.ustc.edu.cn/gnu'

        FRONTEND_BUILD_IMAGE = 'dwg2mvt-frontend-build'
        FRONTEND_BUILD_CONTAINER = 'dwg2mvt-frontend-build-tmp'
        FRONTEND_DIST_DIR = 'frontend-dist'
        FRONTEND_REMOTE_DIR = '/root/app/static/dwgconvert'
        FRONTEND_PUBLIC_BASE = '/public/dwgconvert/'
        FRONTEND_API_BASE = '/public/dwgconvert/api'
        BACKEND_GEOSERVER_PUBLIC_URL = '/public/dwgconvert/geoserver'
    }

    stages {
        stage('Checkout Code') {
            steps {
                deleteDir()
                checkout scmGit(
                    branches: [[name: '*/' + env.GIT_BRANCH]],
                    extensions: [cleanBeforeCheckout()],
                    userRemoteConfigs: [[credentialsId: 'jenkins', url: env.GIT_REPO]]
                )
                sh '''#!/bin/sh
set -eu
git rev-parse HEAD
git log -1 --oneline
'''
            }
        }

        stage('Build Frontend Static') {
            steps {
                sh """#!/bin/sh
set -eu
docker build \\
  --target build \\
  --build-arg NODE_BASE_IMAGE=${env.NODE_BASE_IMAGE} \\
  --build-arg NPM_REGISTRY=${env.NPM_REGISTRY} \\
  --build-arg VITE_APP_BASE=${env.FRONTEND_PUBLIC_BASE} \\
  --build-arg VITE_API_BASE=${env.FRONTEND_API_BASE} \\
  -t ${env.FRONTEND_BUILD_IMAGE} \\
  ./frontend

docker rm -f ${env.FRONTEND_BUILD_CONTAINER} >/dev/null 2>&1 || true
rm -rf ${env.FRONTEND_DIST_DIR}
mkdir -p ${env.FRONTEND_DIST_DIR}
docker create --name ${env.FRONTEND_BUILD_CONTAINER} ${env.FRONTEND_BUILD_IMAGE} >/dev/null
docker cp ${env.FRONTEND_BUILD_CONTAINER}:/app/dist/. ${env.FRONTEND_DIST_DIR}/
docker rm -f ${env.FRONTEND_BUILD_CONTAINER} >/dev/null
ls -la ${env.FRONTEND_DIST_DIR}
"""
            }
        }

        stage('Build Backend Image') {
            steps {
                sh """#!/bin/sh
set -eu
docker build \\
  --build-arg PYTHON_BASE_IMAGE=${env.PYTHON_BASE_IMAGE} \\
  --build-arg APT_MIRROR=${env.APT_MIRROR} \\
  --build-arg PIP_INDEX_URL=${env.PIP_INDEX_URL} \\
  --build-arg GNU_MIRROR=${env.GNU_MIRROR} \\
  -t ${env.BACKEND_IMAGE_NAME}:${env.APP_ENV}-${env.APP_VERSION} \\
  ./backend
"""
            }
        }

        stage('Push Backend Image') {
            steps {
                script {
                    def dockerImage = "${env.HARBOR_REGISTRY}/${env.HARBOR_PROJECT}/${env.BACKEND_IMAGE_NAME}:${env.APP_ENV}-${env.APP_VERSION}"
                    withCredentials([
                        usernamePassword(
                            credentialsId: env.HARBOR_CREDENTIALS_ID,
                            passwordVariable: 'HARBOR_PASSWORD',
                            usernameVariable: 'HARBOR_USERNAME',
                        ),
                    ]) {
                        sh "docker login ${env.HARBOR_REGISTRY} -u ${HARBOR_USERNAME} -p ${HARBOR_PASSWORD}"
                    }
                    sh """#!/bin/sh
set -eu
docker tag ${env.BACKEND_IMAGE_NAME}:${env.APP_ENV}-${env.APP_VERSION} ${dockerImage}
docker push ${dockerImage}
"""
                }
            }
        }

        stage('Deploy Frontend Static') {
            steps {
                sh """#!/bin/sh
set -eu
ssh -i ${env.SSH_KEY_PATH} -o StrictHostKeyChecking=no ${env.REMOTE_USER}@${env.REMOTE_HOST} "rm -rf '${env.FRONTEND_REMOTE_DIR}.tmp' && mkdir -p '${env.FRONTEND_REMOTE_DIR}.tmp'"
scp -i ${env.SSH_KEY_PATH} -o StrictHostKeyChecking=no -r ${env.FRONTEND_DIST_DIR}/. ${env.REMOTE_USER}@${env.REMOTE_HOST}:${env.FRONTEND_REMOTE_DIR}.tmp/
ssh -i ${env.SSH_KEY_PATH} -o StrictHostKeyChecking=no ${env.REMOTE_USER}@${env.REMOTE_HOST} "mkdir -p '${env.FRONTEND_REMOTE_DIR}' && rm -rf '${env.FRONTEND_REMOTE_DIR}'/* && cp -r '${env.FRONTEND_REMOTE_DIR}.tmp'/. '${env.FRONTEND_REMOTE_DIR}'/ && rm -rf '${env.FRONTEND_REMOTE_DIR}.tmp'"
"""
            }
        }

        stage('Deploy Backend To K8S') {
            steps {
                script {
                    def sshCommand = "ssh -i ${env.SSH_KEY_PATH} -o StrictHostKeyChecking=no ${env.REMOTE_USER}@${env.REMOTE_HOST} "
                    def chartPrimary = "${env.HELM_CHART_BASE}/${env.BACKEND_IMAGE_NAME}"
                    def chartFallback = "${env.HELM_CHART_BASE}/sw-dwg2mvt-backend-${env.APP_ENV}"
                    def dockerImage = "${env.HARBOR_REGISTRY}/${env.HARBOR_PROJECT}/${env.BACKEND_IMAGE_NAME}"
                    def envAppVersion = "${env.APP_ENV}-${env.APP_VERSION}"

                    def helmSet =
                        "fullnameOverride=${env.BACKEND_K8S_NAME}" +
                        ",image.repository=${dockerImage}" +
                        ",image.tag=${envAppVersion}" +
                        ',image.pullPolicy=Always' +
                        ",service.port=${env.BACKEND_APP_PORT}" +
                        ",replicaCount=${env.APP_REPLICAS}" +
                        ",env[0].name=APP_GEOSERVER_PUBLIC_URL" +
                        ",env[0].value=${env.BACKEND_GEOSERVER_PUBLIC_URL}"

                    def helmCmdPrimary =
                        'helm upgrade --install ' +
                            env.BACKEND_HELM_RELEASE + ' ' + chartPrimary +
                            ' --set ' + helmSet +
                            ' --namespace ' + env.K8S_ENV +
                            ' --create-namespace'

                    def helmCmdFallback =
                        'helm upgrade --install ' +
                            env.BACKEND_HELM_RELEASE + ' ' + chartFallback +
                            ' --set ' + helmSet +
                            ' --namespace ' + env.K8S_ENV +
                            ' --create-namespace'

                    try {
                        sh "${sshCommand} \"test -d '${chartPrimary}'\""
                        sh "${sshCommand} \"${helmCmdPrimary}\""
                    } catch (exc) {
                        echo 'Primary backend chart not found, trying fallback chart directory.'
                        sh "${sshCommand} \"test -d '${chartFallback}'\""
                        sh "${sshCommand} \"${helmCmdFallback}\""
                    }
                }
            }
        }
    }

    post {
        success {
            sh 'echo "Success"'
        }
        failure {
            sh 'echo "Failure"'
        }
        always {
            sh """#!/bin/sh
docker rm -f ${env.FRONTEND_BUILD_CONTAINER} >/dev/null 2>&1 || true
"""
        }
    }
}
