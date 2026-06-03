# 作者与联系

| 项目 | 信息 |
|------|------|
| 维护者 | **徐岸** |
| 邮箱 | [toxuan1998@qq.com](mailto:toxuan1998@qq.com) |
| 产品 | ATLAS 空间数据治理与服务发布平台 |
| GitHub | [https://github.com/Xu1Aan/ATLAS](https://github.com/Xu1Aan/ATLAS) |

## 代码中的元数据

- API：[services/api/app/meta.py](services/api/app/meta.py)
- Web：[services/web/src/meta.ts](services/web/src/meta.ts)

## 运行时查询

部署后可访问以下接口获取维护者 JSON：

- `GET /api/about`（经网关：`http://<host>:18081/api/about`）
- `GET /`（api 根路径，经网关需直连容器或自行反代）
