# 颐和园

游客端 2D 已上线：`https://954545647.github.io/#map?s=summer-palace`。
包含 14 个景点、14 张有作者与许可证记录的照片、按官方资料核对的讲解及 OSM 几何绘制的园林游览图。
照片公开署名见 `assets/scenics/summer-palace/credits.html`。

## 三维生成与同步

生成端景区 ID：`scenic-amap-b000a7o1cu`。
v1 已于 2026-10-23 07:23:11 UTC 发布。使用默认 4×4 公里选区，建模要求限定颐和园园区。
最终地图包含 14 个景点模型、入口导览牌、7 个地形/植被/装饰模型和一张贴图；已修正误生成的跨湖岸线以及部分屋面方向。
模型为 AI 园林示意，非测绘成果，不能作为实地导航依据。

`studio-published.pending.json` 是通过生成端分享功能导出的 v1 快照，仅包含颐和园并去除了制作人字段。
它保留 14 段核对后的讲解和全部最终模型引用。**尚未合并进游客端 `api/scenics`：23 个生成资源需要先下载。**
生成任务已暂停，避免继续改动模型和消耗额度。
之后重新采用的讲解质检记录已通过，但服务器同步超时，v2 尚未确认发布。

下载所需资源后，按照 `tools/README.md` 的 `sync_studio_scene.py` 流程同步。
可从本地交接目录 `/Users/rex/work/summer-palace-handoff` 恢复：包含下载清单、按 SHA-256 识别资源的脚本和继续同步命令。
下载目录中的文件名可能重复；必须按资源内容哈希匹配，避免混入其他景区的模型。
所有 GLB/PNG 通过校验、网页实测后，再运行 `add_scenic.py` 和提交部署。
此前必须获取最新 `origin/main`，保留其他景区并行新增的内容。

## 二维绘图

`render_scenic_map.py` 使用三维坐标框架，但岸线、岛屿孔洞和堤路取自原始 `geography.json`，避免继承 AI 地图图结构中的假跨湖边。
当前公开图片为 `map-illustrated-20261023b.png`。
数值和来源维护在 `editorial.json`；照片来源维护在 `sources.json`。
