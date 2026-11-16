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


## 岐江公园 · 船厂记忆

`scenes/qijiang-park/README.md` 记录七处导览的实拍、许可、资料来源和坐标边界。

新场景可复用独立的三维资源压缩与恢复下载流程：

```sh
node tools/asset-pipeline/optimize-scene.mjs qijiang-park
python3 tools/asset-pipeline/build-scene-runtime.py qijiang-park v5 f03c0bbb4ebf1232f7e0796f6f85971187957172
```

优化只做网格编码压缩与纹理无损转换，并检查三角形数量、边界和像素一致性。每个场景独立生成清单与入口，复用已验证的下载队列。

当前游客入口使用 `boot-ayou-avatar-v1.js` → `app-ayou-avatar-v1.js`。后者是 `app.js` 的发布快照；后续修改入口时，应生成新的版本文件并同步更新 boot 与 index，避免 CDN 缓存旧脚本。

## 阿游文化导览

`ayou-guide-v1.js` 与 `ayou-guide-v2.css` 为独立组件，由 `index.html` 加载。首页和场景列表提供中山选景入口；孙中山故居、岐江公园的地图与点位页提供文化讲解、照片署名和地图定位。阿游读取已发布内容，不调用 AI 服务，也不使用生成端额度。v2 样式在原生旅伴面板打开时隐藏浮动导览，避免遮挡。

讲解更新后运行 `python3 tools/build_ayou_content.py`，从 `api/scenics` 重新生成小型公开数据文件 `assets/ayou/content-v1.json`。数据含现有 16 处点位的讲解、照片与来源；不复制工作区其他数据。后续发布调整资源版本以避免旧缓存。

地图定位复用原生 `.m3-tag[data-spot]` 或二维 `[data-marker]` 控件；原生三维景点详情打开时，阿游隐藏让位。没有就绪的原生控件时，进入该点位的二维地图。关闭详情后阿游恢复；支持 Escape 收起、焦点回到入口、手机滚动与减少动效偏好。

形象来自香山漫游设计稿，使用内置 image_gen 提取透明底单角色，再编码为约 140 KB WebP，保留透明度。提示词见 `tools/ayou-image-prompt.json`。

## 阿游三维旅伴

`vendor/studio-20261023/ayou-avatar-v1.js` 用本地几何体实现纸船帽、砖红围巾、挎包和折叠地图。保留原生移动、转身、挥手、乘筏与角色切换接口，不新增模型下载请求，也不使用生成端额度。主体约 1.6 万个三角形、21 次绘制；静态部件按材质合并，四肢保留独立动作轴。

孙中山故居与岐江公园分别使用 `map3d-sun-ayou-v1.js`、`map3d-qijiang-ayou-v1.js`。首次升级时，每个中山场景将默认旅伴设为阿游；此后的手动角色选择保留。自定义昵称和其他景区选择不会覆盖。纯静态部署关闭这两个场景的同游连接，保留本地旅伴与动作操作；`api/companions/status` 也声明服务未启用。

```sh
python3 tools/build_ayou_avatar.py
node --test tools/ayou-avatar.test.mjs
```

构建脚本只在冻结版本上应用经过计数校验的挂钩，并重建版本化入口。测试验证模型范围、克隆所需的动作节点、默认角色迁移，以及除上述挂钩外的下载和移动代码不变。`tools/ayou-preview.html` 可在本地预览模型与动作，不随 Pages 发布。
