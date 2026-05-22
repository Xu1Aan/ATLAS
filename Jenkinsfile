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
        HARBOR_CREDENTIALS_ID = '69737d03-6882-4c4d-7bb5c8da07c1'

        HELM_CHART_BASE = '/root/app/helm/app'
        SSH_KEY_PATH = '/var/jenkins_home/.ssh/id_rsa'
        REMOTE_USER = 'root'
        REMOTE_HOST = '10.20.124.50'
        REMOTE_K8S_WORKDIR = '/root/app/k8s/dwg2mvt'

        BACKEND_IMAGE_NAME = 'sw-dwg2mvt-backend-v1'
        BACKEND_K8S_NAME = 'sw-dwg2mvt-backend-v1'
        BACKEND_HELM_RELEASE = 'dwg2mvt-backend'

        PYTHON_BASE_IMAGE = 'docker.m.daocloud.io/library/python:3.11-slim-bookworm'
        APT_MIRROR = 'mirrors.aliyun.com'
        PIP_INDEX_URL = 'https://pypi.tuna.tsinghua.edu.cn/simple'
        GNU_MIRROR = 'https://mirrors.ustc.edu.cn/gnu'

        BACKEND_WORK_DIR = '/data'
        BACKEND_GEOSERVER_URL = 'http://geoserver.sw-dev.svc.cluster.local/geoserver'
        BACKEND_GEOSERVER_PUBLIC_URL = '/public/dwgconvert/geoserver'
        BACKEND_GEOSERVER_USER = 'admin'
        BACKEND_GEOSERVER_PASSWORD = 'geoserver'

        GEOSERVER_MANIFEST_DIR = 'k8s/geoserver'
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
                    echo '=== Push Backend Image ==='
                    def dockerImage = "${env.HARBOR_REGISTRY}/${env.HARBOR_PROJECT}/${env.BACKEND_IMAGE_NAME}:${env.APP_ENV}-${env.APP_VERSION}"
                    sh """#!/bin/sh
set -eu
echo "Local image tag: ${env.BACKEND_IMAGE_NAME}:${env.APP_ENV}-${env.APP_VERSION}"
docker image inspect ${env.BACKEND_IMAGE_NAME}:${env.APP_ENV}-${env.APP_VERSION} >/dev/null
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
echo "Target registry image: ${dockerImage}"
docker login ${env.HARBOR_REGISTRY} -u "${HARBOR_USERNAME}" -p "${HARBOR_PASSWORD}"
docker tag ${env.BACKEND_IMAGE_NAME}:${env.APP_ENV}-${env.APP_VERSION} ${dockerImage}
docker push ${dockerImage}
"""
                    }
                }
            }
        }

        stage('Deploy Backend To K8S') {
            steps {
                script {
                    echo '=== Deploy Backend To K8S ==='
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
                        ",service.port=80" +
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
                        ",env[4].value=${env.BACKEND_GEOSERVER_PASSWORD}"

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

        stage('Deploy GeoServer To K8S') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                    sh """#!/bin/sh
set -eu
set -x
echo "=== Deploy GeoServer To K8S ==="
test -d ${env.WORKSPACE}/${env.GEOSERVER_MANIFEST_DIR}
ls -la ${env.WORKSPACE}/${env.GEOSERVER_MANIFEST_DIR}
ssh -i ${env.SSH_KEY_PATH} -o StrictHostKeyChecking=no ${env.REMOTE_USER}@${env.REMOTE_HOST} "mkdir -p '${env.REMOTE_K8S_WORKDIR}' && rm -rf '${env.REMOTE_K8S_WORKDIR}/geoserver'"
scp -i ${env.SSH_KEY_PATH} -o StrictHostKeyChecking=no -r ${env.WORKSPACE}/${env.GEOSERVER_MANIFEST_DIR} ${env.REMOTE_USER}@${env.REMOTE_HOST}:${env.REMOTE_K8S_WORKDIR}/geoserver
ssh -i ${env.SSH_KEY_PATH} -o StrictHostKeyChecking=no ${env.REMOTE_USER}@${env.REMOTE_HOST} "kubectl apply -k '${env.REMOTE_K8S_WORKDIR}/geoserver' -n ${env.K8S_ENV} && kubectl rollout status deployment/geoserver -n ${env.K8S_ENV} --timeout=300s"
"""
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
