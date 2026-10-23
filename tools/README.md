# 景区数据维护

游客站从 `api/scenics` 读取景区资料。`scenes/` 保存源数据、来源与可再生成的文件；GitHub Pages 工作流不发布 `scenes/` 和 `tools/`。

## 合并源数据

```sh
python3 tools/add_scenic.py scenes/summer-palace
```

合并时保留其他景区，复制照片、绘卷和结构化署名，并保留可选的三维 `mapPackage`。

## 同步生成端

在生成端完成质检、发布并导出备份。备份包含共享工作区的其他景区，原始备份仅保存在本机，不加入这个仓库。

```sh
python3 tools/sync_studio_scene.py /path/to/backup.json scenes/summer-palace \
  --studio-id scenic-amap-b000a7o1cu --base-url https://studio-host
python3 tools/add_scenic.py scenes/summer-palace
```

同步脚本只提取指定的已发布景区，检查 14 个景点 ID、讲解及来源，保留 Commons 原图署名，将三维模型与纹理下载到该景区的资产目录，并更新点位。需要登录才能下载的资源可先导出到本机，再通过 `--asset-cache /path/to/cache` 读取；缓存保留 `/generated/` 后的目录结构。脚本不复制账号、其他景区或 AI 对话记录。

## 二维绘卷

```sh
python3 tools/render_scenic_map.py scenes/summer-palace/studio-map-package.json \
  scenes/summer-palace/map-illustrated.svg scenes/summer-palace/geography.json
```

SVG 使用地图包的完整坐标范围，北向上；转换成同宽高比例的 PNG 后上传生成端。不要添加外边距，否则点位会偏移。建筑符号是插画示意，水岸、园界和步道来自 OSM。PNG 命名为 `map-illustrated.png`，同步脚本会用它更新 `map.png`。

`editorial.json` 记录逐点讲解及官方事实来源；`credits.html` 和每张照片的 `credit` 记录作者、原图、许可证与缩放说明。修改讲解后，在生成端重新运行讲解稿并审核采用。

## 三维渲染兼容

颐和园和孙中山故里使用 `vendor/studio-20261023/` 的生成端三维渲染模块，以支持新版地形与纹理字段。启动时 `studio-map-bridge-20261023.js` 通过新版校验器注册这两个地图包，并将同一个运行时对象提供给游客端路由；不能只注册到旧包集合，否则路由会退回 2D，或新渲染器无法找到地图。原有五个景区继续使用旧模块。修改打包 JS 后更新资源文件名或入口版本参数，避免浏览器使用缓存。

颐和园单独使用 `map3d-summer-palace-packed.js`：同步脚本为每个 GLB 额外生成 `.glb.gz`，浏览器原生解压后交给同一个 GLTF 解析器。原始 GLB 保留作为兼容回退。下载器限制并发数，并对超时和临时网络错误重试；复用同一张地表贴图的下载。
