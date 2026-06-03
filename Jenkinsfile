@Library('jenkins-shared-lib') _

pipeline {
    agent any

    environment {
        PROJECT_VERSION = 'v1'
        APP_ENV = 'dev'
        APP_REPLICAS = '1'
        K8S_ENV = 'sw-dev'
        APP_VERSION = '1.0.0'
        APP_PORT = '80'

        GIT_REPO = 'http://10.20.124.70/digital-design/dwg2mvt.git'
        GIT_BRANCH = 'dev'

        HELM_CHART_BASE = '/root/app/helm/app'
        IMG_PREFIX = 'sw'
        APP_PREFIX = 'sw'
        APP_LIST = 'dwg2mvt-backend'

        HARBOR_REGISTRY = '10.20.124.50:5000'
        HARBOR_PROJECT = 'swhi'
        HARBOR_CREDENTIALS_ID = '69737d03-6882-4c4a-8c4d-7bb5c8da07c1'

        REMOTE_USER = 'root'
        REMOTE_HOST = '10.20.124.50'
        SSH_KEY_PATH = '/var/jenkins_home/.ssh/id_rsa'
        REMOTE_K8S_WORKDIR = '/root/app/k8s/dwg2mvt'

        PYTHON_BASE_IMAGE = 'docker.m.daocloud.io/library/python:3.11-slim-bookworm'
        APT_MIRROR = 'mirrors.aliyun.com'
        PIP_INDEX_URL = 'https://pypi.tuna.tsinghua.edu.cn/simple'
        GNU_MIRROR = 'https://mirrors.ustc.edu.cn/gnu'

        BACKEND_IMAGE_NAME = 'sw-dwg2mvt-backend-v1'
        BACKEND_RELEASE = 'dwg2mvt-backend'
        BACKEND_FULLNAME = 'sw-dwg2mvt-backend-v1'
        BACKEND_CHART_FALLBACK = 'sw-dwg2mvt-backend-dev'

        BACKEND_WORK_DIR = '/data'
        BACKEND_GEOSERVER_URL = 'http://10.20.124.71:18081/geoserver'
        BACKEND_GEOSERVER_PUBLIC_URL = 'http://10.20.124.50:30030/public/dwgconvert/geoserver'
        BACKEND_GEOSERVER_USER = 'admin'
        BACKEND_GEOSERVER_PASSWORD = 'geoserver'
        BACKEND_MINIO_ENDPOINT = 'http://10.20.124.73:9000'
        BACKEND_MINIO_ACCESS_KEY = 'VyKNZUaCYan5nQ23LsHB'
        BACKEND_MINIO_SECRET_KEY = 'VL2K8AAyo9x0VLOVmJb7yRoRLqrqJvjJ64oHqaAz'
        BACKEND_MINIO_SECURE = 'false'
        BACKEND_MINIO_PATH_STYLE = 'true'
        BACKEND_MINIO_REGION = ''
    }

    stages {
        stage('Checkout Code') {
            steps {
                sh 'pwd'
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

        stage('Build Backend Image') {
            steps {
                script {
                    def localImage = "${env.BACKEND_IMAGE_NAME}:${env.APP_ENV}-${env.APP_VERSION}"
                    sh """#!/bin/sh
set -eu
echo "=== Build Backend Image ==="
docker build \\
  --build-arg PYTHON_BASE_IMAGE=${env.PYTHON_BASE_IMAGE} \\
  --build-arg APT_MIRROR=${env.APT_MIRROR} \\
  --build-arg PIP_INDEX_URL=${env.PIP_INDEX_URL} \\
  --build-arg GNU_MIRROR=${env.GNU_MIRROR} \\
  --build-arg APP_ENV=${env.APP_ENV} \\
  -t ${localImage} \\
  ./backend
docker image inspect ${localImage} >/dev/null
"""
                }
            }
        }

        stage('Push Backend Image') {
            steps {
                script {
                    def localImage = "${env.BACKEND_IMAGE_NAME}:${env.APP_ENV}-${env.APP_VERSION}"
                    def remoteImage = "${env.HARBOR_REGISTRY}/${env.HARBOR_PROJECT}/${env.BACKEND_IMAGE_NAME}:${env.APP_ENV}-${env.APP_VERSION}"

                    echo '=== Push Backend Image ==='
                    sh """#!/bin/sh
set -eu
echo "Local image tag: ${localImage}"
docker image inspect ${localImage} >/dev/null
"""

                    withCredentials([
                        usernamePassword(
                            credentialsId: env.HARBOR_CREDENTIALS_ID,
                            passwordVariable: 'HARBOR_PASSWORD',
                            usernameVariable: 'HARBOR_USERNAME',
                        ),
                    ]) {
                        sh """#!/bin/sh
set -eux
docker login ${env.HARBOR_REGISTRY} -u "${HARBOR_USERNAME}" -p "${HARBOR_PASSWORD}"
docker tag ${localImage} ${remoteImage}
docker push ${remoteImage}
"""
                    }
                }
            }
        }

        stage('Deploy Backend To K8S') {
            steps {
                script {
                    def remoteUser = env.REMOTE_USER
                    def remoteHost = env.REMOTE_HOST
                    def keyPath = env.SSH_KEY_PATH
                    def sshCommand = "ssh -i ${keyPath} -o StrictHostKeyChecking=no ${remoteUser}@${remoteHost} "

                    def services = env.APP_LIST.tokenize(',') as List
                    services.each { serviceName ->
                        def sn = serviceName.trim()
                        def envAppVersion = env.APP_ENV + '-' + env.APP_VERSION
                        def appImageName = env.IMG_PREFIX + "-${sn.toLowerCase()}-${env.PROJECT_VERSION}"
                        def helmRelease = env.BACKEND_RELEASE
                        def ns = env.K8S_ENV

                        def chartPrimary = "${env.HELM_CHART_BASE}/${appImageName}"
                        def chartFallback = "${env.HELM_CHART_BASE}/${env.BACKEND_CHART_FALLBACK}"

                        def helmSet =
                            "fullnameOverride=${env.BACKEND_FULLNAME}" +
                            ",image.repository=${env.HARBOR_REGISTRY}/${env.HARBOR_PROJECT}/${appImageName}" +
                            ",image.tag=${envAppVersion}" +
                            ',image.pullPolicy=Always' +
                            ",service.port=${env.APP_PORT}" +
                            ",replicaCount=${env.APP_REPLICAS}" +
                            ",env[0].name=APP_WORK_DIR" +
                            ",env[0].value=${env.BACKEND_WORK_DIR}" +
                            ",env[1].name=APP_GEOSERVER_URL" +
                            ",env[1].value=${env.BACKEND_GEOSERVER_URL}" +
                            ",env[2].name=APP_GEOSERVER_PUBLIC_URL" +
                            ",env[2].value=${env.BACKEND_GEOSERVER_PUBLIC_URL}" +
                            ",env[3].name=APP_GEOSERVER_USER" +
                            ",env[3].value=${env.BACKEND_GEOSERVER_USER}" +
                            ",env[4].name=APP_GEOSERVER_PASSWORD" +
                            ",env[4].value=${env.BACKEND_GEOSERVER_PASSWORD}" +
                            ",env[5].name=APP_MINIO_ENDPOINT" +
                            ",env[5].value=${env.BACKEND_MINIO_ENDPOINT}" +
                            ",env[6].name=APP_MINIO_ACCESS_KEY" +
                            ",env[6].value=${env.BACKEND_MINIO_ACCESS_KEY}" +
                            ",env[7].name=APP_MINIO_SECRET_KEY" +
                            ",env[7].value=${env.BACKEND_MINIO_SECRET_KEY}" +
                            ",env[8].name=APP_MINIO_SECURE" +
                            ",env[8].value=${env.BACKEND_MINIO_SECURE}" +
                            ",env[9].name=APP_MINIO_PATH_STYLE" +
                            ",env[9].value=${env.BACKEND_MINIO_PATH_STYLE}" +
                            ",env[10].name=APP_MINIO_REGION" +
                            ",env[10].value=${env.BACKEND_MINIO_REGION}"

                        def helmCmdPrimary =
                            'helm upgrade --install ' +
                                helmRelease + ' ' + chartPrimary +
                                ' --set ' + helmSet +
                                ' --namespace ' + ns +
                                ' --create-namespace'

                        def helmCmdFallback =
                            'helm upgrade --install ' +
                                helmRelease + ' ' + chartFallback +
                                ' --set ' + helmSet +
                                ' --namespace ' + ns +
                                ' --create-namespace'

                        sh "${sshCommand} \"ls -la ${env.HELM_CHART_BASE}\""

                        try {
                            sh "${sshCommand} \"test -d '${chartPrimary}'\""
                            sh "${sshCommand} \"${helmCmdPrimary}\""
                        } catch (exc) {
                            echo 'Primary chart install failed, trying fallback chart directory.'
                            sh "${sshCommand} \"test -d '${chartFallback}'\""
                            sh "${sshCommand} \"${helmCmdFallback}\""
                        }

                        echo "Helm Release: ${helmRelease}, Image: ${env.HARBOR_REGISTRY}/${env.HARBOR_PROJECT}/${appImageName}:${envAppVersion}"
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
    }
}
