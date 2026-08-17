---
name: mri-brain-to-3d-print
description: 从脑部 MRI（DICOM/NIfTI）数据生成可用于 3D 打印的大脑皮层 STL 模型。涵盖 dcm2niix 转换、FreeSurfer recon-all 皮层重建、pial 表面提取、左右半球合并与水密化、Taubin 平滑全流程。触发词：MRI、DICOM、NIfTI、FreeSurfer、recon-all、皮层表面、pial surface、STL、3D打印大脑、brain stl、脑模型。
---

# 从脑 MRI 到 3D 打印大脑模型

把一份脑部 T1 结构像 MRI，做成一个可直接切片 3D 打印的大脑皮层模型（含脑沟脑回纹理）。

**完整链路**：

```
DICOM ──dcm2niix──▶ NIfTI ──recon-all──▶ 皮层表面(pial) ──mris_convert──▶ STL ──trimesh──▶ 合并+水密+平滑
```

---

## 0. 前置条件

| 依赖 | 用途 | 说明 |
|---|---|---|
| Docker Desktop | 跑 FreeSurfer | Windows/macOS 用 Docker Desktop，Linux 直接 docker |
| 含 FreeSurfer 的镜像 | recon-all | 例如 `freesurfer/freesurfer:7.4.1` 官方镜像，或自建/私有神经影像镜像 |
| FreeSurfer **License** | recon-all 必需 | 免费，需本人到官网注册获取 `license.txt` |
| Python 环境 | mesh 处理 | 需装 `pydicom`、`dcm2niix`、`trimesh` |

> ⚠️ **FreeSurfer License**：没有 license，`recon-all` 直接拒绝运行。去 https://surfer.nmr.mgh.harvard.edu/registration.html 免费注册，拿到 `license.txt`（含你的邮箱和一段注册码）。**这个文件属于个人隐私，不要上传到任何公开仓库。**

```bash
pip install pydicom dcm2niix trimesh
```

---

## 1. DICOM → NIfTI

先把原始 DICOM 序列转成标准 NIfTI（这里以 3D T1 结构像为例，如 `t1_mprage_sag_1mm`）。

```bash
dcm2niix -z y -b y -f "%p" -o <output_dir> <dicom_series_dir>
```

- `-z y`：压缩为 `.nii.gz`
- `-b y`：同时生成 BIDS 格式的 JSON sidecar（含序列参数）
- `-f "%p"`：文件名用协议名

验证结果（体素应接近各向同性 1mm 最佳）：

```bash
python -c "import nibabel as n; img=n.load('<t1>.nii.gz'); print(img.shape, img.header.get_zooms(), n.aff2axcodes(img.affine))"
```

期望输出类似 `(256, 256, 208) (0.9, 0.9, 0.9) ('R','A','S')` —— 方向已被 dcm2niix 校正为 RAS。

---

## 2. FreeSurfer recon-all 皮层重建

这一步最耗时（CPU 上 **4~8 小时**），建议后台跑。

### 2.1 准备运行脚本

把 license 和数据放在同一个目录（下文挂载为容器内 `/data`），写 `run_recon.sh`：

```bash
#!/bin/bash
export FREESURFER_HOME=/usr/local/freesurfer/7.4.1   # 视镜像实际路径而定
export FS_LICENSE=/data/license.txt
source $FREESURFER_HOME/SetUpFreeSurfer.sh
export SUBJECTS_DIR=/data/freesurfer
mkdir -p $SUBJECTS_DIR
recon-all -all -s subj01 -i /data/<t1>.nii.gz -openmp 16 \
    > /data/recon_all.log 2>&1
```

### 2.2 后台启动

```bash
docker run -d --name recon \
  -v "<data_dir>:/data" \
  <neuroimage-image> bash /data/run_recon.sh
```

### 2.3 跟踪进度

recon-all 会写两个日志，随时可查：

```bash
# 总体日志（stdout）
tail -f <data_dir>/recon_all.log

# 已完成的步骤列表
grep '^#@#' <data_dir>/freesurfer/subj01/scripts/recon-all-status.log
```

完成的标志是日志末尾出现：

```
recon-all -s subj01 finished without error at ...
```

> 💡 **耗时分布**：`autorecon1`（预处理，~15min）→ `autorecon2`（分割+表面重建，1~2h）→ `autorecon3`（球面配准+皮层，2~3h）。最慢的三个环节是「自动拓扑修复」「左右半球球面配准」「皮层分块标注」，进度卡住属正常。
>
> 💡 **Docker Desktop 资源**：Windows/macOS 上 `docker info` 里的 `CPUs`/`Total Memory` 才是容器实际可用的（通常被限制为宿主机的 75%），`-openmp` 别设得比这个还大。

---

## 3. pial 表面 → STL

recon-all 完成后，`surf/` 目录下会有皮层表面文件。用 FreeSurfer 自带的 `mris_convert` 转成 STL：

```bash
docker run --rm -v "<data_dir>:/data" <neuroimage-image> bash -c '
  export FREESURFER_HOME=/usr/local/freesurfer/7.4.1
  export FS_LICENSE=/data/license.txt
  source $FREESURFER_HOME/SetUpFreeSurfer.sh
  mkdir -p /data/output
  mris_convert /data/freesurfer/subj01/surf/lh.pial /data/output/lh.pial.stl
  mris_convert /data/freesurfer/subj01/surf/rh.pial /data/output/rh.pial.stl
'
```

> ⚠️ **常见坑**：在 Windows 挂载目录下，`lh.pial` / `rh.pial` 显示为 **0 字节**——它们其实是**符号链接**（`lh.pial -> lh.pial.T1`），真实文件是 `lh.pial.T1`（几 MB）。Windows 文件管理器不识别 Linux 符号链接会显示 0 字节，但在容器内用 `mris_convert` 读 `lh.pial` 会自动跟随链接，数据是完整的，无需处理。

FreeSurfer 的 pial 表面**本身就是水密闭合网格**（覆盖整个皮层，含中线内侧和底面封口），左右半球各自独立闭合，非常适合直接 3D 打印。

---

## 4. 合并左右半球 + 水密化（trimesh）

```python
# merge_stl.py
import trimesh, os

OUT = "./output"
lh = trimesh.load(os.path.join(OUT, "lh.pial.stl"))
rh = trimesh.load(os.path.join(OUT, "rh.pial.stl"))

# 合并两个水密壳（各自已 watertight=True）
combined = trimesh.util.concatenate([lh, rh])
combined = combined.process(validate=True)   # 合并重复顶点、去退化面
combined.fix_normals()                        # 法线统一朝外

combined.export(os.path.join(OUT, "brain_full.stl"))
print(f"watertight={combined.is_watertight}, "
      f"vol={combined.volume/1000:.1f} cm3, "
      f"extents={combined.extents}")
```

输出 `brain_full.stl`：含左右两个半球壳（大脑纵裂处自然分开，符合真实解剖），每个壳都水密，可直接切片。

---

## 5. Taubin 平滑（可选，推荐）

pial 表面是逐顶点优化出来的，带有细小的表面噪声。3D 打印前做一次 **Taubin 平滑**（收缩+膨胀交替，保体积、保沟回），打印出来更顺滑：

```python
# smooth_stl.py
import trimesh

mesh = trimesh.load("./output/brain_full.stl")
# lamb 收缩 + nu 膨胀交替，净效果平滑且不塌陷沟回
smooth = trimesh.smoothing.filter_taubin(mesh, lamb=0.5, nu=-0.53, iterations=10)
smooth.fix_normals()
smooth.export("./output/brain_full_smooth.stl")
```

- `iterations=10`：轻-中度平滑，抹平噪声、保留脑沟脑回
- 想更光滑 → 加到 20；想保留更多细节 → 减到 5
- 平滑后体积约 −5~7%（抹平表面凹凸的正常现象），水密性保持

---

## 6. 常见问题速查

| 现象 | 原因 / 解决 |
|---|---|
| `recon-all` 报 license 错误 | `$FREESURFER_HOME/license.txt` 不存在或 `FS_LICENSE` 未设置 |
| `lh.pial` 0 字节 | 是符号链接，指向 `lh.pial.T1`，容器内正常 |
| 卡在某步很久 | 拓扑修复/球面配准本来就慢，查 `recon-all-status.log` 确认还在推进 |
| 容器内找不到 `mris_convert` | 未 `source SetUpFreeSurfer.sh`，用完整路径 `/usr/local/freesurfer/7.4.1/bin/mris_convert` |
| Docker 比预期慢 | 看 `docker info` 的实际 `CPUs`，Docker Desktop 默认只分到宿主机的一部分 |

---

## 附：本流程用到的完整脚本

`run_recon.sh`（见 §2.1）、`merge_stl.py`（见 §4）、`smooth_stl.py`（见 §5）可原样复用。

**隐私提醒**：MRI 数据、患者信息、FreeSurfer license 均属敏感内容，切勿提交到公开仓库。
