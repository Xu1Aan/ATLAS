
<p align="center">
  <img src="./assets/logowithword.png" alt="ATLAS 空间数据治理与服务发布平台" width="520" />
</p>
<p align="center">
  <a href="./README.md"><strong>中文</strong></a> ·
  <a href="./README.en.md">English</a>
</p>

<p align="center">
  <a href="https://github.com/Xu1Aan/ATLAS">
    <img src="https://img.shields.io/badge/GitHub-Xu1Aan%2FATLAS-181717?logo=github&logoColor=white" alt="GitHub Repository" />
  </a>
</p>

<p align="center">
  🌍 面向 CAD / GIS 源数据的一站式 Docker 化数据治理与地图服务发布平台<br />
  📤 上传或从 MinIO 导入源文件 → 🔄 自动转换 GeoPackage → 🗺️ 发布 MVT / WMTS 地图服务
</p>

<p align="center">
  <a href="#-关于-atlas">关于</a> ·
  <a href="#-架构概览">架构</a> ·
  <a href="#-项目亮点">亮点</a> ·
  <a href="#-适用场景">场景</a> ·
  <a href="#-交付成果">成果</a> ·
  <a href="#-技术栈">技术栈</a> ·
  <a href="#-核心能力">能力</a> ·
  <a href="#-快速启动">启动</a> ·
  <a href="#-使用指南">使用</a> ·
  <a href="#-生产部署">生产</a> ·
  <a href="#-常见问题">FAQ</a> ·
  <a href="#-作者与联系">联系</a> ·
  <a href="#-更多文档">文档</a>
</p>

---

## 📌 关于 ATLAS

**ATLAS**（空间数据治理与服务发布平台）解决的是工程与 GIS 领域的一个常见痛点：CAD 图纸、Shapefile、KML 等数据格式分散、难以直接在 Web 端浏览，传统方案又往往需要在每台机器上单独安装 LibreDWG、GDAL、GeoServer 等组件，部署和维护成本较高。

ATLAS 将这些能力封装为一套 **Docker 化全栈服务**。用户只需执行一条 Compose 命令，即可获得从**数据接入、格式转换、服务发布到地图预览**的完整链路。平台支持两种数据来源——浏览器本地上传与企业 MinIO 对象存储批量导入——转换结果以 **GeoPackage** 为标准中间格式，最终通过 **GeoServer** 发布为高性能的 **MVT 矢量切片** 与 **WMTS / 栅格** 服务，供前端或第三方系统调用。

**适合谁使用？** 如果您从事工程设计、测绘地理信息、智慧城市或园区信息化等工作，需要将 CAD 图档或 GIS 矢量数据快速发布为 Web 地图服务，又不想维护复杂的多组件安装环境，ATLAS 提供了一条开箱即用的路径。对于已具备 MinIO / 对象存储基础设施的团队，ATLAS 还可以作为轻量级的**空间数据治理节点**，嵌入现有数据流水线。

**与传统方案相比**，ATLAS 将「转换工具 + 地图服务器 + 对象存储 + Web 前端」整合为统一 Compose 栈，消除了跨机器路径挂载、手工配置 GeoServer 图层、前后端 URL 不一致等常见问题，显著缩短从原始文件到可浏览地图服务的交付周期。

---

## 🏗️ 架构概览

ATLAS 采用 **Docker Compose 单体栈** 架构：所有服务运行在同一 Compose 项目中，通过 Docker 内部网络通信。对外仅 **web** 服务映射宿主机端口（默认 `18081`），其余服务不直接暴露，有利于安全隔离与运维简化。

**api** 与 **geoserver** 之间通过 **REST API** 传递 GeoPackage，而非共享磁盘目录——这是容器化环境下更稳妥的解耦方式，也便于未来独立扩展 GeoServer 节点。MinIO 则作为可选但已内置的**源数据仓库**，使平台既能独立运行，也能无缝接入企业现有对象存储体系。

<p align="center">
  <img src="./assets/architecture.png" alt="ATLAS 空间数据治理与服务发布平台 — 总体架构图" width="900" />
</p>

<p align="center"><sub>📊 ATLAS 总体架构图 · 访问层 / 网关层 / 服务层 / 持久化层</sub></p>

架构自上而下分为四层：

- **访问层**：用户通过浏览器访问 Web 界面，完成上传、导入、任务查询与地图浏览；亦可通过 REST API 与平台集成。
- **网关层**：Nginx 统一承接 HTTP 请求，按路径分发至前端静态资源、API 或 GeoServer，对外呈现单一入口。
- **服务层**：api 负责转换与发布，geoserver 负责地图服务，minio 负责源文件存储；minio-init 在首次启动时自动创建默认 Bucket。
- **持久化层**：三个 Docker Volume 分别保存任务数据、GeoServer 配置与 MinIO 对象，容器重建后数据不丢失。

| 持久化卷 | 挂载服务 | 存储内容 |
|:---|:---|:---|
| 💼 `atlas_jobs` | api | 上传的原始文件、中间 DXF/GPKG 产物及任务状态元数据 |
| 🗺️ `geoserver_data` | geoserver | 工作区（默认 `atlas`）、图层定义、样式与切片相关配置 |
| 🗄️ `minio_data` | minio | 对象存储中的全部二进制文件 |

平台由以下容器化服务协同工作，彼此通过 Docker 内部 DNS 名称（如 `api`、`geoserver`、`minio`）通信：

| 服务 | 职责 | 对外暴露 |
|:---|:---|:---|
| 🌐 **web** | 托管 Vue 前端静态资源；作为 Nginx 反向代理，将 API 与 GeoServer 请求转发至内网服务 | 宿主机 `:18081` ✅ |
| ⚙️ **api** | 接收上传或 MinIO 导入请求，执行 LibreDWG/GDAL 转换，调用 GeoServer REST 发布图层，管理任务生命周期 | 仅容器内网 🔒 |
| 🗺️ **geoserver** | 基于 GeoServer 2.28 提供 MVT、WMTS 及栅格地图服务；内置 Vector Tiles 插件 | 经 web 反代 `/geoserver`，不直接映射端口 |
| 🗄️ **minio** | S3 兼容对象存储，存放待治理源文件；首次启动由 minio-init 创建 `atlas-data` Bucket | 仅容器内网 🔒 |

**启动依赖关系**：minio 就绪后执行 minio-init 初始化 Bucket → geoserver 通过 healthcheck → api 启动（需等待上述两者）→ web 最后对外提供服务。

> 📖 更详细的启动顺序、三条数据流说明与故障排查指南，请参阅 **[assets/README.md](./assets/README.md)**。

---

## ✨ 项目亮点

ATLAS 在「能转换」之外，更强调**可部署、可集成、可预览**。以下为核心差异化能力：

| | 亮点 | 说明 |
|:---:|:---|:---|
| 🐳 | **Docker 一键部署** | 根目录 `docker compose up` 即可拉起 MinIO、GeoServer、API、Web 四个核心服务，镜像内已集成 LibreDWG 与 GDAL，无需在宿主机单独安装依赖 |
| 📐 | **多格式统一治理** | 将 DWG、DXF、SHP（ZIP）、KML 等异构源数据统一转换为标准 GeoPackage，降低下游系统对接成本 |
| 🚀 | **自动发布地图服务** | 转换完成后自动调用 GeoServer REST API 创建工作区、数据存储与图层，无需手工登录控制台配置 |
| 🔗 | **双模式数据接入** | 既支持 Web 页面上传单文件快速验证，也支持从 MinIO 按 Bucket / Object 拉取，便于对接企业数据湖与批处理流水线 |
| 🌐 | **单端口统一网关** | 所有流量经 Nginx 网关（默认 `:18081`）转发，浏览器访问 `/api` 与 `/geoserver` 同源，避免跨域与内外网 URL 不一致导致的切片加载失败 |
| 🖥️ | **开箱即用地图预览** | 内置 Vue 3 + MapLibre GL 前端，转换任务完成后自动加载 MVT 或栅格图层，无需额外配置地图客户端 |

> 📍 **工程坐标支持**：针对国内常用的无带号高斯-克吕格坐标，平台可在转换阶段自动补带并投影至 WGS84，详见 [高斯-克吕格投影配置说明](./services/api/docs/gauss-kruger.md)。

---

## 🎯 适用场景

ATLAS 面向需要将「离线空间数据」快速变为「在线地图服务」的团队与个人，典型场景如下：

| 场景 | 说明 |
|:---|:---|
| 📋 **CAD 图纸 Web 化** | 设计院、施工方将 DWG / DXF 工程图发布为可在浏览器缩放、平移、叠加的 Web 地图，供项目汇报、协同审图或对外展示 |
| 🗄️ **MinIO 批量治理** | 已建设对象存储（MinIO / S3 兼容）的单位，按目录批量存放待治理文件，由 ATLAS 按需拉取、转换并发布，融入现有数据流水线 |
| 📦 **容器化交付** | 在测试、演示、POC 或内网环境中，以 Docker 镜像形式交付完整能力，避免在 Windows / Linux 上分别安装与调试原生工具链 |
| 🏢 **内网 GIS 中台** | 作为轻量级空间数据治理节点，统一承接多源 CAD/GIS 数据接入与服务发布，对外仅暴露一个 Web 端口，便于防火墙与网关管理 |

在实际项目中，上述场景往往可以组合使用：例如先将历史 DWG 批量入库 MinIO，再按需触发 ATLAS 转换发布，最终通过 Web 前端或第三方 GIS 系统消费已发布的 MVT / WMTS 服务。

---

## 🎁 交付成果

一次成功的转换任务完成后，ATLAS 会在平台内留下多层次的可交付成果，满足不同角色的使用需求：

| 成果类型 | 说明 | 典型使用者 |
|:---|:---|:---|
| 🗺️ **MVT 矢量切片** | 基于 Mapbox Vector Tiles 的高性能矢量瓦片，适合 CAD 线面要素的 Web 端流畅渲染 | 前端开发、Web GIS 应用 |
| 🖼️ **WMTS / 栅格服务** | 适用于 SHP 等需栅格化展示的数据，或 CAD 文本标注较多的场景 | 传统 GIS 客户端、对样式有特殊要求的场景 |
| 📦 **GeoPackage 文件** | 标准 OGC 矢量容器，可通过 API 下载，便于在 QGIS、ArcGIS 等桌面 GIS 中进一步分析 | 数据分析师、测绘工程师 |
| 📋 **任务元数据** | 包含 job_id、文件名、状态、图层列表、BBox 等，可通过 REST API 查询 | 系统集成、运维监控 |
| 🌐 **GeoServer 图层** | 持久化在 GeoServer 工作区中，容器重启后仍可通过 `/geoserver` 访问 | 长期在线服务、多应用共享 |

对于 CAD 类数据，平台优先尝试发布 **MVT 矢量切片**以获得最佳交互体验；对于 SHP 等 GIS 数据，可能同时提供矢量与栅格两种访问方式，具体取决于源数据特征与样式配置。

---

## 🔧 技术栈

平台各层职责清晰，便于二次开发与运维排障：

| 层级 | 技术 | 用途 |
|:---|:---|:---|
| 🖥️ 前端 | Vue 3 · TypeScript · MapLibre GL | 提供文件上传、MinIO 导入表单、历史任务列表及 MVT / 栅格地图交互预览 |
| 🌐 网关 | Nginx | 托管前端静态资源，并将 `/api/*`、`/geoserver/*` 反向代理至对应后端服务 |
| ⚙️ 后端 | FastAPI · Python 3.11 | 编排转换任务、暴露 REST API、通过 GeoServer REST 完成图层自动发布 |
| 📐 转换 | LibreDWG · GDAL | 完成 DWG→DXF→GeoPackage 的空间数据转换与坐标处理 |
| 🗺️ 地图 | GeoServer 2.28 · Vector Tiles | 发布 MVT 矢量切片、WMTS 与栅格瓦片，供 Web 或 GIS 客户端消费 |
| 🗄️ 存储 | MinIO | 提供 S3 兼容的对象存储，存放待转换源文件，默认 Bucket 为 `atlas-data` |
| 🐳 部署 | Docker Compose | 定义服务依赖、健康检查、环境变量与持久化卷，实现一键编排 |

技术选型遵循「成熟开源 + 容器友好」原则：转换层选用 LibreDWG 与 GDAL 这一对 CAD/GIS 领域广泛验证的组合；服务发布层选用 GeoServer 这一 OGC 标准支持最完善的开源地图服务器；前端选用 MapLibre GL 以获得无需插件的 Web 地图渲染能力。

---

## 🛠️ 核心能力

### 📁 支持格式

平台在转换层对常见 CAD / GIS 源格式做了统一封装，上传后由后端自动识别并选择对应处理链路：

| 格式 | 说明 |
|:---|:---|
| 📄 `.dwg` / `.dxf` | AutoCAD 等软件导出的 CAD 图纸；DWG 经 LibreDWG 转为 DXF 后再由 GDAL 写入 GeoPackage，保留线、面、文本等几何与属性 |
| 🗜️ `.zip` | 包含 `.shp` / `.dbf` / `.shx` 等文件的 Shapefile 压缩包，适用于 GIS 矢量数据批量入库 |
| 📍 `.kml` | Google Earth 等工具常用的 KML 矢量数据，可直接转换为 GeoPackage 并发布 |

上传时无需手动指定格式，api 服务会根据文件扩展名自动路由至相应的转换逻辑。对于 DWG 文件，若遇到版本兼容问题，建议先在 CAD 软件中导出为 DXF 再上传，通常可获得更高的转换成功率。

### 📥 数据接入方式

根据数据来源与集成深度，可选择以下两种接入模式：

| 方式 | 入口 | 典型用途 |
|:---|:---|:---|
| ⬆️ **本地上传** | Web 页面上传控件 | 单文件快速验证、临时转换、演示与手工处理 |
| ☁️ **MinIO 导入** | Web 面板填写 Bucket / Object Key，或调用 `POST /api/convert/minio` | 与企业数据湖、ETL 流水线、定时批处理任务集成，适合大批量自动化治理 |

两种模式共享同一套转换与发布引擎，区别仅在于**源文件的获取方式**。本地上传适合「人驱动」的交互式操作；MinIO 导入适合「系统驱动」的自动化流程——例如上游 ETL 任务将新 DWG 写入对象存储后，由调度系统调用 ATLAS API 触发转换。

### ⚡ 数据处理流水线

无论通过哪种方式接入，核心处理链路一致：

```
源文件（DWG/DXF/SHP/KML）
    → LibreDWG / GDAL 转换
    → GeoPackage（标准中间格式）
    → GeoServer REST 发布
    → MVT 矢量切片 / WMTS 栅格服务
    → Web 地图预览或第三方调用
```

**本地上传路径**：浏览器 → web 网关 → api 接收文件 → 转换发布 → 前端加载切片。

**MinIO 导入路径**：外部系统写入 MinIO → api 拉取对象 → 同上转换发布流程。

### 🔄 任务生命周期

每个转换请求在平台内以 **job（任务）** 为单位进行管理，典型状态流转如下：

| 状态 | 含义 |
|:---|:---|
| `pending` | 任务已创建，等待处理 |
| `converting` | 正在执行 LibreDWG / GDAL 格式转换 |
| `publishing` | 转换完成，正在向 GeoServer 发布图层 |
| `done` | 全部完成，可获取 MVT / WMTS 地址与 GeoPackage |
| `error` | 转换或发布失败，可通过 API 或前端查看错误信息 |

任务数据持久化在 `atlas_jobs` 卷中，容器重启后仍可通过 `GET /api/jobs` 查询历史记录，并在前端「历史任务」下拉框中重新加载已发布的地图。

### 📂 项目结构

```text
atlas/
├── docker-compose.yml      # 🐳 唯一部署入口，定义全部服务与卷
├── .env.example            # ⚙️ 环境变量模板，复制为 .env 后修改
├── assets/                 # 🎨 Logo、架构图及完整运维文档
└── services/
    ├── api/                # ⚙️ FastAPI 转换引擎与 GeoServer 发布逻辑
    ├── web/                # 🖥️ Vue 前端 + Nginx 网关配置
    └── geoserver/          # 🗺️ 内置 Vector Tiles 插件的 GeoServer 镜像
```

---

## 🚀 快速启动

### 📋 环境要求

部署前请确认宿主机满足以下条件：

| 项目 | 要求 |
|:---|:---|
| 🐳 Docker | Engine 24 及以上 |
| 📦 Compose | Compose v2（`docker compose` 子命令可用） |
| 💾 内存 | 建议可用内存 ≥ 4 GB；GeoServer 首次启动需加载插件与初始化数据目录，可能耗时 1–2 分钟 |
| 💽 磁盘 | 视数据量而定；Docker Volume 会随上传文件与发布图层增长 |

若在 Windows 上部署，建议使用 WSL2 后端或 Linux 虚拟机以获得更佳的文件 I/O 性能；macOS 与 Linux 可直接使用 Docker Desktop 或原生 Docker Engine。

### 👣 三步启动

```bash
# 1️⃣ 复制环境变量模板
cp .env.example .env

# 2️⃣ 编辑 .env
#    生产环境务必修改 MINIO_ROOT_PASSWORD、APP_GEOSERVER_PASSWORD
#    若通过非 localhost 访问，还需调整 APP_GEOSERVER_PUBLIC_URL

# 3️⃣ 构建镜像并后台启动全部服务
docker compose up --build -d
```

首次启动时，Compose 会按依赖顺序拉起 minio → minio-init → geoserver → api → web。api 镜像构建涉及 LibreDWG 源码编译，**首次 `--build` 可能耗时数分钟**，属正常现象。启动完成后，可通过 `docker compose ps` 观察各容器是否进入 **healthy** 状态。

### 🌐 访问地址

服务就绪后，可通过以下地址访问各功能入口：

| 用途 | 地址 |
|:---|:---|
| 🖥️ ATLAS 前端 | http://localhost:18081/ |
| 💚 API 健康检查 | http://localhost:18081/api/healthz |
| 🗺️ GeoServer 控制台 | http://localhost:18081/geoserver/web/ |

> 💡 **端口与账号**：宿主机端口由 `.env` 中 `ATLAS_HOST_PORT` 控制（默认 `18081`）。**ATLAS 平台登录**默认账号 `admin` / 密码 `admin`（演示用前端门户鉴权，不限制 `/api` 直连）。GeoServer 管理员账号对应 `APP_GEOSERVER_USER` / `APP_GEOSERVER_PASSWORD`；MinIO 凭证对应 `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`。

---

## 📖 使用指南

### 🎬 第一次使用（本地上传）

适合快速体验平台完整链路，无需配置 MinIO：

1. 🌐 在浏览器打开 http://localhost:18081/
2. 🔐 使用默认账号 **admin** / 密码 **admin** 登录（含验证码校验），进入空间数据治理工作台
3. 📤 在上传区域选择 DWG、DXF、SHP(zip) 或 KML 文件并提交
4. ⏳ 等待任务状态变为完成；可在「历史任务」下拉框中切换查看以往记录
5. 🗺️ 转换成功后，地图区域自动加载 MVT 矢量图层或栅格底图；支持缩放、平移与图层切换

若 GeoServer 暂未返回 MVT 地址，页面会提示下载 GPKG，可在 QGIS 等工具中本地查看。对于较大的 DWG 文件，转换可能需要数十秒至数分钟，请耐心等待进度完成。

### ☁️ MinIO 导入

适合已与对象存储打通的生产或批处理场景。请先将源文件上传至 MinIO 的 `atlas-data` Bucket（或其他已配置 Bucket），再触发转换：

```bash
# 示例：转换 MinIO 中 atlas-data/samples/demo.dwg
curl -X POST "http://localhost:18081/api/convert/minio" \
  -H "Content-Type: application/json" \
  -d '{"bucket_name":"atlas-data","object_name":"samples/demo.dwg"}'
```

也可在前端「MinIO 导入」面板中填写 Bucket 名称与 Object Key，无需手写 API 请求。转换进度与结果查询方式与本地上传一致。返回的 JSON 中包含 `job_id`，可用于轮询 `GET /api/convert/{job_id}` 获取最终 MVT / WMTS 地址。

### 🔌 常用 API

平台对外提供 RESTful 接口，便于与外部系统集成。所有 API 经 web 网关暴露，路径前缀为 `/api`；上传接口采用异步模式，立即返回 `job_id`，客户端需轮询或使用前端界面等待完成。

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| `POST` | `/api/convert` | multipart 本地上传文件并异步转换，返回 `job_id` |
| `POST` | `/api/convert/minio` | 指定 Bucket 与 Object Key，从 MinIO 拉取后转换 |
| `GET` | `/api/jobs` | 获取历史任务列表（文件名、状态、创建时间等） |
| `GET` | `/api/convert/{job_id}` | 查询指定任务的进度、错误信息及 MVT / WMTS 访问地址 |
| `GET` | `/api/convert/{job_id}/gpkg` | 下载该任务生成的 GeoPackage 文件 |

---

## 🏭 生产部署建议

将 ATLAS 用于生产或长期运行环境时，建议关注以下配置与安全事项：

**安全配置**

- 务必修改 `.env` 中 `MINIO_ROOT_PASSWORD` 与 `APP_GEOSERVER_PASSWORD`，避免使用默认弱口令。
- 平台默认仅暴露 `18081` 端口；若无 MinIO 管理需求，无需将 MinIO 9000/9001 映射到公网。
- 若部署在公网或 DMZ 区域，建议在 web 服务前增加 HTTPS 反向代理（如 Nginx / Traefik），并同步更新 `APP_GEOSERVER_PUBLIC_URL` 为 HTTPS 地址。

**性能与容量**

- GeoServer 与 api 均为 CPU / 内存敏感服务；大文件转换或高并发上传时，建议分配 ≥ 8 GB 内存。
- 定期关注 `atlas_jobs`、`geoserver_data`、`minio_data` 三个 Volume 的磁盘占用，必要时归档历史任务或清理无用图层。

**URL 配置**

- `APP_GEOSERVER_PUBLIC_URL` 必须设置为**浏览器实际访问 GeoServer 的地址**（含协议、主机、端口与 `/geoserver` 路径），否则地图切片链接可能指向错误地址导致空白地图。
- 若经外层网关转发（如 `https://gis.example.com/public/atlas/geoserver`），请将此外部地址写入该变量。

---

## ✅ 验证

部署完成后，建议执行以下检查确认服务正常：

```bash
docker compose ps
curl http://localhost:18081/api/healthz
```

| 检查项 | 预期结果 |
|:---|:---|
| 健康检查响应 | HTTP 200，Body 为 `{"status":"ok"}` |
| 容器状态 | `api`、`geoserver`、`minio` 均显示 **healthy** 🟢；`web` 处于 running |
| 前端页面 | 浏览器打开首页无报错，上传区与地图容器正常渲染 |
| 试上传 | 上传一个小型 DXF 或 KML 文件，确认任务能完成且地图有响应 |

---

## 🛠️ 常用运维命令

日常运维中，以下命令最为常用。修改 `.env` 后需执行 `docker compose up -d` 或 `restart` 使配置生效；仅重建某个服务可使用 `docker compose up -d --build api`。

```bash
# 📋 实时查看服务日志（排障首选）
docker compose logs -f api
docker compose logs -f geoserver

# 🔄 修改 .env 或配置后重启（数据卷保留）
docker compose restart

# 🛑 停止全部容器（数据卷保留，下次 up 可恢复）
docker compose down

# ⚠️ 停止并删除所有数据卷（将清空已发布图层与 MinIO 对象，慎用）
docker compose down -v

# 🔍 列出本项目相关的持久化卷
docker volume ls | findstr atlas    # Windows
docker volume ls | grep atlas       # Linux / macOS
```

---

## ❓ 常见问题

以下为部署与使用过程中最常遇到的问题及处理思路。更详尽的排查步骤请参阅 [assets/README.md](./assets/README.md)。

| 现象 | 可能原因 | 处理建议 |
|:---|:---|:---|
| 🔐 **无法登录 / 忘记密码** | 演示环境使用固定门户账号 | 默认账号 **admin**、密码 **admin**；生产环境需自行对接企业认证或 SSO |
| 🗺️ **地图空白** | GeoServer 切片 URL 生成错误或网络不可达 | 打开浏览器开发者工具，检查 `/geoserver/...` 请求是否 200；确认 `.env` 中 `APP_GEOSERVER_PUBLIC_URL` 与用户实际访问地址一致 |
| ☁️ **MinIO 导入失败** | Bucket 不存在、Object Key 错误或凭证不匹配 | 确认 `minio-init` 已成功执行、`atlas-data` Bucket 存在；核对 `.env` 中 MinIO 账号与 api 环境变量一致 |
| ⏳ **GeoServer 启动慢** | 首次启动需解压插件并初始化 data_dir | 正常现象，等待 1–2 分钟直至 healthcheck 通过；持续失败请查看 `docker compose logs geoserver` |
| 📐 **坐标偏移** | 源数据为无带号高斯-克吕格，带号配置不符 | 在 `.env` 中调整 `APP_GAUSS_KRUGER_ZONE`（默认 39），详见 [投影配置说明](./services/api/docs/gauss-kruger.md) |
| 🔴 **api 未 healthy** | geoserver 或 minio-init 尚未就绪 | 执行 `docker compose ps` 确认依赖服务状态；查看 `docker compose logs api` 中的 LibreDWG/GDAL 路径与报错信息 |
| 📄 **DWG 转换失败** | 文件版本过新或 LibreDWG 不支持 | 尝试在 CAD 中另存为较低版本 DWG 或导出 DXF 后重新上传 |
| 🔁 **历史任务地图加载失败** | GeoServer 图层已被清理或 Volume 丢失 | 确认 `geoserver_data` 卷仍存在；必要时重新上传并转换源文件 |

---

## 👤 作者与联系

| 项目 | 信息 |
|:---|:---|
| 🐙 **GitHub 仓库** | [https://github.com/Xu1Aan/ATLAS](https://github.com/Xu1Aan/ATLAS) |
| 👨‍💻 **维护者** | 徐岸 |
| 📧 **邮箱** | [toxuan1998@qq.com](mailto:toxuan1998@qq.com) |

完整维护者说明见 **[AUTHORS.md](./AUTHORS.md)**。API 服务根路径与 Swagger 文档中亦包含上述联系信息。

---

## 📚 更多文档

<img src="./assets/logo.png" alt="ATLAS" width="28" align="top" />

| 文档 | 内容 |
|:---|:---|
| 🐙 **[GitHub 仓库](https://github.com/Xu1Aan/ATLAS)** | 源码、Issue 与贡献入口 |
| 🌐 **[README.en.md](./README.en.md)** | 英文版项目说明（与本文档内容对应，可切换阅读） |
| 📘 **[assets/README.md](./assets/README.md)** | 完整架构说明、Mermaid 架构图、环境变量表、典型流程、持久化备份与详细故障排查 |
| 👤 **[AUTHORS.md](./AUTHORS.md)** | 维护者与联系方式 |
| 📐 **[services/api/docs/gauss-kruger.md](./services/api/docs/gauss-kruger.md)** | 高斯-克吕格投影带号、`APP_GAUSS_KRUGER_ZONE` 等配置说明 |
| ⚙️ **[.env.example](./.env.example)** | 全部运行时环境变量模板及默认值 |

---

## 📄 开源许可

本项目应用代码以开源形式提供。平台依赖以下上游组件，各自遵循相应开源协议，部署与分发时请注意合规要求：

| 组件 | 许可 |
|:---|:---|
| LibreDWG | GPLv3 |
| GDAL | MIT |
| GeoServer | GPLv2 |
| MinIO | AGPLv3 |

---

<p align="center">
  <img src="./assets/logo.png" alt="ATLAS" width="40" />
  <br />
  <sub><strong>ATLAS</strong> · 让 CAD / GIS 数据触手可及 🌍</sub>
  <br />
  <sub>徐岸 · <a href="mailto:toxuan1998@qq.com">toxuan1998@qq.com</a></sub>
</p>
