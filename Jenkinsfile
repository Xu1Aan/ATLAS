@Library('jenkins-shared-lib') _

pipeline {
    agent any

    environment {
        PROJECT_NAME = 'dwg2mvt'
        PROJECT_VERSION = 'v1'

        APP_ENV = 'dev'
        APP_REPLICAS = '1'
        K8S_ENV = 'sw-dev'
        HELM_CHART_BASE = '/root/app/helm/app'

        IMG_PREFIX = 'sw'
        APP_PREFIX = 'sw'
        APP_VERSION = '1.0.0'

        GIT_REPO = 'http://10.20.124.70/digital-design/dwg2mvt.git'
        GIT_BRANCH = 'dev'

        // Comma-separated logical services to build/deploy.
        // Supported values in this repo: backend, web
        APP_LIST = 'backend,web'

        // Default exposed container ports used by Helm --set service.port
        BACKEND_APP_PORT = '8000'
        WEB_APP_PORT = '80'

        // Harbor / deploy target
        HARBOR_REGISTRY = '10.20.124.50:5000'
        HARBOR_PROJECT = 'swhi'
        HARBOR_CREDENTIALS_ID = '69737d03-6882-4c4a-8c4d-7bb5c8da07c1'

        // Domestic mirrors for faster CI builds. Replace with your own Harbor cache if available.
        PYTHON_BASE_IMAGE = 'docker.m.daocloud.io/library/python:3.11-slim-bookworm'
        NODE_BASE_IMAGE = 'docker.m.daocloud.io/library/node:20-alpine'
        NGINX_BASE_IMAGE = 'docker.m.daocloud.io/library/nginx:1.27-alpine'
        APT_MIRROR = 'mirrors.aliyun.com'
        PIP_INDEX_URL = 'https://pypi.tuna.tsinghua.edu.cn/simple'
        NPM_REGISTRY = 'https://registry.npmmirror.com'
        GNU_MIRROR = 'https://mirrors.ustc.edu.cn/gnu'

        REMOTE_USER = 'root'
        REMOTE_HOST = '10.20.124.50'
        SSH_KEY_PATH = '/var/jenkins_home/.ssh/id_rsa'
    }

    stages {
        stage('Checkout Code') {
            steps {
                sh 'pwd'
                checkout scmGit(
                    branches: [[name: '*/' + env.GIT_BRANCH]],
                    extensions: [],
                    userRemoteConfigs: [[credentialsId: 'jenkins', url: env.GIT_REPO]]
                )
            }
        }

        stage('Backend Image Build Check') {
            steps {
                sh """\
set -eu
docker build \
  --build-arg PYTHON_BASE_IMAGE=${env.PYTHON_BASE_IMAGE} \
  --build-arg APT_MIRROR=${env.APT_MIRROR} \
  --build-arg PIP_INDEX_URL=${env.PIP_INDEX_URL} \
  --build-arg GNU_MIRROR=${env.GNU_MIRROR} \
  -t ${env.PROJECT_NAME}-backend-ci-check \
  ./backend
"""
            }
        }

        stage('Frontend Image Build Check') {
            steps {
                sh """\
set -eu
docker build \
  --build-arg NODE_BASE_IMAGE=${env.NODE_BASE_IMAGE} \
  --build-arg NGINX_BASE_IMAGE=${env.NGINX_BASE_IMAGE} \
  --build-arg NPM_REGISTRY=${env.NPM_REGISTRY} \
  -t ${env.PROJECT_NAME}-web-ci-check \
  ./frontend
"""
            }
        }

        stage('Docker Build and Push') {
            steps {
                script {
                    def serviceConfigs = [
                        backend: [
                            imageName : "${env.IMG_PREFIX}-${env.PROJECT_NAME}-backend-${env.PROJECT_VERSION}",
                            buildDir  : "${env.WORKSPACE}/backend",
                            appPort   : env.BACKEND_APP_PORT
                        ],
                        web: [
                            imageName : "${env.IMG_PREFIX}-${env.PROJECT_NAME}-web-${env.PROJECT_VERSION}",
                            buildDir  : "${env.WORKSPACE}/frontend",
                            appPort   : env.WEB_APP_PORT
                        ]
                    ]

                    withCredentials([
                        usernamePassword(
                            credentialsId: env.HARBOR_CREDENTIALS_ID,
                            passwordVariable: 'HARBOR_PASSWORD',
                            usernameVariable: 'HARBOR_USERNAME',
                        ),
                    ]) {
                        sh "docker login ${env.HARBOR_REGISTRY} -u ${HARBOR_USERNAME} -p ${HARBOR_PASSWORD}"
                    }

                    def services = env.APP_LIST.tokenize(',') as List
                    services.each { rawName ->
                        def serviceName = rawName.trim()
                        def cfg = serviceConfigs[serviceName]
                        if (cfg == null) {
                            error "Unsupported APP_LIST item '${serviceName}'. Supported values: ${serviceConfigs.keySet().join(', ')}"
                        }

                        def envAppVersion = "${env.APP_ENV}-${env.APP_VERSION}"
                        def dockerImage = "${env.HARBOR_REGISTRY}/${env.HARBOR_PROJECT}/${cfg.imageName}:${envAppVersion}"

                        sh "docker rmi -f ${dockerImage} >/dev/null 2>&1 || true"
                        if (serviceName == 'backend') {
                            sh """\
set -eu
docker build \
  --build-arg PYTHON_BASE_IMAGE=${env.PYTHON_BASE_IMAGE} \
  --build-arg APT_MIRROR=${env.APT_MIRROR} \
  --build-arg PIP_INDEX_URL=${env.PIP_INDEX_URL} \
  --build-arg GNU_MIRROR=${env.GNU_MIRROR} \
  -t ${dockerImage} \
  ${cfg.buildDir}
"""
                        } else if (serviceName == 'web') {
                            sh """\
set -eu
docker build \
  --build-arg NODE_BASE_IMAGE=${env.NODE_BASE_IMAGE} \
  --build-arg NGINX_BASE_IMAGE=${env.NGINX_BASE_IMAGE} \
  --build-arg NPM_REGISTRY=${env.NPM_REGISTRY} \
  -t ${dockerImage} \
  ${cfg.buildDir}
"""
                        } else {
                            error "Unsupported APP_LIST item '${serviceName}'."
                        }
                        sh "docker push ${dockerImage}"
                    }
                }
            }
        }

        stage('Deploy to Server') {
            steps {
                script {
                    def serviceConfigs = [
                        backend: [
                            imageName : "${env.IMG_PREFIX}-${env.PROJECT_NAME}-backend-${env.PROJECT_VERSION}",
                            appName   : "${env.PROJECT_NAME}-backend-${env.PROJECT_VERSION}",
                            appPort   : env.BACKEND_APP_PORT
                        ],
                        web: [
                            imageName : "${env.IMG_PREFIX}-${env.PROJECT_NAME}-web-${env.PROJECT_VERSION}",
                            appName   : "${env.PROJECT_NAME}-web-${env.PROJECT_VERSION}",
                            appPort   : env.WEB_APP_PORT
                        ]
                    ]

                    def sshCommand =
                        "ssh -i ${env.SSH_KEY_PATH} -o StrictHostKeyChecking=no ${env.REMOTE_USER}@${env.REMOTE_HOST} "

                    sh "${sshCommand} \"ls -la ${env.HELM_CHART_BASE}\""

                    def services = env.APP_LIST.tokenize(',') as List
                    services.each { rawName ->
                        def serviceName = rawName.trim()
                        def cfg = serviceConfigs[serviceName]
                        if (cfg == null) {
                            error "Unsupported APP_LIST item '${serviceName}'. Supported values: ${serviceConfigs.keySet().join(', ')}"
                        }

                        def envAppVersion = "${env.APP_ENV}-${env.APP_VERSION}"
                        def helmRelease = "${env.K8S_ENV}-${cfg.appName}"
                        def chartPrimary = "${env.HELM_CHART_BASE}/${cfg.imageName}"
                        def fallbackChartName = "${env.APP_PREFIX}-${env.PROJECT_NAME}-${serviceName}-${env.APP_ENV}"
                        def chartFallback = "${env.HELM_CHART_BASE}/${fallbackChartName}"

                        def helmSet =
                            "image.repository=${env.HARBOR_REGISTRY}/${env.HARBOR_PROJECT}/${cfg.imageName}" +
                            ",image.tag=${envAppVersion}" +
                            ',image.pullPolicy=Always' +
                            ",service.port=${cfg.appPort}" +
                            ",replicaCount=${env.APP_REPLICAS}"

                        def helmCmdPrimary =
                            'helm upgrade --install ' +
                                helmRelease + ' ' + chartPrimary +
                                ' --set ' + helmSet +
                                ' --namespace ' + env.K8S_ENV +
                                ' --create-namespace'

                        def helmCmdFallback =
                            'helm upgrade --install ' +
                                helmRelease + ' ' + chartFallback +
                                ' --set ' + helmSet +
                                ' --namespace ' + env.K8S_ENV +
                                ' --create-namespace'

                        try {
                            sh "${sshCommand} \"test -d '${chartPrimary}'\""
                            sh "${sshCommand} \"${helmCmdPrimary}\""
                        } catch (exc) {
                            echo "Primary chart install failed for ${serviceName}, trying fallback chart directory."
                            currentBuild.result = 'SUCCESS'
                            sh "${sshCommand} \"test -d '${chartFallback}'\""
                            sh "${sshCommand} \"${helmCmdFallback}\""
                        }

                        echo "Helm Release: ${helmRelease}, image: ${env.HARBOR_REGISTRY}/${env.HARBOR_PROJECT}/${cfg.imageName}:${envAppVersion}"
                        currentBuild.result = 'SUCCESS'
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
